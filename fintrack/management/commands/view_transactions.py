# BaseCommand: base class for all custom Django management commands
# Custome command must inherit from BaseCommand and implement handle() which contains the logic
from django.core.management.base import BaseCommand
from fintrack.models import Transaction
from prettytable import PrettyTable

class Command(BaseCommand):
    # Displayed when run 'python manage.py help view_transactions'
    help = "View all transactions"

    def handle(self, *args, **kwargs):
        # Creates table object with columns
        table = PrettyTable(["User", "Amount", "Date", "Description", "Type", "Category"])
        transactions = Transaction.objects.all()
        for transaction in transactions:
            table.add_row([
                transaction.user,
                transaction.amount,
                transaction.date,
                transaction.description,
                transaction.type,
                transaction.category.name
            ])
        self.stdout.write(str(table))