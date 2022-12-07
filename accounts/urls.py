from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path,re_path,include
from .views import  SignUpView, deleteMember, logOff, logIn, memberView, projectAddView,projectListView,projectDelView,ProjectUpd, change_password
from .views import committeeAddView, CommitteeUpd, committeeDelView,committeeListView, minuteAddView, minuteDelView, minuteListView, minuteUpdView
from .views import transactionAddView, transactionDelView, transactionListView,transactionUpdView, memberUpdView
from .views import bankAccountListView, bankAccountAddView, bankAccountDelView, bankAccountUpdView
from .views import bankAccountSummary, deleteMember, pwdResetInstruction, beneficiaryListView
from .views import getTransactions, transactionAllView, beneficiaryAddView, beneficiaryDelView,beneficiaryUpdView
from .views import beneficiaryDetailView, projectClosedListView

urlpatterns = [
    re_path(r'signup', SignUpView.as_view(), name='signup'),
    re_path(r'logoff', logOff, name='logoff'),
    re_path(r'login', logIn, name='login'),
    re_path(r'^member$', memberView, name='member'),
    re_path(r'^updateMember', memberUpdView, name='updateMember'),
    re_path(r'^deleteMember', deleteMember, name='deleteMember'),
    
    re_path(r'beneficiaryDetail/(?P<pk>\d+)', beneficiaryDetailView, name='beneficiaryDetail'),
    re_path(r'beneficiaryList', beneficiaryListView, name='beneficiaryList'),
    re_path(r'beneficiaryAdd', beneficiaryAddView, name='beneficiaryAdd'),
    re_path(r'beneficiaryDel/(?P<pk>\d+)', beneficiaryDelView, name='beneficiaryDel'),
    re_path(r'beneficiaryUpd/(?P<pk>\d+)', beneficiaryUpdView, name='beneficiaryUpd'),

    re_path(r'projectClosedList', projectClosedListView, name='projectClosedList'),
    re_path(r'projectList', projectListView, name='projectList'),
    re_path(r'projectAdd', projectAddView, name='projectAdd'),
    re_path(r'projectDel/(?P<pk>\d+)', projectDelView, name='projectDel'),
    re_path(r'projectUpd/(?P<pk>\d+)', ProjectUpd.as_view(), name='projectUpd'),

    
    re_path(r'bankAccountList', bankAccountListView, name='bankAccountList'),
    re_path(r'bankAccountAdd', bankAccountAddView, name='bankAccountAdd'),
    re_path(r'bankAccountDel(?P<bk>\d+)', bankAccountDelView, name='bankAccountDel'),
    re_path(r'bankAccountUpd(?P<bk>\d+)', bankAccountUpdView, name='bankAccountUpd'),

    re_path(r'transactionAll', transactionAllView, name='transactionAll'),
    re_path(r'transactionList(?P<pk>\d+)', transactionListView, name='transactionList'),
    re_path(r'transactionAdd', transactionAddView, name='transactionAdd'),
    re_path(r'transactionUpd(?P<pk>\d+)', transactionUpdView, name='transactionUpd'),
    re_path(r'transactionDel(?P<pk>\d+)', transactionDelView, name='transactionDel'),

    re_path(r'getTransactions', getTransactions, name='getTransactions'),

    re_path(r'bankAccountSummary(?P<pk>\d+)',bankAccountSummary, name='bankAccountSummary'),

    re_path(r'committeeList(?P<pk>\d+)', committeeListView, name='committeeList'),
    re_path(r'committeeAdd(?P<pk>\d+)', committeeAddView, name='committeeAdd'),
    re_path(r'committeeDel(?P<pk>\d+)', committeeDelView, name='committeeDel'),
    re_path(r'committeeUpd(?P<pk>\d+)', CommitteeUpd.as_view(), name='committeeUpd'),
    
    re_path(r'minuteList(?P<pk>\d+)', minuteListView, name='minuteList'),
    re_path(r'minuteAdd(?P<pk>\d+)', minuteAddView, name='minuteAdd'),
    re_path(r'minuteDel(?P<pk>\d+)', minuteDelView, name='minuteDel'),
    re_path(r'minuteUpd(?P<pk>\d+)', minuteUpdView, name='minuteUpd'),
    
    re_path(r'^change_password/$', change_password, name='change_password'),
    re_path(r'pwdResetInstruction$', pwdResetInstruction, name='pwdResetInstruction'),

    re_path(r'password_reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset/pwdreset_form.html',
             subject_template_name='accounts/password_reset/pwdreset_subject.txt',
             email_template_name='accounts/password_reset/pwdreset_email.html',
             success_url='login'
         ),
         name='password_reset'),
    
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('password_reset_confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset/pwdreset_confirm.html',
             success_url='login'),
         name='password_reset_confirm'),

    re_path(r'password_reset_complete',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset/pwdreset_complete.html'),
         name='password_reset_complete'),
]