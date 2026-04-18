from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    UserProfile, Category, Expense, Income,
    SavingsGoal, Alert, MLInsight, SmartPurchaseLog
)


class RegisterSerializer(serializers.ModelSerializer):
    password     = serializers.CharField(write_only=True)
    income_type  = serializers.CharField(write_only=True, required=False)
    income_cycle = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'income_type', 'income_cycle']

    def create(self, validated_data):
        income_type  = validated_data.pop('income_type',  'other')
        income_cycle = validated_data.pop('income_cycle', 'monthly')
        password     = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        # signal already created profile, so get_or_create instead of create
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.income_type  = income_type
        profile.income_cycle = income_cycle
        profile.save()
        MLInsight.objects.get_or_create(user=user)
        return user