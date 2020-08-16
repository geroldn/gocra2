""" gocra Django views """
# Create your views here.
#import logging
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView, DetailView
from .models import Club, Player, Series, Participant, Result
from .forms import UploadFileForm
from .helpers import ExternalMacMahon

#logging.basicConfig(filename='log/gocra.log', level=logging.DEBUG)


def index(request):
    """ Render the gocra index page """
    return render(request, 'wgocra/index.html')

def current(request):
    ''' This is just a sample. Will be removed '''
    return render(request, 'wgocra/current.html')
#    return HttpResponse("Let's have the current series.")

class SeriesDetailView(ListView):
    """
    Render one Gocra Series.
    Uses Participants and Results
    ListView on Results
    """
    template_name = 'wgocra/series.html'
    context_object_name = 'series_results'
    queryset = Result.objects.filter(participant__series__seriesIsOpen=True)
    ordering = ['participant__mm_id']

class SeriesListView(ListView):
    """
    Renders a list of Gocra Series.
    """
    model = Series
    ordering = ['-name', '-version']
    template_name = 'wgocra/series_all.html'

class ClubListView(ListView):
    """ Render list of clubs """
    model = Club
    template_name = 'wgocra/club_list.html'

class PlayerListView(ListView):
    """ Render list of players """
    model = Player
    template_name = 'wgocra/player_list.html'

def upload_macmahon(request):
    """ Import macmahon file from local """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            macmahon = ExternalMacMahon()
            series_id = macmahon.xml_import(request.FILES['file'])
            request.session['series_qs'] = series_id
            return HttpResponseRedirect(reverse('gocra-series-list'))
    else:
        form = UploadFileForm()
    return render(request, 'wgocra/upload.html', {'form': form})

def series_open(request, *args, **kwargs):
    id = kwargs['id']
    qs1 = Series.objects.filter(seriesIsOpen=True)
    for series in qs1:
        series.seriesIsOpen = False
        series.save()
    qs2 = Series.objects.filter(pk=id)
    for series in qs2:
        series.seriesIsOpen = True
        series.save()
    return HttpResponseRedirect(reverse('gocra-series-list'))

