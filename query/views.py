from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Salom Bobur aka 👋")




def farmer_report(request):

    return render(request, "query/farmer_report.html")
