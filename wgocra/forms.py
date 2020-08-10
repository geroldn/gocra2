""" Helper classes """
from django import forms

class UploadFileForm(forms.Form):
    """ Form to get a file to upload """
    file = forms.FileField()
