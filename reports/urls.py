from django.urls import path,re_path,include

from accounts import views
from .views import (
    annualContribution,
    annualContributionDistribution,
    beneficiariesReport,
    data_monthly,
    data_monthlyAvg,
    expenseByCategory,
    reportMonthly,
)

urlpatterns = [
    path('dashboard/', reportMonthly, name='dashboard'),
    path('contribution-distribution/', reportMonthly, name='contributionDistribution'),
    path('annual-contribution-distribution/', annualContributionDistribution, name='annualContributionDistribution'),
    path('annual-contribution/', annualContribution, name='annualContribution'),
    path('expense-by-category/', expenseByCategory, name='expenseByCategory'),
    path('beneficiaries-report/', beneficiariesReport, name='beneficiariesReport'),
    re_path(r'reportByMonth', reportMonthly, name='reportByMonth'),
    re_path(r'data_monthlyAvg', data_monthlyAvg, name='data_monthlyAvg'),
    re_path(r'data_monthly', data_monthly, name='data_monthly'),
]