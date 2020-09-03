# Register your models here.
from django.contrib import admin

from .models import Club
from .models import Player
from .models import Series

admin.site.register(Series)
admin.site.register(Club)
admin.site.register(Player)
