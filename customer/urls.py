# customer/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("ajax/customers/", views.customers_json, name="customers_json"),
]
