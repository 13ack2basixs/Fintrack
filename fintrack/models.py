from django.db import models
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError

# Create your models here.

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Currency(models.Model):
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=3)
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    CHOICES = [
        ('Income', 'Income'),
        ('Expense', 'Expense'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=CHOICES)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    date = models.DateField()
    currency = models.CharField(max_length=3)
    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.type}: {self.user} {self.amount} on {self.category}'
    
class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    amount_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def clean(self):
        super().clean()
        if self.amount_spent > self.amount:
            raise ValidationError("Amount spent cannot exceed total budget")

    def __str__(self):
        return f'{self.user} has a budget of {self.amount} on {self.category}'

class RecurrencePeriod(models.Model):
    CHOICES = [
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Biannually', 'Biannually'),
        ('Annually', 'Annually')
    ]
    name = models.CharField(max_length=50, choices=CHOICES)

    def __str__(self):
        return self.name

class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    due_date = models.DateField()
    is_recurring = models.BooleanField(default=False)
    recurrence_period = models.ForeignKey(RecurrencePeriod, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f'{self.user} has upcoming bill - {self.description}'
