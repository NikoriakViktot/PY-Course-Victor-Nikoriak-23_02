from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse

def hello_notes(request):
    return HttpResponse("Hello from Notes app.")