import re
from django import forms

class AddProjectForm(forms.Form):
    name  = forms.RegexField(regex=re.compile(r'^[a-zA-Z]\w{0,39}$'), strip=True)
    owner = forms.RegexField(regex=re.compile(r'^\w{1,20}$'), strip=True)