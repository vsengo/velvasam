from django.db import models
from accounts.models import ExpenseType
from django.utils  import timezone

# Create your models here.
class ReportByMonth(models.Model):
    year = models.SmallIntegerField()
    month = models.CharField(max_length=8)
    exType = models.CharField(max_length=32)
    amount = models.IntegerField()
    updatedOn = models.DateTimeField(default=timezone.now)


