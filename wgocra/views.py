from django.shortcuts import render

from django.http import HttpResponse
# Create your views here.

def index(request):
    return HttpResponse("Hello world. You're in the wgocra index.")

def current(request):
    return render(request, 'wgocra/current.html')
#    return HttpResponse("Let's have the current series.")
