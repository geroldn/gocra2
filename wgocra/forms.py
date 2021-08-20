""" Helper classes """
from django import forms
from .models import Participant, Series

class NewSeriesForm(forms.ModelForm):
    """ Form to create a new series """
    class Meta:
        model = Series
        fields = [
            'name',
        ]

class UploadFileForm(forms.Form):
    """ Form to get a file to upload """
    file = forms.FileField()

class AddParticipantForm(forms.ModelForm):
    """ Form to get a new participant for a series """
    class Meta:
        model = Participant
        fields = [
            'player',
        ]

class EditParticipantForm(forms.ModelForm):
    """ Form to get edit participant info """
    class Meta:
        model = Participant
        fields = [
            'rank',
            'rating',
        ]
