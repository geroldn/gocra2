""" wgocra Django models """
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import models as auth_models
from gocra.gocra import Rank
from django.utils import timezone


class Club(models.Model):
    """ Club in the system """
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)
    admin = models.ManyToManyField(
        auth_models.User, blank=True, related_name='admin_for')

    def __str__(self):
        return self.name

class Player(models.Model):
    """ Player in the system """
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    egd_pin = models.CharField(max_length=10, blank=True, null=True)
    reg_date = models.DateTimeField('date registered')
    club = models.ManyToManyField(Club, blank=True, related_name='players')
    last_club = models.ForeignKey(Club, blank=True, null=True,
                             on_delete=models.SET_NULL)
    account = models.ForeignKey(auth_models.User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        account = self.account
        if account:

            s1 = self.account.username.ljust(20, '.')
            s2 = (self.first_name + " " + self.last_name).ljust(30, '.')
            s3 = self.account.email
            return s1 + s2 + s3
        else:
            return '---- ' \
                + self.first_name + ' ' + self.last_name + ' ' \
                + '----'


    def get_last_club(self):
        club = self.last_club
        if not club:
            club_l = Club.objects.filter(
                players=self
            )
            if club_l:
                club = club_l[0]
                self.last_club = club
                self.save()
        return club

    def get_last_rating(self, series):
        rating = Rating.objects.filter(
            player=self,
            series__startDate__lte=series.startDate
        ).order_by('-series__startDate').first()
        if rating:
            return rating
        else:
            return None

    def createUserName(self):
        n = 1
        username = self.first_name + self.last_name[:n]
        while User.objects.filter(username=username):
            n += 1 
            username = self.first_name + self.last_name[:n]
        return username

class Series(models.Model):
    """ Series; Has participants and results """
    name = models.CharField(max_length=200)
    club = models.ForeignKey(Club, blank=True, null=True,
                             on_delete=models.SET_NULL)
    numberOfRounds = models.IntegerField()
    currentRoundNumber = models.IntegerField()
    takeCurrentRoundInAccount = models.BooleanField()
    diffCutoff = models.IntegerField(default=1)
    lastOpponents = models.IntegerField(default=1)
    seriesIsOpen = models.BooleanField()
    version = models.IntegerField()
    startDate = models.DateField(default=timezone.now)

    def __str__(self):
        return self.name + ' (' + '{}'.format(self.version) + ')'

class Rating(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    series = models.ForeignKey(Series, blank=True, null=True,
                               on_delete=models.SET_NULL)
    rank = models.CharField(max_length=10, null=True)
    old_rank = models.CharField(max_length=10, null=True)
    rating = models.IntegerField(null=True)
    old_rating = models.IntegerField(null=True)

    def __str__(self):
        return (
            f'{self.player.first_name} {self.player.last_name}'
            f'({self.series.name})'
            f': {self.rating}({self.rank})'
            f' ({self.old_rating}({self.old_rank}))'
        )

class Participant(models.Model):
    """ Participant in a Series """
    rank = models.CharField(max_length=10)
    rating = models.IntegerField()
    mm_id = models.IntegerField(null=True)
    series = models.ForeignKey(Series, blank=True, null=True, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, blank=True, null=True, on_delete=models.CASCADE)
    nr = models.IntegerField(default=0)
    resultrating = models.IntegerField(default=0)
    gain = models.IntegerField(null=True, default=0)
    games = models.IntegerField(null=True, default=0)
    wins = models.IntegerField(null=True, default=0)
    score = models.FloatField(null=True, default=0)
    points_str = models.CharField(max_length=10, default='')
    new_rank = models.CharField(max_length=10, default='')
    playing = models.BooleanField(default=False)

    def __str__(self):
        return '{:s} {:s} {:s} {:.0f}'.format(
            self.player.first_name,
            self.player.last_name,
            self.rank,
            self.rating
        )

    @property
    def initial_mm(self):
        #import pdb; pdb.set_trace()
        rank = Rank(self.rank)
        round_rating = rank.round_rating()
        return 14.0 + round_rating/100

    def setNr(self, nr):
        self.nr = nr

class Result(models.Model):
    """ Result for a Participant """
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE,
        related_name='results')
    opponent = models.ForeignKey(
        Participant, null=True, blank=True, on_delete=models.CASCADE,
        related_name='opp_results')
    opponent_result = models.ForeignKey(
        "Result", null=True, blank=True, on_delete=models.SET_NULL,
        related_name='participant_result')
    round = models.IntegerField()
    game = models.IntegerField(default=1)
    playing = models.BooleanField(default=False)
    color = models.CharField(max_length=5, null=True)
    handicap = models.IntegerField(null=True)
    komi = models.FloatField(null=True, default=0.0)
    win = models.CharField(max_length=4, null=True)
    gain = models.FloatField(null=True, default=0.0)
    #r_string = models.CharField(max_length=10, null=True, default='')

    def __str__(self):
        participant = self.participant
        if participant == None:
            return '{:d}'.format(self.id)
        series = participant.series
        if series == None:
            return '{:d}'.format(self.id)
        return '{:s}({:d}) {:s} {:s}'.format(
            self.participant.series.name,
            self.round,
            self.participant.player.first_name,
            self.participant.player.last_name,
        )

    @property
    def r_string(self):
        r_string = ''
        if self.color in ('B', 'W') and self.win in ('+', '-', '?'):
            r_string = '{:d}{:s}/{:s}{:d}'.format(
                self.opponent.nr,
                self.win,
                self.color,
                self.handicap)
        return r_string

    @property
    def pr_string(self):
        pr_string = ''
        if self.color in ('B', 'W') and self.win in ('+', '-', '?'):
            if self.win == '?':
                pr_string = '?-?'
            elif self.win == '+':
                pr_string = '1-0'
            elif self.win == '-':
                pr_string = '0-1'
            else:
                pr_string = ''
        return pr_string
