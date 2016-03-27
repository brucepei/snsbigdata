from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import timezone
from tbd.models import Project
from tbd.models import Build
from .forms import AddProjectForm, AddBuildForm

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
                request.session['project_error'] = 'Project {} has laready existed!'.format(prj_name)
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
    if request.method == 'POST':
        form = AddBuildForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['build_project_name']
            target_prj = Project.objects.filter(name=prj_name)
            if target_prj:
                target_prj = target_prj[0]
                version = form.cleaned_data['build_version']
                short_name = form.cleaned_data['build_name']
                server_path = form.cleaned_data['build_server_path']
                crash_path = form.cleaned_data['build_crash_path']
                local_path = form.cleaned_data['build_local_path']
                use_server = form.cleaned_data['build_use_server']
                Build.objects.create(project=target_prj, version=version, short_name=short_name, server_path=server_path,
                    crash_path=crash_path, local_path=local_path, use_server=use_server)
            else:
                request.session['build_error'] = 'Project {} does NOT exist when create Build!'.format(prj_name)
        else:
            prj_name = request.POST['build_project_name']
            request.session['build_error'] = ''
            for field, msg in form.errors.items():
                request.session['build_error'] += "{}:{}".format(field, msg)
        redirect_url = reverse('tbd_build')
        if prj_name:
            redirect_url += '?project_name=' + prj_name
        return redirect(redirect_url)
    else:
        prj_name = request.GET.get('project_name', '')
        form = AddBuildForm(initial={'build_project_name': prj_name})
        projects = Project.objects.all()
        builds = []
        target_prj = None
        if prj_name:
            target_prj = Project.objects.filter(name=prj_name)
            if target_prj:
                target_prj = target_prj[0]
                builds = Build.objects.filter(project=target_prj)
        build_error = None
        if 'build_error' in request.session:
            build_error = request.session.pop('build_error')
        return render(request, 'tbd/build.html', {'error_msg':build_error, 'form': form, 'project': target_prj, 'builds': builds, 'projects': projects})
