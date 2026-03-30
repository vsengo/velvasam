from django.shortcuts import render
from  django_pandas.io import read_frame
from django.http import JsonResponse
import pandas as pd
from accounts.models import Transaction
from .models import ReportByMonth
import datetime as dt
import util.date as du

def reportMonthly(request):
        return render(request, 'charts.html')

def data_monthly(request):
    yy = dt.datetime.today().replace(day=1)

    transaction = read_frame(Transaction.objects.filter(date__gt=yy))
    txs = transaction.loc[:,['date','exType','amount']]
    txs['year'] = du.DateUtil.cv2Year(txs['date'])
    txs['month'] = du.DateUtil.cv2Month(txs['date'])
    report = txs.groupby(["exType","year","month"]).sum().reset_index()

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
    dataset    = read_frame(ReportByMonth.objects.filter(month=mm).filter(year=yy).exclude(exType='Contribution').exclude(exType='Monthly Contribution'))

    exGroup = dataset.groupby(['exType']).sum()
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
            'text': 'Expense for '+mm+","+str(yy),
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

def data_monthlyAvg(request):
    today = dt.datetime.today()
    mm = today.strftime("%b")
    yy = today.year
    dataset    = read_frame(ReportByMonth.objects.exclude(month=mm).exclude(year=yy).exclude(exType='Contribution').exclude(exType='Monthly Contribution'))

    exGroup = dataset.groupby(['exType']).sum()

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
            'text': 'Average Expense by Category',
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


   

