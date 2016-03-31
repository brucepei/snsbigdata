from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils import timezone
from tbd.models import Project
from tbd.models import Build
from tbd.models import Crash
from .forms import AddProjectForm, AddBuildForm, AddCrashForm

# Create your views here.
def home_page(request):
    return render(request, 'tbd/home.html')
    
def flash(request, flash_data=None):
    if flash_data:
        request.session['flash_data'] = flash_data
    else:
        flash_data = request.session.pop('flash_data') if 'flash_data' in request.session else None
        return flash_data
        
def project_page(request):
    if request.method == 'POST':
        form = AddProjectForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['project_name']
            prj_owner = form.cleaned_data['project_owner']
            target_prj = Project.objects.filter(name=prj_name)
            if not target_prj:
                try:
                    Project.objects.create(name=prj_name, owner=prj_owner)
                    flash(request, {'type': 'success', 'msg': "Create Project {} successfully!".format(prj_name)})
                except Exception as err:
                    flash(request, {'type': 'danger', 'msg': "Save Project {} failed: {}!".format(prj_name, err)})
            else:
                flash(request, {'type': 'danger', 'msg': 'Project {} has laready existed!'.format(prj_name)})
        else:
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, {'type': 'danger', 'msg': flash_err})
        return redirect('tbd_project')
    else:
        prj_name = request.GET.get('project_name', '')
        get_method = request.GET.get('method', None)
        form = AddProjectForm()
        if get_method:
            if get_method.lower() == 'delete':
                target_prj = Project.objects.filter(name=prj_name)
                if target_prj:
                    try:
                        target_prj.delete()
                        flash(request, {'type': 'success', 'msg': "Delete Project {} successfully!".format(prj_name)})
                    except Exception as err:
                        flash(request, {'type': 'danger', 'msg': "Delete Project {} failed: {}!".format(prj_name, err)})
        return render(request, 'tbd/project.html', {'form': form, 'projects': Project.objects.all(), 'flash': flash(request)})

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
                try:
                    Build.objects.create(project=target_prj, version=version, short_name=short_name, server_path=server_path,
                        crash_path=crash_path, local_path=local_path, use_server=use_server)
                    flash(request, {'type': 'success', 'msg': "Create Build {} successfully!".format(version)})
                except Exception as err:
                    flash(request, {'type': 'danger', 'msg': "Save Build {} failed: {}!".format(version, err)})
            else:
                flash(request, {'type': 'danger', 'msg': 'Project {} does NOT exist when create Build!'.format(prj_name)})
        else:
            prj_name = request.POST.get('build_project_name', '')
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, {'type': 'danger', 'msg': flash_err})
        redirect_url = reverse('tbd_build')
        if prj_name:
            redirect_url += '?project_name=' + prj_name
        return redirect(redirect_url)
    else:
        prj_name = request.GET.get('project_name', '')
        get_method = request.GET.get('method', None)
        target_version = request.GET.get('version', None)
        page_data = {}
        cur_page = request.GET.get('page', 1)
        try:
            cur_page = int(cur_page)
        except:
            cur_page = 1
        page_data['cur'] = cur_page
        total_page = None
        builds_in_page = 5
        form = AddBuildForm(initial={'build_project_name': prj_name})
        projects = Project.objects.all()
        builds = []
        target_prj = None
        if prj_name:
            target_prj = Project.objects.filter(name=prj_name)
            if target_prj:
                target_prj = target_prj[0]
                if target_version and get_method:
                    if get_method.lower() == 'delete':
                        target_build = Build.objects.filter(project=target_prj, version=target_version)
                        if target_build:
                            try:
                                target_build[0].delete()
                                flash(request, {'type': 'success', 'msg': "Delete Version {} in Project {} successfully!".format(target_version, prj_name)})
                            except Exception as err:
                                flash(request, {'type': 'danger', 'msg': "Delete Version {} in Project {} failed: {}!".format(target_version, prj_name, err)})
                builds = Build.objects.filter(project=target_prj).order_by('-create')
                total_builds = len(builds)
                total_page = (total_builds+builds_in_page-1)/builds_in_page
                builds = builds[(cur_page-1)*builds_in_page:cur_page*builds_in_page]
        page_data['list'] = xrange(1, total_page+1) if total_page else []
        page_data['previous'] = cur_page - 1 if cur_page > 1 else 1
        page_data['next'] = cur_page + 1 if cur_page < total_page else total_page
        for no, build in enumerate(builds):
            setattr(build, 'no', no + 1 + builds_in_page * (cur_page-1))
        return render(request, 'tbd/build.html', {'page': page_data, 'flash': flash(request), 
            'form': form, 'project': target_prj, 'builds': builds, 'projects': projects})

def testdata_page(request):
    if request.method == 'POST':
        # form = AddProjectForm(request.POST)
        # if form.is_valid():
        return redirect('tbd_testdata')
    else:
        form = AddCrashForm()
        return render(request, 'tbd/testdata.html', {'form': form})