# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView

from wgocra.models import Club, Player

def index(request):
    return render(request, 'wgocra/index.html')

def current(request):
    return render(request, 'wgocra/current.html')
#    return HttpResponse("Let's have the current series.")

class ClubListView(ListView):
    model = Club
    template_name = 'wgocra/club_list.htl'

class PlayerListView(ListView):
    model = Player
    template_name = 'wgocra/player_list.htl'
