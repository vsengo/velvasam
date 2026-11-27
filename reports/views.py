from django.shortcuts import render
from  django_pandas.io import read_frame
from django.http import Http404, JsonResponse
from django.db.models import Case, Count, F, IntegerField, Q, Sum, When
from django.db.models.functions import TruncYear, Trim
import pandas as pd
from accounts.models import Beneficiary, Project, Transaction
from .models import ReportByMonth
import datetime as dt
import util.date as du


def _yearly_contribution_distribution(transactions):
    contribution_type = Q(
        txType=Transaction.TxType_DEPOSIT,
        exType__expense__in=('Contribution', 'Monthly Contribution'),
    )
    yearly_totals = (
        transactions.annotate(
            year=TruncYear('date'),
            amount_lkr=Case(
                When(amountLocal=0, then=F('amount')),
                default=F('amountLocal'),
                output_field=IntegerField(),
            ),
        )
        .values('year')
        .annotate(
            contribution=Sum('amount_lkr', filter=contribution_type),
            distribution=Sum('amount_lkr', filter=~contribution_type),
        )
        .order_by('year')
    )
    return {
        'labels': [row['year'].year for row in yearly_totals],
        'contributions': [float(row['contribution'] or 0) for row in yearly_totals],
        'distributions': [float(row['distribution'] or 0) for row in yearly_totals],
    }


def reportMonthly(request):
    projects = Project.objects.order_by('name')
    selected_project_id = request.GET.get('project', '')
    transactions = Transaction.objects.all()
    selected_project = None

    if selected_project_id:
        try:
            selected_project_id = int(selected_project_id)
        except ValueError as exc:
            raise Http404("Project not found") from exc

        selected_project = projects.filter(pk=selected_project_id).first()
        if selected_project is None:
            raise Http404("Project not found")
        transactions = transactions.filter(project=selected_project)

    chart_data = {
        **_yearly_contribution_distribution(transactions),
        'title': (
            f"Contribution vs Distributions - {selected_project.name}"
            if selected_project
            else 'Contribution vs Distributions - All Projects'
        ),
    }

    return render(request, 'charts.html', {
        'projects': projects,
        'selected_project': selected_project,
        'chart_data': chart_data,
    })


def annualContributionDistribution(request):
    chart_data = _yearly_contribution_distribution(Transaction.objects.all())
    return render(request, 'annual_contribution_distribution.html', {
        'chart_data': chart_data,
    })


def data_monthly(request):
    yy = dt.datetime.today().replace(day=1)

    transaction = read_frame(Transaction.objects.all())
    txs = transaction.loc[:,['date','exType','amount']]
    txs['year'] = du.DateUtil.cv2Year(txs['date'])
    txs['month'] = du.DateUtil.cv2Month(txs['date'])
    report = txs.groupby(["exType","year","month"]).agg({'amount':'sum'}).reset_index()

    for index, data in report.iterrows():
        ext = data['exType']
        yr = data['year']
        mm = data['month']
        
        row = ReportByMonth.objects.filter(exType=ext).filter(year=yr).filter(month=mm) 
        if bool(row):
            row = row.first()
        else:
            row = ReportByMonth()
            row.year = data['year']
            row.month = data['month']
            row.exType = data['exType']

        row.amount = data['amount']
        row.save()

    mm = dt.datetime.today().strftime("%b")
    yy = dt.datetime.today().year
    dataset= read_frame(ReportByMonth.objects.all())
    datasetInc=dataset.loc[lambda df:df['exType'].str.contains('Contribution'),('year','amount')]
    datasetEx=dataset.loc[lambda df:~df['exType'].str.contains('Contribution'),('year','amount')]
  
    exGroup = datasetEx.groupby(['year']).agg({'amount':'sum'})
    exGroup.reset_index(inplace=True)
    exGroup.rename(columns={'amount':'Distribution'}, inplace=True)
    inGroup = datasetInc.groupby(['year']).agg({'amount':'sum'})
    inGroup.rename(columns={'amount':'Contribution'}, inplace=True)
    data=exGroup.merge(inGroup,on='year')
    data.fillna(0,inplace=True)
    dataX = data['year']
    dataY1 = data['Distribution']
    dataY2 = data['Contribution']
    
    chart = {
        'chart':{'type':'bar'},
        'title': {'text': 'Annual Contribution vs Distribution'},
        'xAxis':{
            'categories':list(dataX)
        },
        'yAxis':{
            'title':{
                'text':'Amount in Rs.'
            }
        },
        'plotOptions':{
            'series':{
                'stacking':'normal'
            }
        },
        'series': [{
            'name': 'Distribution',
            'data':list(dataY1),
        },{
            'name': 'Contribution',
            'data':list(dataY2),
        }]
    }

    return JsonResponse(chart)

def data_monthlyAvg(request):
    today = dt.datetime.today()
    mm = today.strftime("%b")
    yy = today.year
    #dataset    = read_frame(ReportByMonth.objects.exclude(month=mm).exclude(year=yy).exclude(exType='Contribution').exclude(exType='Monthly Contribution'))
    dataset    = read_frame(ReportByMonth.objects.all().values("exType","amount"))
    
    exGroup = dataset.groupby(['exType']).agg({'amount':'sum'})

    exGroup.reset_index(inplace=True)
    dataX = []
    for i, row in exGroup.iterrows():
         data={'name':row['exType'],'y':row['amount']}
         dataX.append(data)
 
    chart = {
        'chart':{
            'type': 'pie'
        },
        'title': {
            'text': 'Expense by Category',
            'align': 'center'
        },
    
        'plotOptions':{
           'pie': {
                'allowPointSelect': 'true',
                'cursor': 'pointer',
                'dataLabels': {
                    'enabled': 'true',
                    'format': '<b>{point.name}</b>: {point.percentage:.1f} %'
                }
            }
        },
    
        'series': [{
            'type': 'pie',
            'data':dataX,
        }]
    }

    return JsonResponse(chart)

def annualContribution(request):
    contribution_transactions = Transaction.objects.filter(
        txType=Transaction.TxType_DEPOSIT,
        exType__expense__in=('Contribution', 'Monthly Contribution'),
    )
    years = list(
        contribution_transactions.annotate(year=TruncYear('date'))
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    years = [year.year for year in years]
    all_years_selected = request.GET.get('year') == 'all'
    selected_year = years[0] if years and not all_years_selected else None
    requested_year = request.GET.get('year')
    if requested_year and not all_years_selected:
        try:
            requested_year = int(requested_year)
        except ValueError as exc:
            raise Http404("Year not found") from exc
        if requested_year not in years:
            raise Http404("Year not found")
        selected_year = requested_year

    report_rows = contribution_transactions.annotate(
        year=TruncYear('date'),
        amount_lkr=Case(
            When(amountLocal=0, then=F('amount')),
            default=F('amountLocal'),
            output_field=IntegerField(),
        ),
    )
    if selected_year is not None:
        report_rows = report_rows.filter(date__year=selected_year)
    elif not all_years_selected:
        report_rows = report_rows.none()
    totals = (
        report_rows.values('exType__expense')
        .annotate(total=Sum('amount_lkr'))
        .order_by('exType__expense')
    )
    categories = [
        {'name': row['exType__expense'], 'amount': float(row['total'] or 0)}
        for row in totals
    ]

    return render(request, 'annual_contribution.html', {
        'years': years,
        'selected_year': selected_year,
        'all_years_selected': all_years_selected,
        'categories': categories,
        'chart_data': {
            'labels': [category['name'] for category in categories],
            'values': [category['amount'] for category in categories],
        },
    })


def expenseByCategory(request):
    years = list(
        ReportByMonth.objects.order_by()
        .values_list('year', flat=True)
        .distinct()
        .order_by('-year')
    )
    requested_year = request.GET.get('year')
    selected_year = None
    if requested_year and requested_year != 'all':
        try:
            selected_year = int(requested_year)
        except ValueError as exc:
            raise Http404("Year not found") from exc
        if selected_year not in years:
            raise Http404("Year not found")

    report_rows = ReportByMonth.objects.all()
    if selected_year is not None:
        report_rows = report_rows.filter(year=selected_year)
    totals = (
        report_rows.annotate(category=Trim('exType'))
        .exclude(category__in=('Contribution', 'Monthly Contribution'))
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('category')
    )
    categories = [
        {'name': row['category'], 'amount': float(row['total'] or 0)}
        for row in totals
    ]

    return render(request, 'expense_by_category.html', {
        'years': years,
        'selected_year': selected_year,
        'categories': categories,
        'chart_data': {
            'labels': [category['name'] for category in categories],
            'values': [category['amount'] for category in categories],
        },
    })


def beneficiariesReport(request):
    counts_by_category = {
        row['category']: row
        for row in Beneficiary.objects.values('category').annotate(
            active=Count('id', filter=Q(status='Active')),
            inactive=Count('id', filter=Q(status='Inactive')),
            total=Count('id'),
        )
    }
    categories = [
        {
            'name': category,
            'active': counts_by_category.get(category, {}).get('active', 0),
            'inactive': counts_by_category.get(category, {}).get('inactive', 0),
            'total': counts_by_category.get(category, {}).get('total', 0),
        }
        for category, _ in Beneficiary.CATEGORY
    ]

    return render(request, 'beneficiaries_report.html', {
        'categories': categories,
        'chart_data': {
            'labels': [category['name'] for category in categories],
            'active': [category['active'] for category in categories],
            'inactive': [category['inactive'] for category in categories],
        },
        'total_beneficiaries': sum(category['total'] for category in categories),
        'active_beneficiaries': sum(category['active'] for category in categories),
        'inactive_beneficiaries': sum(category['inactive'] for category in categories),
    })
