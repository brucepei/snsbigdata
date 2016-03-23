import re
from django import forms

class AddProjectForm(forms.Form):
    project_name = forms.RegexField(
        regex=re.compile(r'^[a-zA-Z]\w{0,39}$'),
        strip=True,
        label='Project Name',
        max_length=40,
    )
    project_owner = forms.RegexField(
        regex=re.compile(r'^\w{1,20}$'),
        strip=True,
        label='Owner name',
        max_length=20,
    )