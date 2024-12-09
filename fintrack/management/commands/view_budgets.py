# BaseCommand: base class for all custom Django management commands
# Custome command must inherit from BaseCommand and implement handle() which contains the logic
from django.core.management.base import BaseCommand
from fintrack.models import Budget
from prettytable import PrettyTable

class Command(BaseCommand):
    # Displayed when run 'python manage.py help view_budgets'
    help = "View all budgets"

    def handle(self, *args, **kwargs):
        # Creates table object with columns
        table = PrettyTable(["User", "Amount", "Category", "Start Date", "End Date", "Amount Spent"])
        budgets = Budget.objects.all()
        for budget in budgets:
            table.add_row([
                budget.user,
                budget.amount,
                budget.category.name,
                budget.start_date,
                budget.end_date,
                budget.amount_spent
            ])
        self.stdout.write(str(table))