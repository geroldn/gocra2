""" gocra Django views """
# Create your views here.
import logging
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView
from .models import Club, Player
from .forms import UploadFileForm
from .helpers import ExternalMacMahon

logging.basicConfig(filename='log/gocra.log', level=logging.DEBUG)


def index(request):
    """ Render the gocra index page """
    return render(request, 'wgocra/index.html')

def current(request):
    ''' This is just a sample. Will be removed '''
    return render(request, 'wgocra/current.html')
#    return HttpResponse("Let's have the current series.")

class SeriesView(TemplateView):
    """
    Render one Gocra Series.
    Uses Participants and Results
    """
    template_name = 'wgocra/series.html'

class ClubListView(ListView):
    """ Render list of clubs """
    model = Club
    template_name = 'wgocra/club_list.htl'

class PlayerListView(ListView):
    """ Render list of players """
    model = Player
    template_name = 'wgocra/player_list.htl'

def upload_macmahon(request):
    """ Import macmahon file from local """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        logging.debug(request.FILES['file'])
        if form.is_valid():
#            logging.debug('POST valid')
            macmahon = ExternalMacMahon()
            macmahon.xml_import(request.FILES['file'])
            request.session['mname'] = macmahon.doc['Tournament']['Name']
            return HttpResponseRedirect(reverse('gocra-series'))
        logging.debug('POST not valid')
    else:
        logging.debug('not POST')
        form = UploadFileForm()
    return render(request, 'wgocra/upload.html', {'form': form})
