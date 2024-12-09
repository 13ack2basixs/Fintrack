from django.contrib import admin
from .models import User, Category, Transaction, Budget, Currency, RecurrencePeriod, Bill


# Register your models here.
admin.site.register(User)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Budget)
admin.site.register(Currency)
admin.site.register(RecurrencePeriod)
admin.site.register(Bill)
