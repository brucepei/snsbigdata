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
            prj_name = form.cleaned_data['project_name']
            prj_owner = form.cleaned_data['project_owner']
            target_prj = Project.objects.filter(name=prj_name)
            if not target_prj:
                Project.objects.create(name=prj_name, owner=prj_owner)
        else:
            request.session['project_error'] = ''
            for field, msg in form.errors.items():
                request.session['project_error'] += "{}:{}".format(field, msg)
        return redirect('tbd_project')
    else:
        prj_name = request.GET.get('project_name', '')
        get_method = request.GET.get('method', None)
        form = AddProjectForm()
        if get_method:
            if get_method.lower() == 'delete':
                target_prj = Project.objects.filter(name=prj_name)
                if target_prj:
                    target_prj.delete()
        project_error = None
        if 'project_error' in request.session:
            project_error = request.session.pop('project_error')
        return render(request, 'tbd/project.html', {'form': form, 'projects': Project.objects.all(), 'error_msg': project_error})

def build_page(request):
    return HttpResponse('<html>not implement</html>')
