from django.forms import ValidationError
from django.test import TestCase
from .models import User, Category, Transaction, Budget, Currency, RecurrencePeriod, Bill
from django.urls import reverse
from .utils import get_exchange_rate, create_paypal_payment
from unittest.mock import patch, MagicMock

# Create your tests here.

class UserAuthTest(TestCase):
    # Verifies user registration is successful
    def test_register_user(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirmation": "password123"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    # Checks if registered user can log in
    def test_login_user(self):
        user = User.objects.create_user(username="testuser", password="password")
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "password"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("success", response.json())

class CategoryModelTest(TestCase):
    # Ensures Category object is created and stored
    def test_category_creation(self):
        Category.objects.create(name="Alcohol")
        self.assertTrue(Category.objects.filter(name="Alcohol").exists())

class CurrencyModelTest(TestCase):
    # Ensures Currency object is created and stored
    def test_currency_creation(self):
        currency = Currency.objects.create(name="US Dollar", symbol="USD")
        self.assertTrue(Currency.objects.filter(name="US Dollar").exists())
        self.assertEqual(str(currency), "US Dollar")

class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Utilities")

    # Ensures Transaction object is created and stored 
    def test_transaction_creation(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=50.00,
            description="Electric Bill",
            type="Expense",
            category=self.category,
            currency="SGD"
        )
        self.assertEqual(str(transaction), "Expense: testuser 50.0 on Utilities")

class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Savings")
    
    # Checks that amount_spent > amount will trigger ValidationError
    def test_budget_validation(self):
        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            amount=100.00,
            amount_spent=150.00,
            start_date="2024-01-01",
            end_date="2024-12-31"
        )
        with self.assertRaises(ValidationError):
            budget.clean()

class RecurrencePeriodModelTest(TestCase):
    # Ensures RecurrencePeriod object is created and stored
    def test_recurrence_period_creation(self):
        period = RecurrencePeriod.objects.create(name="Monthly")
        self.assertTrue(RecurrencePeriod.objects.filter(name="Monthly").exists())
        self.assertEqual(str(period), "Monthly")

class BillModelTest(TestCase):    
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Utilities")
        self.recurrence_period = RecurrencePeriod.objects.create(name="Monthly")

    # Ensures recurring bill is created and stored
    def test_bill_creation(self):
        bill = Bill.objects.create(
            user=self.user,
            description="Electric Bill",
            amount=100.00,
            category=self.category,
            due_date="2024-01-01",
            is_recurring=True,
            recurrence_period=self.recurrence_period
        )
        self.assertTrue(Bill.objects.filter(description="Electric Bill").exists())
        self.assertEqual(str(bill), f"{self.user} has upcoming bill - Electric Bill")

    # Ensures non-recurring bill is created and stored
    def test_non_recurring_bill(self):
        bill = Bill.objects.create(
            user=self.user,
            description="One-Time Payment",
            amount=50.00,
            category=self.category,
            due_date="2024-01-15",
            is_recurring=False
        )
        self.assertFalse(bill.is_recurring)
        self.assertIsNone(bill.recurrence_period)
    
    # Ensures recurring bill without recurrence period raises ValidationError
    def test_invalid_recurring_bill_in_view(self):
        response = self.client.post(reverse("bills"), {
            "amount": "75.00",
            "description": "Invalid Recurring Bill",
            "category": self.category.name,
            "due_date": "2024-01-20",
            "is_recurring": "Yes",
            "recurrence_period": "Choose..."
        })
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Please select a recurrence period.")
        self.assertFalse(Bill.objects.filter(description="Invalid Recurring Bill").exists())

class TransactionsFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Groceries")
        self.client.login(username="testuser", password="password")

    def test_missing_fields_in_transaction_form(self):
        response = self.client.post(reverse("transactions"), {
            "description": "",
            "amount": "",
            "currency": "",
            "category": "",
            "type": ""
        })
        self.assertEqual(response.status_code, 302) 
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Please fill out all fields.")
        self.assertFalse(Transaction.objects.filter(description="").exists())

class BudgetFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Utilities")
        self.client.login(username="testuser", password="password")

    def test_missing_fields_in_budget_form(self):
        response = self.client.post(reverse("budget"), {
            "amount": "",
            "category": "",
            "startdate": "",
            "enddate": ""
        })
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Please fill out all fields.")
        self.assertFalse(Budget.objects.filter(category=self.category).exists())

class BillsFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Utilities")
        self.period = RecurrencePeriod.objects.create(name="Monthly")
        self.client.login(username="testuser", password="password")

    def test_missing_fields_in_bills_form(self):
        response = self.client.post(reverse("bills"), {
            "amount": "",
            "description": "",
            "category": "",
            "due_date": "",
            "is_recurring": "Yes",
            "recurrence_period": ""
        })
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Please fill out all fields.")
        self.assertFalse(Bill.objects.filter(description="").exists())

    def test_recurring_bill_without_recurrence_period(self):
        response = self.client.post(reverse("bills"), {
            "amount": "50.00",
            "description": "Gym Membership",
            "category": self.category.name,
            "due_date": "2024-01-01",
            "is_recurring": "Yes",
            "recurrence_period": "Choose..."
        })
        self.assertEqual(response.status_code, 302)
        messages = list(response.wsgi_request._messages)
        self.assertEqual(str(messages[0]), "Please select a recurrence period.")
        self.assertFalse(Bill.objects.filter(description="Gym Membership").exists())

    def test_non_recurring_bill_without_recurrence_period(self):
        response = self.client.post(reverse("bills"), {
            "amount": "100.00",
            "description": "Electric Bill",
            "category": self.category.name,
            "due_date": "2024-01-01",
            "is_recurring": "No",
            "recurrence_period": ""
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Bill.objects.filter(description="Electric Bill").exists())

class DashboardViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")

    # Checks authenticated user can access dashboard view
    def test_dashboard_view_authenticated(self):
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "fintrack/dashboard.html")

    # Unauthenticated users are redirected to login view
    def test_dashboard_view_unauthenticated(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

class TransactionViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Groceries")
        self.client.login(username="testuser", password="password")

    # Checks new Transaction can be created via POST request and saved in database
    def test_transaction_creation_view(self):
        response = self.client.post(reverse("transactions"), {
            "description": "Groceries",
            "amount": "100",
            "currency": "SGD",
            "category": self.category.name,
            "type": "Expense"
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Transaction.objects.filter(description="Groceries").exists())

class RecurringBillTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Bills")
        self.period = RecurrencePeriod.objects.create(name="Monthly")
        self.bill = Bill.objects.create(
            user=self.user,
            description="Gym Membership",
            amount=50.00,
            category=self.category,
            due_date="2024-01-01",
            is_recurring=True,
            recurrence_period=self.period
        )

    # Simulates paying recurring bill, old bill is deleted new bill is recurred
    def test_recurring_bill_payment(self):
        self.client.login(username="testuser", password="password")
        response = self.client.post(reverse("paid_bill", args=[self.bill.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Bill.objects.filter(id=self.bill.id).exists())
        self.assertTrue(Bill.objects.filter(description="Gym Membership").exists())

class BillPaymentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category = Category.objects.create(name="Bills")
        self.bill = Bill.objects.create(
            user=self.user,
            description="Internet Bill",
            amount=100.00,
            category=self.category,
            due_date="2024-12-31",
            is_recurring=False
        )
        self.client.login(username="testuser", password="password")

    # Ensures bill is deleted and new transaction is created
    def test_paid_bill_view(self):
        response = self.client.post(reverse("paid_bill", args=[self.bill.id]))
        self.assertEqual(response.status_code, 302) 
        self.assertFalse(Bill.objects.filter(id=self.bill.id).exists())
        self.assertTrue(Transaction.objects.filter(description="Internet Bill").exists())

class ChartDataTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.category_income = Category.objects.create(name="Income")
        self.category_expense = Category.objects.create(name="Games")
        Transaction.objects.create(
            user=self.user, amount=100, description="Salary", type="Income", category=self.category_income, currency="SGD"
        )
        Transaction.objects.create(
            user=self.user, amount=50, description="Games", type="Expense", category=self.category_expense, currency="SGD"
        )
        self.client.login(username="testuser", password="password")

    # Checks accuracy of get_barchart_data endpoint with correct labels, data and specified period
    def test_income_expenses_by_period(self):
        response = self.client.get(reverse("get_barchart_data", args=["months"]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("labels", data)
        self.assertIn("income", data)
        self.assertIn("expenses", data)

    # Checks accuracy of get_piechart_data endpoint with correct labels and data
    def test_income_expenses_by_category(self):
        response = self.client.get(reverse("get_piechart_data"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("income_labels", data)
        self.assertIn("income_data", data)
        self.assertIn("expenses_labels", data)
        self.assertIn("expenses_data", data)
        self.assertIn(self.category_income.name, data["income_labels"])
        self.assertIn(self.category_expense.name, data["expenses_labels"])

class ExchangeRateAPITest(TestCase):
    @patch("requests.get")
    # Verifies accurate API call of get_exchange_rate
    def test_get_exchange_rate_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "success": True,
            "rates": {"USD": 1.0, "SGD": 1.35}
        }
        rate = get_exchange_rate("USD", "SGD")
        self.assertEqual(rate, 1.35)

class PayPalAPITest(TestCase):
    @patch("fintrack.utils.get_access_token")
    @patch("requests.post")
    # Verifies accurate API call of create_paypal_payment
    def test_create_paypal_payment_success(self, mock_post, mock_get_access_token):
        mock_get_access_token.return_value = "mock_access_token"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "links": [
                {"rel": "payer-action", "href": "http://example.com/pay"}
            ]
        }
        mock_post.return_value = mock_response

        result = create_paypal_payment(50.00, "http://example.com/success", "http://example.com/cancel")

        self.assertEqual(result, "http://example.com/pay")
        mock_get_access_token.assert_called_once()
        mock_post.assert_called_once_with(
            'https://api-m.sandbox.paypal.com/v2/checkout/orders',
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer mock_access_token",
            },
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "SGD",
                            "value": "50.00",
                        },
                    }
                ],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "return_url": "http://example.com/success",
                            "cancel_url": "http://example.com/cancel",
                        }
                    }
                },
            }
        )
 