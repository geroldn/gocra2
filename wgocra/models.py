""" wgocra Django models """
# Create your models here.
from django.db import models
from django.contrib.auth import models as auth_models
from gocra.gocra import Rank


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
    club = models.ManyToManyField(Club, blank=True)
    account = models.ForeignKey(auth_models.User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Series(models.Model):
    """ Series; Has participants and results """
    name = models.CharField(max_length=200)
    club = models.ForeignKey(Club, blank=True, null=True,
                             on_delete=models.SET_NULL)
    numberOfRounds = models.IntegerField()
    currentRoundNumber = models.IntegerField()
    takeCurrentRoundInAccount = models.BooleanField()
    diffCutoff = models.IntegerField(default=1)
    seriesIsOpen = models.BooleanField()
    version = models.IntegerField()

    def __str__(self):
        return self.name + ' (' + '{}'.format(self.version) + ')'

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
    round = models.IntegerField()
    playing = models.BooleanField(default=False)
    color = models.CharField(max_length=5, null=True)
    handicap = models.IntegerField(null=True)
    komi = models.FloatField(null=True, default=0.0)
    win = models.CharField(max_length=4, null=True)
    gain = models.FloatField(null=True, default=0.0)
    #r_string = models.CharField(max_length=10, null=True, default='')

    def __str__(self):
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
