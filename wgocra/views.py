""" gocra Django views """
# Create your views here.
#import logging
from django.db.models import Exists, OuterRef
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView
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

class RoundDetailView(TemplateView):
    """
    Render Round as Result Details
    """
    template_name = 'wgocra/round.html'

    def get_context_data(self, **kwargs):
        #import pdb; pdb.set_trace()
        context = super().get_context_data(**kwargs)
        serie = Series.objects.get(seriesIsOpen=True)
        if serie:
            #serie = series[0]
            round_results = Result.objects.filter(
                participant__series=serie
            ).filter(
                round=serie.currentRoundNumber
            ).filter(
                color='B'
            )
            context['round_results'] = round_results
            null_pairing = Result.objects.filter(
                participant=OuterRef('pk')
            ).filter(
                color=None
            ).filter(
                playing=True
            ).filter(
                round=serie.currentRoundNumber
            )
            not_paired = Participant.objects.filter(
                series=serie
            ).filter(
                Exists(null_pairing)
            )
            context['not_paired'] = not_paired
            return context
        return None

class SeriesDetailView(TemplateView):
    """
    Render RESULTS from one Gocra Series.
    Uses Participants and Results
    ListView on Results
    """
    template_name = 'wgocra/series.html'
    #context_object_name = 'series_results'

    def get_context_data(self, **kwargs):
        #import pdb; pdb.set_trace()
        context = super().get_context_data(**kwargs)
        series_list = Series.objects.filter(seriesIsOpen=True)
        context['series'] = series_list
        series = series_list[0]
        current_round_number = series.currentRoundNumber
        series_results = Result.objects.filter(
            participant__series=series
        ).order_by('participant__mm_id', 'round')
        context['series_results'] = series_results
        # create round headings for rendering:
        rounds = []
        if series:
            nrounds = series.numberOfRounds
            for n_round in range(nrounds):
                rounds.append({
                    'round': n_round+1,
                    'name': 'Ronde {:d}'.format(n_round+1)
                })
        context['rounds'] = rounds
        context['current'] = current_round_number
        return context

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

def series_set_round(request, *args, **kwargs):
    #import pdb; pdb.set_trace()
    round = kwargs['round']
    qs1 = Series.objects.filter(seriesIsOpen=True)
    if qs1:
        series = qs1[0]
        series.currentRoundNumber = round
        series.save()
        '''
        qs2 = Result.objects.filter(participant__series=series)
        if qs2:
            qs2[0].save()
        '''
    return HttpResponseRedirect(reverse('gocra-series'))

def series_delete(request, *args, **kwargs):
    """ Delete specific series """
    series_id = kwargs['id']
    series = Series.objects.filter(pk=series_id)
    if series:
        series.delete()
    return HttpResponseRedirect(reverse('gocra-series-list'))

def series_open(request, *args, **kwargs):
    """ Set specific series as open """
    series_id = kwargs['id']
    qs1 = Series.objects.filter(seriesIsOpen=True)
    for series in qs1:
        series.seriesIsOpen = False
        series.save()
    qs2 = Series.objects.filter(pk=series_id)
    for series in qs2:
        series.seriesIsOpen = True
        series.save()
    return HttpResponseRedirect(reverse('gocra-series-list'))

def result_toggle_playing(request, *args, **kwargs):
    """ Toggle round result as playing for player """
    result_id = kwargs['id']
    qs1 = Result.objects.filter(pk=result_id)
    for result in qs1:
        result.playing = not result.playing
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

