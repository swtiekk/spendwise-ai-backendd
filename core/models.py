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
    
class Category(models.Model):
    CATEGORY_CHOICES = [
        ('food',          'Food & Dining'),
        ('transport',     'Transport'),
        ('entertainment', 'Entertainment'),
        ('utilities',     'Utilities'),
        ('shopping',      'Shopping'),
        ('health',        'Health'),
        ('education',     'Education'),
        ('savings',       'Savings'),
        ('other',         'Other'),
    ]
    key   = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    label = models.CharField(max_length=50)
    icon  = models.CharField(max_length=10)
    color = models.CharField(max_length=10)

    def __str__(self):
        return self.label


class Expense(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    timestamp   = models.DateTimeField()
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - ₱{self.amount}"