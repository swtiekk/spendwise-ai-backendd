from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import (
    Alert, Category, Expense, Income,
    MLInsight, SavingsGoal, SmartPurchaseLog, UserProfile
)

from .serializers import (
    AlertSerializer, CategorySerializer, ExpenseSerializer,
    IncomeSerializer, MLInsightSerializer, RegisterSerializer,
    SavingsGoalSerializer, SmartPurchaseSerializer,
    UserProfileSerializer, UserSerializer,
)

# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


@api_view(['GET'])
def current_user_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
def profile_view(request):
    profile = request.user.profile

    if request.method == 'GET':
        return Response(UserProfileSerializer(profile).data)

    serializer = UserProfileSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)

    return Response(serializer.errors, status=400)