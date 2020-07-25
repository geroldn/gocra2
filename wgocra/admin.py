# Register your models here.
from django.contrib import admin

from .models import Club
from .models import Player

admin.site.register(Club)
admin.site.register(Player)
