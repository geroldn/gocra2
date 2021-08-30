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
from random import randrange, seed
#from random import randrange, seed
from .models import Club, Player, Series, Participant, Result, Rating
from .forms import UploadFileForm, AddParticipantForm, \
        EditParticipantForm, NewSeriesForm
from .helpers import ExternalMacMahon, get_handicap
from .helpers import rank2rating, rating2rank
from .ratingsystem import RatingSystem as Rsys

#logging.basicConfig(filename='log/gocra.log', level=logging.DEBUG)


def index(request):
    """ Render the gocra index page """
    return render(request, 'wgocra/index.html')

class RoundDetailView(TemplateView):
    """
    Render Round as Result Details
    """
    template_name = 'wgocra/round.html'

    def get_context_data(self, **kwargs):
        current = self.kwargs['current']
        context = super().get_context_data(**kwargs)
        user = self.request.user
        cplayer = Player.objects.get(account=user)
        cclub = cplayer.get_last_club()
        series = Series.objects.get(seriesIsOpen=True, club=cclub)
        context['series'] = series
        if series:
            results = Result.objects.filter(
                participant__series=series
            ).filter(round=current)
            round_results = results.filter(
                color__in=['B', '?']
            ).order_by('participant__nr')
            context['round_results'] = round_results
            not_paired = get_not_paired(series, current)
            context['not_paired'] = not_paired
            context['club_admin'] = is_club_admin(self.request.user,
                                                  series.club)
            #import pdb; pdb.set_trace()
            add_user_playing_status(context, results, current, user)
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
    ).order_by(
        '-score'
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
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['series'] = [] #returns length 0 in template if none
        #import pdb; pdb.set_trace()
        if user.is_authenticated:
            try:
                player = Player.objects.get(
                    account=user
                )
            except Player.DoesNotExist:
                player = None
            if player:
                club = player.get_last_club()
                series_l = Series.objects.filter(
                    club=club
                ).filter(
                    seriesIsOpen=True
                )
        else:
            series_l = Series.objects.filter(
                seriesIsOpen=True,
                club=1,
            )
        if series_l:
            context['series'] = series_l
            series = series_l[0]
            current_round_number = series.currentRoundNumber
            # calculate the ratings:
            participants = Participant.objects.filter(series=series)
            self.calculate_rating(participants)
            for participant in participants:
                if Result.objects.filter(
                    participant=participant,
                    playing=True):
                    participant.playing = True
                else:
                    participant.playing = False
                participant.save()
            playing_dict = {}
            for participant in participants:
                playing_dict['{:d}'.format(participant.id)] = \
                Result.objects.get(participant=participant,
                                   round=current_round_number,
                                   game=1
                                  ).playing
            self.rank_participants(participants, playing_dict, series)
            series_results = Result.objects.filter(
                participant__series=series
            ).order_by('participant__nr', 'round', 'game')
            context['series_results'] = series_results
            #import pdb; pdb.set_trace()
            add_user_playing_status(context,
                                    series_results,
                                    current_round_number,
                                    user)
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

    def rank_participants(self, participants, playing, series):
        """
        Rank participants according to their results.
        """
        for p_enum in enumerate(
                sorted(
                    participants,
                    key=lambda ptnt: ((ptnt.games > 0),
                                      ptnt.wins, ptnt.gain,
                                      playing['{:d}'.format(ptnt.id)],
                                      ptnt.rating),
                    reverse=True
                ),
                1 #start rank value
            ):
            participant = participants.get(id=p_enum[1].id)
            participant.nr = p_enum[0]
            participant.save()
        results = Result.objects.filter(participant__series=series)

def add_user_playing_status(context, results, current, user):
    is_user_in_series = False
    is_user_playing = False
    is_user_paired = False
    for result in results:
        if result.round == current \
        and result.participant.player \
        and result.participant.player.account == user:
            is_user_in_series = True
            if result.playing:
                is_user_playing = True
            if result.opponent:
                is_user_paired = True
    context['user_playing'] = is_user_playing
    context['user_paired'] = is_user_paired
    context['user_in_series'] = is_user_in_series

@method_decorator(login_required, name='dispatch')
class SeriesListView(TemplateView):
    """
    Renders a list of Gocra Series.
    """
    model = Series
    template_name = 'wgocra/series_all.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            player = Player.objects.get(account=self.request.user)
        except Player.DoesNotExist:
            player = None
        if player:
            club = player.get_last_club()
            context['club_admin'] = is_club_admin(self.request.user,
                                                  club)
        else:
            club = None
        series_l = Series.objects.filter(
            club=club
        ).order_by('-name', '-version')
        context['series'] = series_l
        return context

@method_decorator(login_required, name='dispatch')
class ClubListView(ListView):
    """ Render list of clubs """
    model = Club
    template_name = 'wgocra/club_list.html'

    def get_queryset(self):
        user = self.request.user
        try:
            player = Player.objects.get(account=user)
        except Player.DoesNotExist:
            player = None
        if player:
            club_l = player.club.all()
        else:
            club_l = []
        return club_l


@method_decorator(login_required, name='dispatch')
class PlayerListView(ListView):
    """ Render list of players """
    model = Player
    template_name = 'wgocra/player_list.html'
    def get_queryset(self):
        user = self.request.user
        try:
            player = Player.objects.get(account=user)
        except Player.DoesNotExist:
            player = None
        if player:
            club = player.get_last_club()
        else:
            return None
        player_l = Player.objects.filter(
            club=club
        )
        return player_l


def is_club_admin(user, club):
    return (
        user in auth_models.User.objects.filter(
            admin_for=club
        )
    )

@login_required
def club_select(request, *args, **kwargs):
    """ Select club as last accessed by this user """
    club = Club.objects.get(pk=kwargs['id'])
    user = request.user
    try:
        player = Player.objects.get(
            account=user
        )
        player.last_club = club
        player.save()
    except Player.DoesNotExist:
        player = None
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def user_result(request, *args,**kwargs):
    series = Series.objects.get(pk=kwargs['sid'])
    current = kwargs['round']
    win = kwargs['win']
    user = request.user
    result = Result.objects.get(
        participant__series = series,
        participant__player__account=user,
        round=current
    )
    result2 = Result.objects.get(
        participant__series=series,
        opponent__player__account=user,
        round=current
    )
    if win:
        result.win = '+'
        result2.win  = '-'
    else:
        result.win = '-'
        result2.win  = '+'
    result.save()
    result2.save()
    return HttpResponseRedirect('/round/{:d}'.format(current))

@login_required
def add_round(request, *args, **kwargs):
    series = Series.objects.get(pk=kwargs['sid'])
    round = series.numberOfRounds + 1
    series.numberOfRounds = round
    series.save()
    participants = Participant.objects.filter(
        series=series
    )
    for participant in participants:
        result = Result()
        result.series = series
        result.participant = participant
        result.round = round
        result.game = 1
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def rem_round(request, *args, **kwargs):
    series = Series.objects.get(pk=kwargs['sid'])
    participants = Participant.objects.filter(
        series=series
    )
    for participant in participants:
        Result.objects.filter(
            participant=participant,
            round__gte=series.numberOfRounds,
        ).delete()
    series.numberOfRounds = series.numberOfRounds - 1
    series.save()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def del_participant(request, *args, **kwargs):
    participant = Participant.objects.get(pk=kwargs['pid'])
    series = participant.series
    if is_club_admin(request.user, series.club):
        Result.objects.filter(
    #        participant__series=series
    #    ).filter(
            participant=participant
        ).delete()
    participant.delete()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def add_participant(request, *args, **kwargs):
    series = Series.objects.get(pk=kwargs['id'])
    if is_club_admin(request.user, series.club):
        if request.method == 'POST':
            form = AddParticipantForm(request.POST)
            if form.is_valid():
                participant = Participant()
                participant.series = series
                participant.player = form.cleaned_data['player']
                rating = participant.player.get_last_rating(series)
                participant.rating = 100
                participant.rank = '20k'
                if rating:
                    if rating.rating:
                        participant.rating = rating.rating
                    if rating.old_rating:
                        participant.rating = rating.old_rating
                    if rating.rank:
                        participant.rank = rating.rank
                    if rating.old_rank:
                        participant.rank = rating.old_rank
                participant.save()
                for round in range(series.numberOfRounds):
                    result = Result()
                    result.series = series
                    result.participant = participant
                    result.round = round + 1
                    result.game = 1
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
def edit_participant(request, *args, **kwargs):
    participant = Participant.objects.get(pk=kwargs['pid'])
    series = participant.series
    if is_club_admin(request.user, series.club):
        if request.method == 'POST':
            form = EditParticipantForm(request.POST, instance=participant)
            if form.is_valid():
                participant.rank = form.cleaned_data['rank']
                participant.rating = form.cleaned_data['rating']
                participant.save()
                return HttpResponseRedirect(reverse('gocra-series'))
        else:
            form = EditParticipantForm(instance=participant)
        return render(request,
                      'wgocra/edit_participant.html',
                      {
                          'form':form,
                          'participant':participant,
                      })
    else:
        return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def new_series(request):
    """ Create new series from scratch """
    #import pdb; pdb.set_trace()
    user = request.user
    player = Player.objects.get(account=user)
    club = player.get_last_club()
    if player and club and is_club_admin(user, club):
        if request.method == 'POST':
            form = NewSeriesForm(request.POST)
            if form.is_valid():
                series = Series()
                series.club = club
                series.name = form.cleaned_data['name']
                series.numberOfRounds = 6
                series.currentRoundNumber = 1
                series.lastOpponents = 4
                series.seriesIsOpen = False
                series.takeCurrentRoundInAccount = True
                series.version = 1
                series.save()
                return HttpResponseRedirect(reverse('gocra-series-list'))
        else:
            form = NewSeriesForm()
        return render(request,
                      'wgocra/new_series.html',
                      {'form':form})
    else:
        return HttpResponseRedirect(reverse('gocra-series-list'))

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
    user = request.user
    player = Player.objects.get(account=user)
    club = player.get_last_club()
    qs1 = Series.objects.filter(seriesIsOpen=True, club=club)
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
    user = request.user
    player = Player.objects.get(account=user)
    club = player.get_last_club()
    series_id = kwargs['id']
    qs1 = Series.objects.filter(seriesIsOpen=True, club=club)
    for series in qs1:
        series.seriesIsOpen = False
        series.save()
    qs2 = Series.objects.filter(pk=series_id)
    for series in qs2:
        series.seriesIsOpen = True
        series.save()
    return HttpResponseRedirect(reverse('gocra-series-list'))

@login_required
def series_finalize(request, *args, **kwargs):
    """ Save result ratings for players and close series """
    series_id = kwargs['id']
    series = Series.objects.get(pk=series_id)
    participant_l = Participant.objects.filter(
        series=series
    )
    for participant in participant_l:
        try:
            rating = Rating.objects.get(
                series=series,
                player=participant.player
            )
        except Rating.DoesNotExist:
            rating = Rating()
            rating.series = series
            rating.player = participant.player
        rating.old_rank = participant.rank
        rating.rank = participant.new_rank
        rating.old_rating = participant.rating
        rating.rating =  participant.resultrating
        rating.save()
    return HttpResponseRedirect(reverse('gocra-series-list'))

@login_required
def set_playing_user(request, *args, **kwargs):
    """ Toggle round result as playing for player """
    series_id = kwargs['sid']
    playing = ( kwargs['playing'] == 1 )
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
        result.playing = playing
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def result_set_playing(request, *args, **kwargs):
    """ Toggle round result as playing for player """
    result_id = kwargs['id']
    playing = ( kwargs['playing'] == 1 )
    qs1 = Result.objects.filter(pk=result_id)
    for result in qs1:
        result.playing = playing
        result.save()
    return HttpResponseRedirect(reverse('gocra-series'))

@login_required
def wins_game(request, *args, **kwargs):
    #import pdb; pdb.set_trace()
    color = kwargs['color']
    result_id = kwargs['r_id']
    result = Result.objects.get(id=result_id)
    current = result.round
    result2 = result.opponent_result
    if result2 == None:
        result2 = Result.objects.get(participant=result.opponent,
                                 round=current)
        result.opponent_result = result2
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
    igame = kwargs['game']
    p_candidate = Participant.objects.get(id=candidate)
    if igame == 1:
        new_game = Result.objects.get(participant=p_candidate,
                                round=current)
    if igame == 2:
        simul_l = Result.objects.filter(participant=p_candidate,
                                   round=current,
                                   game=2)
        if simul_l:
            return HttpResponseRedirect('/round/{:d}'.format(current))
        else:
            new_game = Result()
            new_game.series = p_candidate.series
            new_game.participant = p_candidate
            new_game.round = current
            new_game.game = 2
            new_game.save()
    half_games = Result.objects.filter(participant__series=new_game.participant.series,
                                   round=current,
                                   color='?')
    if half_games:
        half_game = half_games[0]
        opponent = half_game.participant
        half_game.opponent = p_candidate
        new_game.opponent = opponent
        half_game.opponent_result = new_game
        new_game.opponent_result = half_game
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
    round = result.round
    if result.game == 1:
        result.opponent = None
        result.win = None
        result.color = None
        result.save()
    if result.opponent_result:
        result2 = result.opponent_result
        has_opponent = True
    else:
        if result2_l:
            result2 = result2_l[0]
            has_opponent = True
        else:
            has_opponent = False
    if result.game == 2:
        result.delete()
    if has_opponent:
        if result2.game == 1:
            result2.opponent = None
            result2.win = None
            result2.color = None
            result2.save()
        if result2.game == 2:
            result2.delete()
    return HttpResponseRedirect('/round/{:d}'.format(round))

@login_required
def make_pairing(request, *args, **kwargs):
    seed()
    current = kwargs['current']
    cuser = request.user
    cplayer = Player.objects.get(account=cuser)
    cclub = cplayer.get_last_club()
    series_l = Series.objects.filter(seriesIsOpen=True, club=cclub)
    if series_l:
        series = series_l[0]
        to_pair = get_not_paired(series, current)
        if len(to_pair) < 2:
            return HttpResponseRedirect('/round/{:d}'.format(current))
        to_pair_sm = []
        #import pdb; pdb.set_trace()
        for player in to_pair:
            player_sm = {}
            player_sm['id'] = player.id
            player_sm['player_id'] = player.player_id
            player_sm['score'] = player.score
            #opponents in this series
            player_sm['ops'] = []
            result_l = Result.objects.filter(participant=player)
            for result in result_l:
                if result.opponent:
                    player_sm['ops'].append(result.opponent.id)
            #recently played opponents over all series
            recents = series.lastOpponents
            playerPlayer = Player.objects.filter(id=player.player_id)[0]
            player_sm['recentOps'] = []
            result_l2 = Result.objects.filter(
                participant__player=playerPlayer
            ).filter(
                opponent__isnull=False
            ).order_by('-participant__series__startDate', '-round')[:recents]
            for result in result_l2:
                player_sm['recentOps'].append(result.opponent.player_id)
            to_pair_sm.append(player_sm)
        games = pair_long(to_pair_sm, series, current)
        for game in games:
            if game[0]['score'] < game[1]['score']:
                p_black = Participant.objects.get(id=game[0]['id'])
                p_white = Participant.objects.get(id=game[1]['id'])
            elif game[1]['score'] < game[0]['score']:
                p_black = Participant.objects.get(id=game[1]['id'])
                p_white = Participant.objects.get(id=game[0]['id'])
            elif game[1]['score'] == game[0]['score']:
                random = randrange(1)
                if random == 1:
                    p_black = Participant.objects.get(id=game[0]['id'])
                    p_white = Participant.objects.get(id=game[1]['id'])
                else:
                    p_black = Participant.objects.get(id=game[1]['id'])
                    p_white = Participant.objects.get(id=game[0]['id'])
            res_b = Result.objects.get(
                participant=p_black,
                round=current,
                game=1)
            res_w = Result.objects.get(
                participant=p_white,
                round=current,
                game=1)
            res_w.opponent_result = res_b
            res_b.opponent_result = res_w
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

def pair_long(to_pair, series, round):
    games = []
    while len(to_pair) > 11:
        paired = pair(to_pair[0:10], series, round)
        games2add = paired['games'][0:4]
        games.extend(games2add)
        for game in games2add:
            to_pair.remove(game[0])
            to_pair.remove(game[1])
    paired = pair(to_pair, series, round)
    games.extend(paired['games'])
    return games

def pair(to_pair, series, round):
    #import pdb; pdb.set_trace()
    paired = {}
    tries = []
    player1 = to_pair[0]
    for player2 in to_pair[1:]:
        p_score = get_score(player1, player2, series, round)
        tries.append({'p_score':p_score, 'p1':player1, 'p2':player2})
    tries.sort(key=lambda t: t['p_score'])
    if len(to_pair) < 4:
        paired['p_score'] = tries[0]['p_score']
        paired['games'] = []
        paired['games'].append((tries[0]['p1'], tries[0]['p2']))
    else:
        cur_score = 1E8
        paired['p_score'] = cur_score
        for game in tries:
            sub_to_pair = [
                p for p in to_pair \
                if p != game['p1'] and p != game['p2']
            ]
            sub_paired = pair(sub_to_pair, series, round)
            new_score = game['p_score'] + sub_paired['p_score']
            if new_score < cur_score:
                cur_score = new_score
                paired['p_score'] = cur_score
                paired['games'] = []
                paired['games'].append((game['p1'], game['p2']))
                paired['games'].extend(sub_paired['games'])
    return paired

def get_score(player1, player2, series, round):
    #import pdb; pdb.set_trace()
    encountered = player2['id'] in player1['ops']
    recent = player2['player_id'] in player1['recentOps']
    score = (encountered + recent) * 1E6
    score_diff = abs(player1['score'] - player2['score'])
    score += ((score_diff // series.diffCutoff) ** 2) * 1E3 + randrange(100)
    return score

@login_required
def drop_pairing(request, *args, **kwargs):
    current = kwargs['current']
    cuser = request.user
    cplayer = Player.objects.get(account=cuser)
    cclub = cplayer.get_last_club()
    results = Result.objects.filter(
        participant__series__seriesIsOpen=True,
        participant__series__club=cclub
    ).filter(
        round=current
    ).filter(
        game=2
    )
    for result in results:
        result.delete()
    results = Result.objects.filter(
        participant__series__seriesIsOpen=True,
        participant__series__club=cclub
    ).filter(
        round=current
    )
    for result in results:
        if result.game == 2:
            result.delete()
        else:
            result.opponent = None
            result.color = None
            result.win = None
            result.save()
        """
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
        """
    return HttpResponseRedirect('/round/{:d}'.format(current))

