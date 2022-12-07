from .models import Member, Transaction
from django.contrib.auth.models import User


from rest_framework import serializers

class MemberPhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Member
        fields = ['mobile']

class MemberSerializer(serializers.ModelSerializer):
    # mobile = serializers.SlugRelatedField(
    #     many=True,
    #     read_only=True,
    #     slug_field='mobile'
    #  )
    #profile = serializers.StringRelatedField(many=True)
    class Meta:
        model  = User
        fields = ['first_name','last_name','email']

class TransactionSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name")
    project_name = serializers.CharField(source="project.name")
    owner_name  = serializers.CharField(source="owner.first_name")
    ex_name = serializers.CharField(source = "exType.expense")

    class Meta:
        model = Transaction
        fields = ['bank_name','project_name','owner_name','amount','date','txType','ex_name','confirmed']