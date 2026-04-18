from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/me/', views.current_user_view),

    # Profile
    path('profile/', views.profile_view),
    
    # Categories
    path('categories/', views.categories_view),

    # Expenses
    path('expenses/', views.ExpenseListCreateView.as_view()),
    path('expenses/<int:pk>/', views.ExpenseDetailView.as_view()),
    path('expenses/stats/', views.expense_stats_view),

]