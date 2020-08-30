""" gocra Django views """
# Create your views here.
#import logging
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.db.models import Exists, OuterRef
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView
from .models import Club, Player, Series, Participant, Result
from .forms import UploadFileForm
from .helpers import ExternalMacMahon, get_handicap
from .ratingsystem import RatingSystem as Rsys

#logging.basicConfig(filename='log/gocra.log', level=logging.DEBUG)


def index(request):
    """ Render the gocra index page """
    return render(request, 'wgocra/index.html')

@method_decorator(login_required, name='dispatch')
class RoundDetailView(TemplateView):
    """
    Render Round as Result Details
    """
    template_name = 'wgocra/round.html'

    def get_context_data(self, **kwargs):
        #import pdb; pdb.set_trace()
        current = self.kwargs['current']
        context = super().get_context_data(**kwargs)
        serie = Series.objects.get(seriesIsOpen=True)
        if serie:
            round_results = Result.objects.filter(
                participant__series=serie
            ).filter(
                round=current
            ).filter(
                color='B'
            ).order_by('participant__nr')
            context['round_results'] = round_results
            null_pairing = Result.objects.filter(
                participant=OuterRef('pk')
            ).filter(
                color=None
            ).filter(
                playing=True
            ).filter(
                round=current
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
        # calculate the ratings:
        participants = Participant.objects.filter(series=series)
        self.calculate_rating(participants)
        self.rank_participants(participants, series)
        series_results = Result.objects.filter(
            participant__series=series
        ).order_by('participant__nr', 'round')
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

    def calculate_rating(self, participants):
        """
        Calculate rating gains for each result in the series
        """
        #import pdb; pdb.set_trace()
        for participant in participants:
            participant.resultrating = participant.rating
            participant.gain = 0
            participant.games = 0
            participant.wins = 0
            participant.score = 0.0 + participant.mm_score
            participant.new_rank = ''
            results = Result.objects.filter(
                participant=participant).order_by('round')
            for result in results:
                result.gain = 0
                if result.round <= participant.series.currentRoundNumber:
                    if result.color in ('B', 'W'):
                        if result.win in ('+', '-'):
                            result.gain = Rsys.calculate_gain(
                                result.color,
                                participant.rating,
                                result.opponent.rating,
                                result.handicap,
                                result.win == '+'
                            )
                            participant.resultrating += result.gain
                            participant.gain += result.gain
                            if result.win in ('+', '-'):
                                participant.games += 1
                            if result.win == '+':
                                participant.wins += 1
                                participant.score += 1.0
                        else:
                            participant.score += 0.5
                    else:
                        participant.score += 0.5
                result.save()
            participant.points_str = '{:d}/{:d}'.format(participant.wins, participant.games)
            if participant.gain < -100:
                participant.gain = -100
                participant.resultrating = participant.rating - 100
            participant.save()

    def rank_participants(self, participants, series):
        """
        Rank participants according to their results.
        """
        for p_enum in enumerate(
                sorted(
                    participants,
                    key=lambda ptnt: (ptnt.wins, ptnt.gain, ptnt.rating),
                    reverse=True
                ),
                1 #start rank value
            ):
            participant = participants.get(id=p_enum[1].id)
            participant.nr = p_enum[0]
            participant.save()
        results = Result.objects.filter(participant__series=series)

@method_decorator(login_required, name='dispatch')
class SeriesListView(ListView):
    """
    Renders a list of Gocra Series.
    """
    model = Series
    ordering = ['-name', '-version']
    template_name = 'wgocra/series_all.html'

@method_decorator(login_required, name='dispatch')
class ClubListView(ListView):
    """ Render list of clubs """
    model = Club
    template_name = 'wgocra/club_list.html'

@method_decorator(login_required, name='dispatch')
class PlayerListView(ListView):
    """ Render list of players """
    model = Player
    template_name = 'wgocra/player_list.html'

@login_required
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

@login_required
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

@login_required
def series_delete(request, *args, **kwargs):
    """ Delete specific series """
    series_id = kwargs['id']
    series = Series.objects.filter(pk=series_id)
    if series:
        series.delete()
    return HttpResponseRedirect(reverse('gocra-series-list'))

@login_required
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

@login_required
def result_toggle_playing(request, *args, **kwargs):
    """ Toggle round result as playing for player """
    result_id = kwargs['id']
    qs1 = Result.objects.filter(pk=result_id)
    for result in qs1:
        result.playing = not result.playing
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def wins_game(request, *args, **kwargs):
    #import pdb; pdb.set_trace()
    color = kwargs['color']
    result_id = kwargs['r_id']
    result = Result.objects.get(id=result_id)
    current = result.round
    result2 = Result.objects.get(participant=result.opponent,
                                 round=current)
    if color == 'B':
        result.win = '+'
        result2.win = '-'
    elif color == 'W':
        result.win = '-'
        result2.win = '+'
    else:
        result.win = '?'
        result2.win = '?'
    result.save()
    result2.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

@login_required
def add_game(request, *args, **kwargs):
    #import pdb; pdb.set_trace()
    current = kwargs['current']
    candidate = kwargs['p_id']
    p_candidate = Participant.objects.get(id=candidate)
    new_game = Result.objects.get(participant=p_candidate,
                                round=current)
    half_games = Result.objects.filter(participant__series=new_game.participant.series,
                                   round=current,
                                   color='?')
    if half_games:
        half_game = half_games[0]
        opponent = half_game.participant
        half_game.opponent = p_candidate
        new_game.opponent = opponent
        if opponent.mm_score < p_candidate.mm_score:
            p_black = opponent
            p_white = p_candidate
            half_game.color = 'B'
            new_game.color = 'W'
        else:
            p_black = p_candidate
            p_white = opponent
            half_game.color = 'W'
            new_game.color = 'B'
        handicap = get_handicap(p_black.mm_score, p_white.mm_score)
        new_game.handicap = handicap
        half_game.handicap = handicap
        new_game.win = '?'
        half_game.win = '?'
        new_game.save()
        half_game.save()
    else:
        new_game.color = '?'
        new_game.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

@login_required
def drop_pairing(request, *args, **kwargs):
    current = kwargs['current']
    results = Result.objects.filter(
        participant__series__seriesIsOpen=True
    ).filter(
        round=current
    )
    for result in results:
        result.opponent = None
        result.color = None
        result.win = None
        result.save()
        results2 = Result.objects.filter(
            opponent=result.participant
        ).filter(
            round=current
        )
        for result in results2: #will be 1 opponent result
            result.opponent = None
            result.color = None
            result.win = None
            result.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

