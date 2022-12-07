from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.template  import loader
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import UpdateView
from django.contrib  import messages
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from   django_pandas.io import read_frame

from django.db.models import Sum, Count
from django.conf import settings
from django.http import JsonResponse
from os import path, rename
from util import img
from PIL import Image
from datetime import datetime
from django.utils  import timezone
from accounts.forms import RegisterForm, UserForm, MemberForm, ProjectForm, CommiteeForm, MinuteForm, TransactionForm, TransactionUserForm, BankAccountForm
from accounts.models import BankAccount, Commitee, Member, Project, Minute, UserRole, Transaction, ExpenseType, BankAccount
from accounts.serializers import MemberSerializer, TransactionSerializer
from accounts.models import Beneficiary
from accounts.forms import BeneficiaryForm

class SignUpView(generic.CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'signup.html'

def logIn(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}")
                c =  {'user_id':user.id,
                     'name':user.first_name
                     }
                t = loader.get_template('home/base.html')
                #request.user = user
                return  render(request = request,template_name = "home/index.html",context=c)
            else:
                return render(request=request,template_name="error.html", context={'title':"Login ERROR", 'message':"User name <strong>"+username+"</strong> or Password is wrong"})
        else:
            return render(request=request,template_name="error.html", context={'title':"Login ERROR", 'message':"User name or Password is wrong"})

    form = AuthenticationForm()
    return render(request = request,
                    template_name = "login.html",
                    context={"form":form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })

def pwdResetInstruction(request):
    return render(request, 'password_reset/pwdreset_instruction.html')

@login_required
def deleteMember(request):
    member = Member.objects.get(user_id=request.user.id)
    user = User.objects.get(id=request.user.id)
    logout(request)
    try:
        user.delete()
    except IntegrityError as e:
        user.is_active=0
        user.username=user.username+"DELETED"
        user.save(update_fields=['is_active'])

    return redirect('/')

@login_required
def memberView(request):
    member = Member.objects.get(user_id=request.user.id)
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        transaction = Transaction.objects.all().filter(owner_id=user.id).order_by('-date')

    return render(request = request,template_name = "member.html",context={'member':member, 'transaction_list':transaction})

@login_required
def memberUpdView(request):
    member = Member.objects.get(user_id=request.user.id)
    user = User.objects.get(id=request.user.id)
    
    if request.method == 'GET':
        profile_form = MemberForm(instance=member)

        user_form = UserForm(instance=user)
        return render(request = request,template_name = "member_upd.html",context={"profile_form":profile_form, 'user_form':user_form, 'member':member})

    if request.method == 'POST':
        member_form = MemberForm(request.POST,request.FILES, instance=request.user.member)
        user_form = UserForm(request.POST,instance=request.user)
        if user_form.is_valid():
            obj=user_form.save(commit=False)
            obj.save(update_fields=['first_name','last_name','email'])

        if member_form.is_valid():
            obj=member_form.save(commit=False)
            user = User.objects.get(id=request.user.id)
            obj.user = user
            obj.id=member.id
            obj.save()
            
            if obj.photo:
                today = datetime.now()
                twidth, theight = 150, 200
                fname, ext = path.splitext(obj.photo.name)
                albumPath = path.join(settings.MEDIA_ROOT, "profile/")
                opath = path.join(settings.MEDIA_ROOT,fname + ext)
                nfname = today.strftime("%m%dT%H%M%S") + ext
                npath = path.join(albumPath,nfname)
                photo = Image.open(opath)
                width, height = photo.size
                if (width > twidth):
                    photo = img.apply_orientation(photo)
                    photo.thumbnail((twidth, theight), Image.HAMMING)
                photo.save(opath)
                rename(opath,npath)
                obj.photo.name = "profile/"+nfname
                obj.save()
                messages.success(request, "Profile information was updated. Successfully")

        return redirect('accounts:member')

@login_required
def logOff(request):
    logout(request)
    user = User.objects.filter(username=request.user)
    return render(request, 'logoff.html',{'user':user})

def getUserRole(user,table):
    userRole='NONE'
    if user.has_perm('accounts.add_'+table):
        userRole='EDIT'
    elif user.has_perm('accounts.view_'+table):
        userRole='VIEW'
    print('table :'+table+' '+userRole)
   
    return userRole

@login_required
def projectAddView(request):
    if request.method == 'GET':
        form = ProjectForm()
        return render(request = request,template_name = "project.html",context={"form":form})

    if request.method == 'POST':
        user = User.objects.get(id=request.user.id)
        form = ProjectForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy = user
            obj.save()
            return redirect('accounts:projectList')
        else:
            error={'message':'Error'}
            return render(request,template_name='error.html',context=error)
def calculate():
    transaction = read_frame(Transaction.objects.all())
    txs = transaction.loc[:,['txType','amount','project']]
    txs['project'] = txs['project'].str.strip()

    px = txs.groupby(['project','txType']).sum().reset_index()
    px.fillna(0)
    project = Project.objects.all()
    for prj in project.iterator():
        tmp=px.loc[lambda df:(df["project"]==prj.name) & (px['txType']=='Deposit'),['amount']]
        prj.raisedFund=0 
        prj.spentFund=0
        if not tmp.empty:
            prj.raisedFund = tmp['amount'].values[0]

        tmp = px.loc[lambda df:(px['project'] == prj.name) & (px['txType']=='Withdraw'),['amount']]
        if not tmp.empty:
            prj.spentFund = tmp['amount'].values[0]

        prj.balance    = prj.raisedFund - prj.spentFund
        prj.save()

@login_required
def projectListView(request):
    if request.method == 'GET':
        calculate()
        projects = Project.objects.filter(status=Project.IN_PROGRESS)
        user = User.objects.get(id=request.user.id)
        userRole=getUserRole(user,'project')
        return render(request = request,template_name = "project_list.html",context={'project_list':projects, 'userRole':userRole})

@login_required
def projectClosedListView(request):
    if request.method == 'GET':
        projects = Project.objects.filter(status=Project.COMPLETED)
        user = User.objects.get(id=request.user.id)
        userRole=getUserRole(user,'project')
        return render(request = request,template_name = "project_list.html",context={'project_list':projects, 'userRole':userRole})

@login_required
def projectDelView(request,pk):
    project = Project.objects.get(id=pk)
    project.status = Project.COMPLETED
    project.endDate = timezone.now()
    project.save()
    return redirect('accounts:projectList')

class ProjectUpd(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'project.html'

    def get_success_url(self):
        return  reverse_lazy('accounts:projectList')

    def get_queryset(self):
        return Project.objects.filter(id=self.kwargs['pk'])


@login_required
def committeeAddView(request,pk):
    project = Project.objects.get(id=pk)
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        form = CommiteeForm()
        form.fields['member'].queryset = User.objects.order_by('first_name')

        if project.isCommiteeMember(user) or user.is_staff:
            return render(request = request,template_name = "committee.html",context={"form":form,'project':project})
        else:
            error={'title':'Access Control', 'message':user.first_name+" is not a committee member of "+project.name}
            return render(request,template_name='error.html',context=error)
 
    if request.method == 'POST':
        form = CommiteeForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy = user
            obj.project = project
            obj.save()
            return redirect('accounts:committeeList', pk=pk)
        else:
            error={'message':'Error'}
            return render(request,template_name='error.html',context=error)

@login_required
def committeeListView(request,pk):
    if request.method == 'GET':
        committees = Commitee.objects.all().filter(project_id=pk).order_by('role__priority')
        project = Project.objects.get(id=pk)
        user = User.objects.get(id=request.user.id)
        userRole=getUserRole(user,'committee')
        return render(request = request,template_name = "committee_list.html",context={'committee_list':committees, 'project':project, 'userRole':userRole})

class CommitteeUpd(UpdateView):
    model = Commitee
    form_class = CommiteeForm
    template_name = 'committee.html'

    def get_success_url(self):
        return  reverse_lazy('accounts:committeeList', kwargs={'pk':self.object.project_id})

    def get_queryset(self):
        return Commitee.objects.filter(id=self.kwargs['pk'])
 
@login_required
def committeeDelView(request,pk):
    committee = Commitee.objects.get(id=pk)
    project = Project.objects.get(id=committee.project_id)
    committee.delete()        
    committeeList = Commitee.objects.all().filter(project_id=project.id).order_by('role__priority')
    
    return render(request = request,template_name = "committee_list.html",context={'committee_list':committeeList,'project':project, 'userRole':'EDIT'})

#Minutes
@login_required
def minuteAddView(request,pk):
    project = Project.objects.get(id=pk)
    user = User.objects.get(id=request.user.id)  
    
    if request.method == 'GET':
        userRole=project.getUserRole(user,'Minute')
        form = MinuteForm()
        return render(request = request,template_name = "minute.html",context={"form":form,'project':project,'userRole':userRole})
        
    if request.method == 'POST':
        form = MinuteForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy = user
            obj.project = project
            obj.save()
           
            return redirect('accounts.minuteList')
        else:
            error={'message':'Error in Data input to Minutes'}
            return render(request,template_name='error.html',context=error)

@login_required
def minuteListView(request,pk):
    if request.method == 'GET':
        minutes = Minute.objects.all().filter(project_id=pk).order_by('-date')
        user = User.objects.get(id=request.user.id)
        prj=Project.objects.get(id=pk)
        userRole=getUserRole(user,'minute')
        userRole=prj.getUserRole(user,'Minute')
        return render(request = request,template_name = "minute_list.html",context={'minute_list':minutes, 'userRole':userRole, 'project':prj})

class MinuteUpd(UpdateView):
    model = Minute
    form_class = MinuteForm
    template_name = 'minute.html'

    def get_success_url(self):
        return  reverse_lazy('accounts:minuteList', kwargs=self.kwargs['pk'])

    def get_queryset(self):
        return Minute.objects.filter(id=self.kwargs['pk'])

def minuteUpdView(request,pk):
    user = User.objects.get(id=request.user.id)
    minute = Minute.objects.get(id=pk)  
    project = Project.objects.get(id=minute.project_id)
    
    if request.method == 'GET':
        form  = MinuteForm(instance = minute)
        return render(request,template_name='minute.html',context={'form':form})

    if request.method == 'POST':
        form = MinuteForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy = user
            obj.project = project
            obj.id = minute.id
            obj.save()

        else:
            error={'message':'Error in Data input to Minutes'}
            return render(request,template_name='error.html',context=error)

    return redirect('accounts:minuteList', pk=pk)

@login_required
def minuteDelView(request,pk):
    minute = Minute.objects.get(id=pk)
    user = User.objects.get(id=request.user.id)
    project=Project.objects.get(id=minute.project_id)
    userRole=UserRole.EDIT

    minute.delete()     
    minuteList = Minute.objects.all().filter(project_id=project.id)
    
    return render(request = request,template_name = "minute_list.html",context={'minute_list':minuteList,'project':project, 'userRole':userRole})

@login_required
def transactionAllView(request):
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        userRole = getUserRole(user,'transaction')
        return render(request = request,template_name = "transactionAll.html", context={"userRole":userRole})

@login_required
def transactionListView(request,pk):
    if request.method == 'GET':
        user = User.objects.get(id=request.user.id)
        userRole = getUserRole(user,'transaction')
        if pk == '0':
            tx = Transaction.objects.all()
            project_name="All projects"
        else:
            tx = Transaction.objects.filter(project_id=pk)
            project_name = Project.objects.get(id=pk).name

        return render(request = request,template_name = "transaction_list.html",context={"transaction_list":tx, "userRole":userRole,'project_name':project_name})

@login_required
def transactionAddView(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        form = TransactionForm()
        form.fields['exType'].queryset = ExpenseType.objects.all()
        form.fields['bank'].queryset = BankAccount.objects.all()
        form.fields['owner'].queryset = User.objects.order_by('first_name')

        return render(request = request,template_name = "transaction.html",context={"form":form})
        
    if request.method == 'POST':
        form = TransactionForm(request.POST,request.FILES)

        if form.is_valid():
            try:
                obj=form.save(commit=False)
                obj.updatedBy = user
                obj.save()

                if obj.receipt:
                    today = datetime.now()
                    fname, ext = path.splitext(obj.photo.name)
                    albumPath = path.join(settings.MEDIA_ROOT, "transaction/")
                    opath = path.join(settings.MEDIA_ROOT,fname + ext)
                    nfname = today.strftime("%m%dT%H%M%S") + ext
                    npath = path.join(albumPath,nfname)
                    rename(opath,npath)
                    obj.photo.name = "transaction/"+nfname
                    obj.save(update_fields=['receipt'])

                return render(request,template_name="transaction_success.html",context={'transaction':obj})
            except IntegrityError as e:
                error={'message':'Could not save to database'}
                return render(request,template_name='error.html',context=error)
        else:
            error={'message':'Error'}
            return render(request,template_name='error.html',context=error)

@login_required
def transactionUpdView(request,pk):
    user = User.objects.get(id=request.user.id)
    tx = Transaction.objects.get(id=pk)  
    bank = BankAccount.objects.get(id=tx.bank_id)
    project = Project.objects.get(id = tx.project_id)

    if request.method == 'GET':
        form  = TransactionForm(instance = tx)
        form.fields['exType'].queryset = ExpenseType.objects.filter(prjType_id = project.prjType.id)
        form.fields['bank'].queryset = BankAccount.objects.all()
        form.fields['owner'].queryset = User.objects.order_by('first_name')
        return render(request,template_name='common_form.html',context={'form':form, 'form_name':"Transaction "})

    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy = user
            obj.project = project
            obj.bank = bank
            obj.id = tx.id
            obj.save()

            if obj.receipt:
                    today = datetime.now()
                    fname, ext = path.splitext(obj.receipt.name)
                    albumPath = path.join(settings.MEDIA_ROOT, "transaction/"+today.strftime("%Y"))
                    opath = path.join(settings.MEDIA_ROOT,fname + ext)
                    nfname = today.strftime("%m%dT%H%M%S") + ext
                    npath = path.join(albumPath,nfname)
                    rename(opath,npath)
                    obj.receipt.name = "transaction/"+today.strftime("%Y")+"/"+nfname
                    obj.save(update_fields=['receipt'])
        else:
            error={'message':'Error in Data input to Minutes'}
            return render(request,template_name='error.html',context=error)

    return redirect('accounts:transactionList',pk=0)
 
@login_required
def transactionDelView(request,pk):
    tx = Transaction.objects.filter(id=pk).first()
    tx.delete()
    return redirect('accounts:transactionList',pk=0)

@api_view(['GET'])
def getTransactions(request):
    data=Transaction.objects.all()
    eqSerializer = TransactionSerializer(data,many=True)
    return Response(eqSerializer.data)

def bankAccountSummary(request,pk):
    labels = []
    data = []
    print("bak account summary")
    queryset = Transaction.objects.all().filter(bank__id = pk).filter(txType=Transaction.TxType_DEPOSIT).values('bank_id').annotate(total=Sum('amount'))

    for entry in queryset:
        withdraw = Transaction.objects.all().filter(bank_id =entry['bank_id']).filter(txType=Transaction.TxType_WITHDRWAL).values('bank_id').annotate(total=Sum('amount'))
        if withdraw.count()==0:
            w = 0
        else:
            w = withdraw.first()['total']

        bank = BankAccount.objects.get(id=entry['bank_id'])
        labels.append(bank.name)
        balance = entry['total'] - w
        data.append(balance)
    
    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })

@login_required
def bankAccountAddView(request):
    return bankAccountUpdView(request,'x')

@login_required
def bankAccountUpdView(request,bk):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        if bk=='x':
            form = BankAccountForm()
            bank = BankAccount()
        else:
            bank = BankAccount.objects.get(id=bk) 

        form  = BankAccountForm(instance = bank)
        form_name="Bank Account"
        return render(request,template_name='common_form.html',context={'form':form, 'form_name':form_name})

    if request.method == 'POST':
        form = BankAccountForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            obj.updatedBy_id = user.id
            obj.save()
        else:
            error={'message':'Error in Data input to Minutes'}
            return render(request,template_name='error.html',context=error)

        return redirect('accounts:bankAccountList')

@login_required
def bankAccountDelView(request,bk):
    tx = BankAccount.objects.filter(id=bk).first()
    tx.delete()
    return redirect('accounts:bankAccountList')
    
@login_required
def bankAccountListView(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        banks = BankAccount.objects.all()
        userRole = getUserRole(user,'bank')
        context={ 'bank_list':banks, 'userRole':userRole}
        return render(request = request,template_name = "bank_list.html",context=context)

@login_required
def memberList(request):
    return render(request,'member_list.html')

@api_view(['GET'])
def memberAll(request):
    data=User.objects.all()
    eqSerializer = MemberSerializer(data,many=True)
    return Response(eqSerializer.data)

@login_required
def beneficiaryAddView(request):
    return beneficiaryUpdView(request,'x')

@login_required
def beneficiaryUpdView(request,pk):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        if pk=='x':
            form = BeneficiaryForm()
            beneficiary = Beneficiary()
        else:
            beneficiary = Beneficiary.objects.get(id=pk) 
            form  = BeneficiaryForm(instance = beneficiary)
        
        form_name="Beneficiary"
        return render(request,template_name='common_form.html',context={'form':form, 'form_name':form_name})

    if request.method == 'POST':
        form = BeneficiaryForm(request.POST)
        if form.is_valid():
            obj=form.save(commit=False)
            if pk != 'x':
                obj.id = pk
            obj.save()
        else:
            error={'message':'Error in Data input to Minutes'}
            return render(request,template_name='error.html',context=error)

        return redirect('accounts:beneficiaryList')

@login_required
def beneficiaryDelView(request,pk):
    tx = Beneficiary.objects.get(id=pk)
    tx.delete()
    return redirect('accounts:beneficiaryList')

@login_required
def beneficiaryListView(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'GET':
        data_list = Beneficiary.objects.all().exclude(id=14)
        userRole=getUserRole(user,'beneficiary')
        print('userRole :'+userRole)
        context={ 'data_list':data_list, 'userRole':userRole}
        return render(request = request,template_name = "beneficiary_list.html",context=context)

def beneficiaryDetailView(request,pk):
    if request.method == 'GET':
        beneficiary = Beneficiary.objects.filter(id=pk).first()
        data_list = Transaction.objects.filter(beneficiary_id=pk)
        context={ 'data_list':data_list, 'beneficiary':beneficiary}
        return render(request = request,template_name = "beneficiary.html",context=context)