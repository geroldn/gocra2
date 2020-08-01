# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse
from django.views.generic.list import ListView
from .forms import UploadFileForm

import logging
logging.basicConfig(filename='log/gocra.log', level=logging.DEBUG)

from wgocra.models import Club, Player

def index(request):
    return render(request, 'wgocra/index.html')

def series(request):
    return render(request, 'wgocra/series.html')

def current(request):
    return render(request, 'wgocra/current.html')
#    return HttpResponse("Let's have the current series.")

class ClubListView(ListView):
    model = Club
    template_name = 'wgocra/club_list.htl'

class PlayerListView(ListView):
    model = Player
    template_name = 'wgocra/player_list.htl'

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        logging.debug(request.FILES['file'])
        if form.is_valid():
            logging.debug('POST valid')
            handle_uploaded_file(request.FILES['file'])
            return HttpResponseRedirect('wgocra/series.html')
        logging.debug('POST not valid')
    else:
        logging.debug('not POST')
        form = UploadFileForm()
    return render(request, 'wgocra/upload.html', {'form': form})
