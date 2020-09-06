""" gocra Django views """
# Create your views here.
#import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth import models as auth_models
from django.utils.decorators import method_decorator
from django.db.models import Exists, OuterRef
from django.shortcuts import render, reverse
from django.http import HttpResponseRedirect
from django.views.generic import ListView, TemplateView
from random import randrange
from .models import Club, Player, Series, Participant, Result
from .forms import UploadFileForm, AddParticipantForm
from .helpers import ExternalMacMahon, get_handicap
from .helpers import rank2rating, rating2rank
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
        series = Series.objects.get(seriesIsOpen=True)
        if series:
            round_results = Result.objects.filter(
                participant__series=series
            ).filter(
                round=current
            ).filter(
                color__in=['B', '?']
            ).order_by('participant__nr')
            context['round_results'] = round_results
            not_paired = get_not_paired(series, current)
            context['not_paired'] = not_paired
            context['club_admin'] = is_club_admin(self.request.user,
                                                  series.club)
            return context
        return None

def get_not_paired(series, round):
    ''' Return participants not paired for this round '''
    null_pairing = Result.objects.filter(
        participant=OuterRef('pk')
    ).filter(
        color=None
    ).filter(
        playing=True
    ).filter(
        round=round
    )
    not_paired = Participant.objects.filter(
        series=series
    ).filter(
        Exists(null_pairing)
    )
    return not_paired

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
        user = self.request.user
        context['series'] = [] #returns length 0 in template if none
        if user.is_authenticated:
            user_participant = Participant.objects.filter(
                series=OuterRef('pk')
            ).filter(player__account=user)
            series_l = Series.objects.filter(
                Exists(user_participant)
            ).filter(
                seriesIsOpen=True
            )
        else:
            series_l = Series.objects.filter(seriesIsOpen=True)
        if series_l:
            context['series'] = series_l
            series = series_l[0]
            current_round_number = series.currentRoundNumber
            # calculate the ratings:
            participants = Participant.objects.filter(series=series)
            self.calculate_rating(participants)
            self.rank_participants(participants, series)
            series_results = Result.objects.filter(
                participant__series=series
            ).order_by('participant__nr', 'round')
            context['series_results'] = series_results
            is_user_in_series = False
            is_user_playing = False
            is_user_paired = False
            for result in series_results:
                if result.round == current_round_number \
                and result.participant.player.account == user:
                    is_user_in_series = True
                    if result.playing:
                        is_user_playing = True
                    if result.opponent:
                        is_user_paired = True
            context['user_playing'] = is_user_playing
            context['user_paired'] = is_user_paired
            context['user_in_series'] = is_user_in_series
            # create round headings for rendering:
            rounds = []
            nrounds = series.numberOfRounds
            for n_round in range(nrounds):
                rounds.append({
                    'round': n_round+1,
                    'name': 'Ronde {:d}'.format(n_round+1)
                })
            context['rounds'] = rounds
            context['current'] = current_round_number
            context['club_admin'] = is_club_admin(user, series.club)
        return context

    def calculate_rating(self, participants):
        """
        Calculate rating gains for each result in the series
        """
        #import pdb; pdb.set_trace()
        for participant in participants:
            participant.resultrating = participant.rating
            participant.gain = 0.0
            participant.games = 0
            participant.wins = 0
            participant.score = 0.0 + participant.initial_mm
            participant.new_rank = ''
            results = Result.objects.filter(
                participant=participant).order_by('round')
            for result in results:
                result.gain = 0.0
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
            if participant.resultrating >= rank2rating(participant.rank) + 100:
                participant.new_rank = rating2rank(
                    rank2rating(participant.rank) + 100)
            if participant.resultrating < rank2rating(participant.rank) - 100:
                participant.new_rank = rating2rank(
                    rank2rating(participant.rank) - 100)
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

def is_club_admin(user, club):
    return (
        user in auth_models.User.objects.filter(
            admin_for=club
        )
    )

def del_participant(request, *args, **kwargs):
    series = Series.objects.get(pk=kwargs['sid'])
    participant = Participant.objects.get(pk=kwargs['pid'])
    if is_club_admin(request.user, series.club):
        Result.objects.filter(
            participant__series=series
        ).filter(
            participant=participant
        ).delete()
    participant.delete()
    return HttpResponseRedirect(reverse('gocra-series'))

def add_participant(request, *args, **kwargs):
    series = Series.objects.get(pk=kwargs['id'])
    if is_club_admin(request.user, series.club):
        if request.method == 'POST':
            form = AddParticipantForm(request.POST)
            if form.is_valid():
                participant = Participant()
                participant.series = series
                participant.rank = form.cleaned_data['rank']
                participant.rating = form.cleaned_data['rating']
                participant.player = form.cleaned_data['player']
                participant.save()
                for round in range(series.numberOfRounds):
                    result = Result()
                    result.series = series
                    result.participant = participant
                    result.round = round + 1
                    result.save()
                return HttpResponseRedirect(reverse('gocra-series'))
        else:
            form = AddParticipantForm()
            players = Player.objects.filter(
                ~Exists(Participant.objects.filter(
                    player=OuterRef('pk'),
                    series=series
                )),
                club=series.club,
            )
            form.fields['player'].queryset = players
        return render(request,
                      'wgocra/add_participant.html',
                      {'form':form, 'series':series})
    else:
        return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def upload_macmahon(request):
    """ Import macmahon file from local """
    club_l = Club.objects.filter(admin=request.user)
    if club_l:
        club = club_l[0]
        if request.method == 'POST':
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                macmahon = ExternalMacMahon()
                series_id = macmahon.xml_import(request.FILES['file'], club)
                request.session['series_qs'] = series_id
                return HttpResponseRedirect(reverse('gocra-series-list'))
        else:
            form = UploadFileForm()
        return render(request, 'wgocra/upload.html', {'form': form})
    return HttpResponseRedirect(reverse('gocra-series-list'))

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
def toggle_playing_user(request, *args, **kwargs):
    """ Toggle round result as playing for player """
    series_id = kwargs['sid']
    series = Series.objects.get(id=series_id)
    user = request.user
    qs1 = Result.objects.filter(
        participant__series__id=series_id
    ).filter(
        round=series.currentRoundNumber
    ).filter(
        participant__player__account=user
    )
    for result in qs1:
        result.playing = not result.playing
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

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
        if opponent.score < p_candidate.score:
            p_black = opponent
            p_white = p_candidate
            half_game.color = 'B'
            new_game.color = 'W'
        else:
            p_black = p_candidate
            p_white = opponent
            half_game.color = 'W'
            new_game.color = 'B'
        handicap = get_handicap(p_black.score, p_white.score)
        if handicap == 0:
            komi = 6.5
        else:
            komi = 0.5
        new_game.handicap = handicap
        new_game.komi = komi
        half_game.handicap = handicap
        half_game.komi = komi
        new_game.win = '?'
        half_game.win = '?'
        new_game.save()
        half_game.save()
    else:
        new_game.color = '?'
        new_game.handicap = 0
        new_game.komi = 0.0
        new_game.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

@login_required
def del_game(request, *args, **kwargs):
    result_id = kwargs['r_id']
    result = Result.objects.get(id=result_id)
    result2_l = Result.objects.filter(round=result.round,
                                 participant=result.opponent)
    result.opponent = None
    result.win = None
    result.color = None
    result.save()
    round = result.round
    if result2_l:
        result = result2_l[0]
        result.opponent = None
        result.win = None
        result.color = None
        result.save()
    return HttpResponseRedirect('/round/{:d}'.format(round))

@login_required
def make_pairing(request, *args, **kwargs):
    current = kwargs['current']
    series_l = Series.objects.filter(seriesIsOpen=True)
    if series_l:
        series = series_l[0]
        to_pair = get_not_paired(series, current)
        #import pdb; pdb.set_trace()
        paired = pair(to_pair, series, current)
        for game in paired['games']:
            if game[0].score < game[1].score:
                p_black = game[0]
                p_white = game[1]
            elif game[1].score < game[0].score:
                p_black = game[1]
                p_white = game[0]
            elif game[1].score == game[0].score:
                random = randrange(1)
                if random == 1:
                    p_black = game[0]
                    p_white = game[1]
                else:
                    p_black = game[1]
                    p_white = game[0]
            res_b = Result.objects.get(
                participant=p_black,
                round=current)
            res_w = Result.objects.get(
                participant=p_white,
                round=current)
            handicap = get_handicap(p_black.score,  p_white.score)
            if handicap == 0:
                komi = 6.5
            else:
                komi = 0.5
            res_b.color = 'B'
            res_b.opponent = p_white
            res_b.win = '?'
            res_b.handicap = handicap
            res_b.komi = komi
            res_b.save()
            res_w.color = 'W'
            res_w.opponent = p_black
            res_w.win = '?'
            res_w.handicap = handicap
            res_w.komi = komi
            res_w.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

def pair(to_pair, series, round):
    paired = {}
    tries = []
    player1 = to_pair[0]
    for player2 in to_pair[1:]:
        score = get_score(player1, player2, series, round)
        tries.append({'score':score, 'p1':player1, 'p2':player2})
    tries.sort(key=lambda t: t['score'])
    if len(to_pair) < 4:
        paired['score'] = tries[0]['score']
        paired['games'] = []
        paired['games'].append((tries[0]['p1'], tries[0]['p2']))
    else:
        cur_score = 1E8
        paired['score'] = cur_score
        paired['games'] = []
        for game in tries:
            if game['score'] < cur_score:
                sub_to_pair = [
                    p for p in to_pair \
                    if p != game['p1'] and p != game['p2']
                ]
                sub_paired = pair(sub_to_pair, series, round)
                new_score = game['score'] + sub_paired['score']
                if new_score < cur_score:
                    cur_score = new_score
                    paired['score'] = new_score
                    paired['games'].append((game['p1'], game['p2']))
                    paired['games'].extend(sub_paired['games'])
    return paired

def get_score(player1, player2, series, round):
    encounters = Result.objects.filter(
        participant__series=series,
        round__lt=round,
        participant=player1,
        opponent=player2,
    ).count() + Result.objects.filter(
        participant__series=series,
        round__lt=round,
        participant=player2,
        opponent=player1,
    ).count()
    score = encounters * 1E6
    score_diff = abs(player1.score - player2.score)
    score += score_diff * 1E4
    return score

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

