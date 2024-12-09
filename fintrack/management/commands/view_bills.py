# BaseCommand: base class for all custom Django management commands
# Custome command must inherit from BaseCommand and implement handle() which contains the logic
from django.core.management.base import BaseCommand
from fintrack.models import Bill
from prettytable import PrettyTable

class Command(BaseCommand):
    # Displayed when run 'python manage.py help view_bills'
    help = "View all bills"

    def handle(self, *args, **kwargs):
        # Creates table object with columns
        table = PrettyTable(["User", "Description", "Amount", "Category", "Due Date", "Recurring?", "Recurrence Period"])
        bills = Bill.objects.all()
        for bill in bills:
            table.add_row([
                bill.user,
                bill.description,
                bill.amount,
                bill.category.name,
                bill.due_date,
                bill.is_recurring,
                bill.recurrence_period
            ])
        self.stdout.write(str(table))