from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    INCOME_TYPE_CHOICES = [
        ('salary',    'Salary'),
        ('allowance', 'Allowance'),
        ('freelance', 'Freelance'),
        ('other',     'Other'),
    ]
    INCOME_CYCLE_CHOICES = [
        ('weekly',   'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly',  'Monthly'),
    ]

    user                    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    income_type             = models.CharField(max_length=20, choices=INCOME_TYPE_CHOICES, default='salary')
    income_cycle            = models.CharField(max_length=20, choices=INCOME_CYCLE_CHOICES, default='monthly')
    income_amount           = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    next_income_date        = models.DateField(null=True, blank=True)
    savings_goal            = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notifications_enabled   = models.BooleanField(default=True)
    dark_mode               = models.BooleanField(default=False)
    currency                = models.CharField(max_length=10, default='PHP')
    language                = models.CharField(max_length=10, default='en')
    budget_alert_threshold  = models.IntegerField(default=80)
    push_notifications      = models.BooleanField(default=True)
    email_notifications     = models.BooleanField(default=True)
    budget_alerts           = models.BooleanField(default=True)
    weekly_reports          = models.BooleanField(default=True)
    spending_reminders      = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s profile"