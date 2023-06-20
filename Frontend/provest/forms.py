from django import forms
from provest.models import *

class postcodeForm(forms.Form):
    postcode = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), max_length=9, label="Postcode:")
