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

def flash(request, flash_type=None, flash_msg=None):
    if flash_type:
        request.session['flash_type'] = flash_type
        request.session['flash_msg'] = flash_msg
        # print "save type {}, err: {}".format(request.session['flash_type'], request.session['flash_msg'])
    else:
        flash_type = request.session.pop('flash_type') if 'flash_type' in request.session else None
        flash_msg = request.session.pop('flash_msg') if 'flash_msg' in request.session else None
        # print "load type {}, err: {}".format(flash_type, flash_msg)
        return (flash_type, flash_msg)
    
def project_page(request):
    if request.method == 'POST':
        form = AddProjectForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['project_name']
            prj_owner = form.cleaned_data['project_owner']
            target_prj = Project.objects.filter(name=prj_name)
            if not target_prj:
                Project.objects.create(name=prj_name, owner=prj_owner)
                flash(request, 'success', "Create Project {} successfully!".format(prj_name))
            else:
                flash(request, 'danger', 'Project {} has laready existed!'.format(prj_name))
        else:
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, 'danger', flash_err)
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
        flash_type, flash_msg = flash(request)
        return render(request, 'tbd/project.html', {'form': form, 'projects': Project.objects.all(), 'flash_type': flash_type, 'flash_msg': flash_msg})

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
                flash(request, 'success', "Create Build {} successfully!".format(version))
            else:
                flash(request, 'danger', 'Project {} does NOT exist when create Build!'.format(prj_name))
        else:
            prj_name = request.POST.get('build_project_name', '')
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, 'danger', flash_err)
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
        flash_type, flash_msg = flash(request)
        return render(request, 'tbd/build.html', {'flash_type':flash_type, 'flash_msg':flash_msg, 'form': form, 'project': target_prj, 'builds': builds, 'projects': projects})
