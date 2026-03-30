from django.urls import path,re_path,include
from .views import reportMonthly,data_monthly, data_monthlyAvg

urlpatterns = [
    re_path(r'reportByMonth', reportMonthly, name='reportByMonth'),
    re_path(r'data_monthlyAvg', data_monthlyAvg, name='data_monthlyAvg'),
    re_path(r'data_monthly', data_monthly, name='data_monthly'),
]