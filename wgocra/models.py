# Create your models here.
from django.db import models


class Club(models.Model):
    name = models.CharField(max_length=200)
    city = models.CharField(max_length=200)

class Player(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    egd_pin = models.CharField(max_length=10)
    reg_date = models.DateTimeField('date registered')
    club = models.ForeignKey(Club, null=True, on_delete=models.SET_NULL)
