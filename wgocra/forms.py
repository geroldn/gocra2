""" Helper classes """
from django import forms
from .models import Participant

class UploadFileForm(forms.Form):
    """ Form to get a file to upload """
    file = forms.FileField()

class AddParticipantForm(forms.ModelForm):
    """ Form to get a new participant for a series """
    class Meta:
        model = Participant
        fields = [
            'player',
            'rank',
            'rating',
        ]
