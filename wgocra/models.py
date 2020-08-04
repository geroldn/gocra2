# Create your models here.
from django.db import models
from django.contrib.auth import models as auth_models
from gocra.gocra import Rank


class Club(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)

    def __str__(self):
        return self.name

class Player(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    egd_pin = models.CharField(max_length=10)
    reg_date = models.DateTimeField('date registered')
    club = models.ForeignKey(Club, blank=True, null=True, on_delete=models.SET_NULL)
    account = models.ForeignKey(auth_models.User, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Series(models.Model):
    name = models.CharField(max_length=200)
    numberOfRounds = models.IntegerField()
    currentRoundNumber = models.IntegerField()
    TakeCurrentRoundInAccount = models.BooleanField()
    SeriesIsOpen = models.BooleanField()

    def reg_import(self, macmahon):
        self.name = macmahon.doc['Tournament']['Name']
        self.numberOfRounds = int(macmahon.doc['Tournament']['NumberOfRounds'])
        self.currentRoundNumber = int(macmahon.doc['Tournament']['CurrentRoundNumber'])
        self.takeCurrentRoundInAccount = macmahon.doc['Tournament']['TakeCurrentRoundInAccount']

class Participant(models.Model):
    name = models.CharField(max_length=200)
    rank = models.CharField(max_length=10)
    rating = models.IntegerField()
    mm_id = models.IntegerField()
    series = models.ForeignKey(Series, blank=True, null=True, on_delete=models.CASCADE)

    def __init__(self, name, rank, rating, _id, series):
        self.name = name
        self.rank = Rank(rank)
        self.newRank = Rank(rank)
        if rating == 0:
            rating = self.rank.round_rating()
        self.rating = rating
        self.mmid = _id
        self.nr = 0
        self.startRating = rating
        self.resultRating = rating
        self.series = series.id

    def setNr(self, nr):
        self.nr = nr


class Result(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE,
        related_name='results')
    opponent = models.ForeignKey(Participant, on_delete=models.CASCADE,
        related_name='opp_results')
    round = models.IntegerField()
    color = models.CharField(max_length=5)
    handicap = models.IntegerField()
    win = models.CharField(max_length=4)
