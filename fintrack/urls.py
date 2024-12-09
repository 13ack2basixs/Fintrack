from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register"),
    path("home", views.home, name="home"),
    path("transactions", views.transactions, name="transactions"),
    path("budget", views.budget, name="budget"),
    path("dashboard", views.dashboard, name="dashboard"),
    path('delete-transaction/<int:id>/', views.delete_transaction, name='delete_transaction'),
    path('delete-budget/<int:id>/', views.delete_budget, name='delete_budget'),
    path('bills', views.bills, name='bills'),
    path('delete-bill/<int:id>/', views.delete_bill, name='delete_bill'),
    path('paid-bill/<int:id>/', views.paid_bill, name='paid_bill'),
    path("get-barchart-data/<str:period>/", views.get_income_expenses_by_period, name="get_barchart_data"),
    path("get-piechart-data/", views.get_income_expenses_by_category, name="get_piechart_data"),

]
