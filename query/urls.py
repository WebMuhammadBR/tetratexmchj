from django.urls import path
from .views import farmer_report,home

urlpatterns = [
    path("", home, name="home"),
    path("report/farmer/", farmer_report, name="farmer_report"),
]