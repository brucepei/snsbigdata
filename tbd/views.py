from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.utils import timezone
from tbd.models import Project
from .forms import AddProjectForm

# Create your views here.
def home_page(request):
    return render(request, 'tbd/home.html')

def project_page(request):
    if request.method == 'POST':
        form = AddProjectForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['name']
            prj_owner = form.cleaned_data['owner']
            target_prj = Project.objects.filter(name=prj_name)
            if not target_prj:
                Project.objects.create(name=prj_name, owner=prj_owner)
        else:
            request.session['flash_msg'] = ''
            request.session['flash_type'] = 'Error'
            for field, msg in form.errors.items():
                request.session['flash_msg'] += "{}:{}".format(field, msg)
        return redirect('tbd_project')
    else:
        prj_name = request.GET.get('name', '')
        get_method = request.GET.get('method', None)
        if get_method:
            if get_method.lower() == 'delete':
                target_prj = Project.objects.filter(name=prj_name)
                if target_prj:
                    target_prj.delete()
        if 'flash_type' in request.session:
            flash_type = request.session.pop('flash_type')
            flash_msg = request.session.pop('flash_msg')
            return render(request, 'tbd/project.html', {'projects': Project.objects.all(), 'error_type': flash_type, 'error_msg': flash_msg})
        else:
            return render(request, 'tbd/project.html', {'projects': Project.objects.all()})