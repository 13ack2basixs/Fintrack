from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.utils.timezone import now 
from django.contrib import messages
from django.db import models
from datetime import date, timedelta
from django.db.models import Sum
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required

from .utils import convert_to_sgd, create_paypal_payment
from .models import User, Category, Transaction, Budget, Currency, RecurrencePeriod, Bill

# Create your views here.

def send_payment(request, id):
    if request.method == 'POST':
        try:
            transaction = Transaction.objects.get(id=id)
            amount = transaction.amount

            return_url = request.build_absolute_uri(f'/transactions?payment_status=success&id={id}')
            cancel_url = request.build_absolute_uri(f'/transactions?payment_status=cancel&id={id}')

            approval_url = create_paypal_payment(amount, return_url, cancel_url)
            return HttpResponseRedirect(approval_url)
        except Transaction.DoesNotExist:
            return HttpResponse("Transaction not found.")
        except Exception as e:
            return HttpResponse(f"Error processing payment: {str(e)}") 

def get_income_expenses_by_period(request, period):
    if period == "weeks":
        income_data = Transaction.objects.filter(user=request.user, type="Income") \
            .annotate(time_period=TruncWeek('date')) \
            .values('time_period') \
            .annotate(total_income=Sum('amount')) \
            .order_by('time_period')
        
        expense_data = Transaction.objects.filter(user=request.user, type="Expense") \
            .annotate(time_period=TruncWeek('date')) \
            .values('time_period') \
            .annotate(total_expenses=Sum('amount')) \
            .order_by('time_period')
        
    elif period == "months":
        income_data = Transaction.objects.filter(user=request.user, type="Income") \
        .annotate(time_period=TruncMonth('date')) \
        .values('time_period') \
        .annotate(total_income=Sum('amount')) \
        .order_by('time_period')
        
        expense_data = Transaction.objects.filter(user=request.user, type="Expense") \
            .annotate(time_period=TruncMonth('date')) \
            .values('time_period') \
            .annotate(total_expenses=Sum('amount')) \
            .order_by('time_period')
        
    elif period == "years":
        income_data = Transaction.objects.filter(user=request.user, type="Income") \
            .annotate(time_period=TruncYear('date')) \
            .values('time_period') \
            .annotate(total_income=Sum('amount')) \
            .order_by('time_period')
        
        expense_data = Transaction.objects.filter(user=request.user, type="Expense") \
            .annotate(time_period=TruncYear('date')) \
            .values('time_period') \
            .annotate(total_expenses=Sum('amount')) \
            .order_by('time_period')

    # Combine income and expense data
    combined_data = {}
    for entry in income_data:
        key = entry['time_period']
        combined_data[key] = {'total_income': entry['total_income'], 'total_expenses': 0}

    for entry in expense_data:
        key = entry['time_period']
        if key not in combined_data:
            combined_data[key] = {'total_income': 0, 'total_expenses': entry['total_expenses']}
        else:
            combined_data[key]['total_expenses'] = entry['total_expenses']

    chart_data = {
        "labels": [key.strftime('%Y-%m-%d') for key in combined_data.keys()],
        "income": [data['total_income'] for data in combined_data.values()],
        "expenses": [data['total_expenses'] for data in combined_data.values()]
    }
    return JsonResponse(chart_data)

def get_income_expenses_by_category(request):
    # Total expenses from each category
    # __name to access field from related model via a foreign key 
    # [ {'cat__name': ..., 'total': ...}, {...} ] 
    expenses_by_category = Transaction.objects.filter(user=request.user, type="Expense") \
            .values('category__name') \
            .annotate(total=Sum('amount'))
    # Returns list anymore not QuerySet
    expenses_by_category = sorted(expenses_by_category, key=lambda i: i['total'], reverse=True)[:5]
    
    # Expenses Labels and Data
    expenses_labels = [item['category__name'] for item in expenses_by_category]
    expenses_data = [float(item['total']) for item in expenses_by_category]


    # Total income from each category
    # __name to access field from related model via a foreign key
    income_by_category = Transaction.objects.filter(user=request.user, type="Income") \
            .values('category__name') \
            .annotate(total=Sum('amount'))
    income_by_category = sorted(income_by_category, key=lambda i: i['total'], reverse=True)[:5]

    # Income Labels and Data
    income_labels = [item['category__name'] for item in income_by_category]
    income_data = [float(item['total']) for item in income_by_category]

    return JsonResponse({
        "income_labels": income_labels,
        "income_data": income_data,
        "expenses_labels": expenses_labels,
        "expenses_data": expenses_data,
    })

def paid_bill(request, id):
    if request.method == 'POST':
        current_bill = Bill.objects.get(id=id)
        # Non-recurring Bill -> add it as an Expense and delete Bill
        if current_bill.recurrence_period is None:
            newTransaction = Transaction(
                user = request.user,
                amount = current_bill.amount,
                description = current_bill.description,
                type = "Expense",
                category = Category.objects.get(name="Bills"),
                currency = "SGD" 
            )
            newTransaction.save()
            current_bill.delete()
            return HttpResponseRedirect(reverse("bills"))
        # Bill is recurring -> delete current Bill and create new Bill
        else:
            if current_bill.recurrence_period.name == "Monthly":
                new_due_date = current_bill.due_date + relativedelta(months=1)
            elif current_bill.recurrence_period.name == "Quarterly":
                new_due_date = current_bill.due_date + relativedelta(months=3)
            elif current_bill.recurrence_period.name == 'Biannually':
                new_due_date = current_bill.due_date + relativedelta(months=6)
            else:
                new_due_date = current_bill.due_date + relativedelta(years=1)

            newBill = Bill(
                user = request.user,
                description = current_bill.description,
                amount = current_bill.amount,
                category = current_bill.category,
                due_date = new_due_date,
                is_recurring = current_bill.is_recurring,
                recurrence_period = current_bill.recurrence_period
            )
            newBill.save()

            newTransaction = Transaction(
                user = request.user,
                amount = current_bill.amount,
                description = current_bill.description,
                type = "Expense",
                category = Category.objects.get(name="Bills"),
                currency = "SGD" 
            )
            newTransaction.save()
            current_bill.delete()
            return HttpResponseRedirect(reverse("bills"))

def delete_bill(request, id):
    if request.method == 'POST':
        bill = Bill.objects.get(id=id)
        bill.delete()
    return HttpResponseRedirect(reverse("bills"))

def bills(request):
    if request.method == 'POST':
        amount = request.POST["amount"]
        description = request.POST["description"]
        category = request.POST["category"]
        due_date = request.POST["due_date"]
        is_recurring = request.POST.get("is_recurring", "")

        if not all([amount, description, category, due_date]):
            messages.error(request, "Please fill out all fields.")
            return HttpResponseRedirect(reverse("bills"))

        # Check if category is empty
        if category == "Choose...":
            messages.error(request, "Please select a valid category")
            return HttpResponseRedirect(reverse("bills"))
        category_model = Category.objects.get(name = category)
        
        # Check if is_recurring is empty
        if is_recurring not in ['Yes', 'No']:
            messages.error(request, "Please state if bill is recurring")
            return HttpResponseRedirect(reverse("bills"))
        
        # Change it to Boolean because it is set as BooleanField in models.py
        is_recurring = True if is_recurring == 'Yes' else False

        recurrence_period = request.POST["recurrence_period"] if is_recurring else None
        
        # Check if required fields are missing or bill is recurring but recurrence_period empty 
        recurrence_period_model = None
        if is_recurring:
            if recurrence_period == 'Choose...':
                messages.error(request, "Please select a recurrence period.")
                return HttpResponseRedirect(reverse("bills"))
            recurrence_period_model = RecurrencePeriod.objects.get(name=recurrence_period)

        newBill = Bill(
            user = request.user,
            description = description,
            amount = amount,
            category = category_model,
            due_date = due_date,
            is_recurring = is_recurring,
            recurrence_period = recurrence_period_model
        )
        newBill.save()
        return HttpResponseRedirect(reverse("bills"))
    else:
        # Display bills
        categories = Category.objects.all().order_by("name")
        bills = Bill.objects.filter(user=request.user).order_by("due_date")
        periods = RecurrencePeriod.objects.all()
        return render(request, "fintrack/bills.html", {
                "bills": bills,
                "categories": categories,
                "periods": periods
            })

@login_required
def dashboard(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse("login"))
    
    one_week = date.today() + timedelta(days=7)
    bills = Bill.objects.filter(user=request.user, due_date__lte=one_week).order_by("due_date")
    
    # Add budget spending when new transaction of that budget category is made
    budgets = Budget.objects.filter(user=request.user).order_by("category")
    for transaction in Transaction.objects.filter(is_processed=False):
            # Queryset, not Budget instance
            budget = Budget.objects.filter(category=transaction.category)
            if not budget.exists(): # No budget of that category
                continue
            b = budget.first()
            b.amount_spent += transaction.amount
            transaction.is_processed = True
            transaction.save()
            b.save()
    
    # Get the data from sessions
    ts = Transaction.objects.filter(user=request.user).order_by("-date")
    total_income, total_expenses = 0, 0  
    for t in ts:
        if t.type == 'Income':
            total_income += t.amount
        else:
            total_expenses += t.amount
    balance = total_income - total_expenses

    return render(request, "fintrack/dashboard.html", {
            "total_income": total_income,
            "total_expenses": total_expenses,
            "bills": bills,
            "balance": round(balance, 2),
            "budgets": budgets,
        })

def delete_budget(request, id):
    if request.method == 'POST':
        budget = Budget.objects.get(id=id)
        budget.delete()
    return HttpResponseRedirect(reverse("budget"))

def budget(request):
    # Remove expired budgets
    Budget.objects.filter(end_date__lt=now().date()).delete()

    if request.method == 'POST':
        amount = request.POST["amount"]
        category = request.POST["category"]
        start_date = request.POST["startdate"]
        end_date = request.POST["enddate"]

        # Check for empty fields
        if not all([amount, category, start_date, end_date]):
            messages.error(request, "Please fill out all fields.")
            return HttpResponseRedirect(reverse("budget"))

        # Check for duplicates of budgets of same category
        cat = Category.objects.get(name=category)
        if Budget.objects.filter(category=cat).exists():
            messages.error(request, "Only one budget for each category is allowed.")
            return HttpResponseRedirect(reverse("budget"))

        # Get the respective category from the class
        category_model = Category.objects.get(name = category)
        
        newBudget = Budget(
            user = request.user,
            amount = amount,
            category = category_model,
            start_date = start_date,
            end_date = end_date
        )
        newBudget.save()
        return HttpResponseRedirect(reverse("budget"))
    else:
        # Display Budgets
        categories = Category.objects.all().order_by("name")
        budgets = Budget.objects.filter(user=request.user).order_by("category")
        return render(request, "fintrack/budget.html", {
            'user': request.user,
            'categories': categories,
            'budgets': budgets,
        })
    
def delete_transaction(request, id):
    if request.method == 'POST':
        transaction = Transaction.objects.get(id=id)
        transaction.delete()
        budgetQS = Budget.objects.filter(category=transaction.category)
        if not budgetQS:
            return HttpResponseRedirect(reverse("transactions"))
        budget = budgetQS.first()
        budget.amount_spent -= transaction.amount
        budget.save()
    return HttpResponseRedirect(reverse("transactions"))

def transactions(request):
    if request.method == 'POST':
        description = request.POST["description"]
        amount = request.POST["amount"]
        currency = request.POST["currency"]
        category = request.POST["category"]
        type = request.POST["type"]

        # Check for empty fields
        if not all([description, amount, currency, category, type]):
            messages.error(request, "Please fill out all fields.")
            return HttpResponseRedirect(reverse("transactions"))
        
        # Get category from the class
        if category == 'Choose...':
            messages.error(request, "Please choose a category")
            return HttpResponseRedirect(reverse("transactions"))
        category_model = Category.objects.get(name = category)

        # Convert currency to SGD
        try: 
            converted_amount = convert_to_sgd(amount, currency)
        except ValueError as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse("transactions"))

        newTransaction = Transaction(
            user = request.user,
            amount = converted_amount,
            description = description,
            type = type,
            category = category_model,
            currency = "SGD"
        )
        newTransaction.save()

        # Check if the transaction type is 'Expense' and exceeds budget
        if type == "Expense":
            # Fetch user's budgets for the selected category
            budget = Budget.objects.filter(user=request.user, category=category_model).first()

            if budget:
                # Calculate total expenses for the category
                total_expenses = Transaction.objects.filter(
                    user=request.user,
                    category=category_model,
                    type="Expense"
                ).aggregate(total=models.Sum("amount"))["total"] or 0

                # Compare total expenses with the budget
                if total_expenses > budget.amount:
                    messages.error(
                        request,
                        f"You have exceeded your budget for {category_model.name}! "
                        f"Budget: {budget.amount}, Total Expenses: {total_expenses:.2f}"
                    )
        return HttpResponseRedirect(reverse("transactions"))
    else:
        # Transaction History
        categories = Category.objects.all().order_by("name")
        currencies = Currency.objects.all().order_by("symbol")
        transactions = Transaction.objects.filter(user=request.user).order_by("-date")

        # For sending payments 
        payment_status = request.GET.get("payment_status", None)
        id = request.GET.get("id", None)
        t = Transaction.objects.filter(id=id)
        if t.exists():
            t = t.first()
        if payment_status == 'success':
            messages.success(
                request,
                f"Payment was successful! Date: {t.date}, Description: {t.description}, Amount: {t.amount}"
            )
        elif payment_status == 'cancel':
            messages.warning(
                request,
                f"Payment was cancelled. Date: {t.date}, Description: {t.description}, Amount: {t.amount}"
            )

        return render(request, "fintrack/transactions.html", {
            "categories": categories,
            "currencies": currencies,
            "transactions": transactions,
        })

def home(request):
    return render(request, "fintrack/home.html", {
        'user': request.user
    })

def index(request):
    return render(request, "fintrack/index.html")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        # print(password)
        # print(user)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'redirect_url': reverse('dashboard')})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid Credentials'})
    else:
        return render(request, 'fintrack/index.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return JsonResponse({'success': False, 'error': 'Passwords do not match'})
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Username already exists'})
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already exists'})
        
        user = User.objects.create_user(username, email, password)
        user.save()
        return JsonResponse({'success': True})
    return render(request, 'fintrack/index.html')
    