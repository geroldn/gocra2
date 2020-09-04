# Register your models here.
from django.contrib import admin

from .models import Club
from .models import Player
from .models import Participant
from .models import Series
from .models import Result

admin.site.register(Series)
admin.site.register(Club)
admin.site.register(Player)
admin.site.register(Participant)
admin.site.register(Result)
