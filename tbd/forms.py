import re
from django import forms

class AddProjectForm(forms.Form):
    name = forms.SlugField()
    owner = forms.RegexField(regex=re.compile(r'\w{1,20}'), strip=True)