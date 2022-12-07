from cgitb import text
from turtle import pd
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import IntegrityError
from accounts.models import Transaction, Project
import string
import pandas as pd
import numpy as np
from   django_pandas.io import read_frame

class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        transaction = read_frame(Transaction.objects.all())
        txs = transaction.loc[:,['txType','amount','project']]
        txs['project'] = txs['project'].str.strip()

        px = txs.groupby(['project','txType']).sum().reset_index()
        px.fillna(0)
        project = Project.objects.all()
        for prj in project.iterator():
            print(prj.name+"##")
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
            





