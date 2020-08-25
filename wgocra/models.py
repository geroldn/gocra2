""" wgocra Django models """
# Create your models here.
from django.db import models
from django.contrib.auth import models as auth_models
from gocra.gocra import Rank


class Club(models.Model):
    """ Club in the system """
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Player(models.Model):
    """ Player in the system """
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    egd_pin = models.CharField(max_length=10, null=True)
    reg_date = models.DateTimeField('date registered')
    club = models.ForeignKey(Club, blank=True, null=True, on_delete=models.SET_NULL)
    account = models.ForeignKey(auth_models.User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Series(models.Model):
    """ Series; Has participants and results """
    name = models.CharField(max_length=200)
    numberOfRounds = models.IntegerField()
    currentRoundNumber = models.IntegerField()
    takeCurrentRoundInAccount = models.BooleanField()
    seriesIsOpen = models.BooleanField()
    version = models.IntegerField()

class Participant(models.Model):
    """ Participant in a Series """
    rank = models.CharField(max_length=10)
    rating = models.IntegerField()
    mm_id = models.IntegerField()
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

    @property
    def mm_score(self):
        #import pdb; pdb.set_trace()
        rank = Rank(self.rank)
        round_rating = rank.round_rating()
        mm_start = 14.0 + round_rating/100
        return mm_start + self.wins

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
    win = models.CharField(max_length=4, null=True)
    gain = models.FloatField(null=True, default=0.0)
    r_string = models.CharField(max_length=10, null=True, default='')
