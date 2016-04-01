import re
from django import forms
from .models import Crash

class AddProjectForm(forms.Form):
    project_name = forms.RegexField(
        regex=re.compile(r'^[a-zA-Z][\w.-]{0,39}$'),
        strip=True,
        label='Project Name',
        max_length=40,
        error_messages={
            'invalid': "Maximum length 40, and starts with letter, only includes '.', '-', letter and digit!"
        }
    )
    project_owner = forms.RegexField(
        regex=re.compile(r'^\w{1,20}$'),
        strip=True,
        label='Owner name',
        max_length=20,
        error_messages={
            'invalid': 'Maximum length 20, only includes letter and digits!'
        }
    )

class AddBuildForm(forms.Form):
    build_project_name = forms.CharField(
        widget=forms.HiddenInput,
        error_messages={
            'required': 'Please choose a Project!'
        }
    )
    build_version = forms.RegexField(
        regex=re.compile(r'^[a-zA-Z][\w.-]{0,39}$'),
        strip=True,
        label='Version',
        max_length=40,
        error_messages={
            'invalid': "Maximum length 40, and starts with letter, only includes '.', '-', letter and digit!"
        }
    )
    build_name = forms.RegexField(
        regex=re.compile(r'^\w{1,20}$'),
        strip=True,
        label='Short Name',
        max_length=20,
        error_messages={
            'invalid': 'Maximum length 20, only includes letter and digits!'
        }
    )
    build_server_path = forms.RegexField(
        regex=re.compile(r'^\\\\.+'),
        label='Server Installer Path',
        max_length=255,
        error_messages={
            'invalid': "Maximum length 255, should start with '\\\\'!"
        },
        widget=forms.TextInput(
            attrs={'class':'path_input'}
        )
    )
    build_crash_path = forms.RegexField(
        regex=re.compile(r'^\\\\.+'),
        label='Crash Path',
        max_length=255,
        error_messages={
            'invalid': "Maximum length 255, should start with '\\\\'!"
        },
        widget=forms.TextInput(
            attrs={'class':'path_input'}
        )
    )
    build_local_path = forms.RegexField(
        regex=re.compile(r'^\\\\.+'),
        label='Local Installer Path',
        max_length=255,
        required=False,
        error_messages={
            'invalid': "Maximum length 255, should start with '\\\\'!"
        },
        widget=forms.TextInput(
            attrs={'class':'path_input'}
        )
    )
    build_use_server = forms.BooleanField(
        label='Use Server Installer',
        required=False,
    )
    
class AddCrashForm(forms.Form):
    crash_path = forms.RegexField(
        regex=re.compile(r'^\\\\.+'),
        label='Crash Path',
        max_length=255,
        error_messages={
            'invalid': "Maximum length 255, should start with '\\\\'!"
        },
        widget=forms.TextInput(
            attrs={'class':'path_input'}
        )
    )
    
    crash_project_name = forms.CharField(
        widget=forms.HiddenInput,
        error_messages={
            'required': 'Please choose a Project!'
        }
    )
    
    crash_build_version = forms.CharField(
        widget=forms.HiddenInput,
        error_messages={
            'required': 'Please choose a Build!'
        }
    )
