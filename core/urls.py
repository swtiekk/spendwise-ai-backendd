from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view()),
    path('auth/me/', views.current_user_view),

    # Profile
    path('profile/', views.profile_view),

]