from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from tbd.models import Project, Build, Crash, TestCase, Host
from .forms import AddProjectForm, AddBuildForm, AddCrashForm, AddHostForm, AddTestCaseForm
import json

#internal func
def flash(request, flash_data=None):
    if flash_data:
        request.session['flash_data'] = flash_data
    else:
        flash_data = request.session.pop('flash_data') if 'flash_data' in request.session else None
        return flash_data

def json_response(json, code=0):
    if code and hasattr(json, 'items'):
        err_str = ''
        for k, v in json.items():
            err_str += "<span>{}</span>{}".format(k, v)
        json = err_str
    return JsonResponse({'code': code, 'result': json})

def add_project(name, owner):
    target_prj = Project.objects.filter(name=name)
    if not target_prj:
        try:
            Project.objects.create(name=name, owner=owner)
        except Exception as err:
            return (-1, "Save Project {} failed: {}!".format(name, err))
        return (0, "Create Project {} successfully!".format(name))
    else:
        return (-1, 'Project {} has already existed!')

def del_project(name):
    target_prj = Project.objects.filter(name=name)
    if target_prj:
        try:
            target_prj.delete()
        except Exception as err:
            return (-1, "Delete Project {} failed: {}!".format(name, err))
        return (0, "Delete Project {} successfully!".format(name))
    else:
        return (0, 'Project {} is NOT existed, no necessary to delete!')

def host_select_options(target_prj, select_host=None):
    options = []
    for host in Host.objects.filter(project=target_prj):
        is_select = False
        if select_host and host.name == select_host:
            is_select = True
        options.append((
            {'host_name': host.name, 'host_ip': host.ip, 'host_mac': host.mac},
            "{}({})".format(host.name, host.ip),
            is_select
        ))
    return options

def testcase_select_options(target_prj, select_tc_name=None, select_tc_platform=None):
    options = []
    for tc in TestCase.objects.filter(project=target_prj):
        is_select = False
        if select_tc_name and select_tc_platform and tc.name == select_tc_name and tc.platform == select_tc_platform:
            is_select = True
        options.append((
            {'testcase_name': tc.name, 'testcase_platform': tc.platform},
            "{}({})".format(tc.name, tc.platform),
            is_select
        ))
    return options

#ajax views
def ajax(request, action):
    global_vars = globals()
    action = 'ajax_' + action
    if action in global_vars and callable(global_vars[action]):
        func = global_vars[action]
        return func(request)
    else:
        return json_response("Unknown ajax action: {!r}!".format(action), -1)

def ajax_get_builds(request):
    prj_name = request.POST.get('project_name', None)
    builds = []
    if prj_name:
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            builds = Build.objects.filter(project=target_prj).order_by('-create')
    return json_response([bld.version for bld in builds])

def ajax_add_tc(request):
    form = AddTestCaseForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['testcase_project_name']
        tc_name = form.cleaned_data['testcase_name']
        tc_platform = form.cleaned_data['testcase_platform']
        print "project={}, tc_platform={}, tc_platform={}".format(prj_name, tc_name, tc_platform)
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
            if not target_tc:
                try:
                    TestCase.objects.create(name=tc_name, platform=tc_platform, project=target_prj)
                except Exception as err:
                    return json_response('TestCase {}({}) failed to create: {}'.format(tc_name, tc_platform, err), -1)
                return json_response(testcase_select_options(target_prj, tc_name, tc_platform))
            else:
                return json_response('TestCase {}({}) has already existed!'.format(tc_name, tc_platform), -1)
        else:
            return json_response('Project {} does NOT exist!'.format(prj_name), -1)
    else:
        return json_response(form.errors, -1)

def ajax_del_tc(request):
    form = AddTestCaseForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['testcase_project_name']
        tc_name = form.cleaned_data['testcase_name']
        tc_platform = form.cleaned_data['testcase_platform']
        print "project={}, tc_platform={}, tc_platform={}".format(prj_name, tc_name, tc_platform)
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
            if target_tc:
                try:
                    target_tc.delete()
                except Exception as err:
                    return json_response('TestCase {}({}) failed to delete: {}'.format(tc_name, tc_platform, err), -1)
                return json_response(testcase_select_options(target_prj))
            else:
                return json_response('TestCase {}({}) is NOT existed!'.format(tc_name, tc_platform), -1)
        else:
            return json_response('Project {} does NOT exist!'.format(prj_name), -1)
    else:
        return json_response(form.errors, -1)

def ajax_del_host(request):
    form = AddHostForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['host_project_name']
        host_name = form.cleaned_data['host_name']
        host_ip = form.cleaned_data['host_ip']
        host_mac = form.cleaned_data['host_mac']
        print "project={}, host_name={}, host_ip={}, host_mac={}".format(prj_name, host_name, host_ip, host_mac)
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            target_host = Host.objects.filter(name=host_name, project=target_prj)
            if target_host:
                try:
                    target_host.delete()
                except Exception as err:
                    return json_response('Host {} failed to delete: {}'.format(host_name, err), -1)
                return json_response(host_select_options(target_prj))
            else:
                return json_response('Host {} is NOT existed!'.format(host_name), -1)
        else:
            return json_response('Project {} does NOT exist!'.format(prj_name), -1)
    else:
        return json_response(form.errors, -1)

def ajax_add_host(request):
    form = AddHostForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['host_project_name']
        host_name = form.cleaned_data['host_name']
        host_ip = form.cleaned_data['host_ip']
        host_mac = form.cleaned_data['host_mac']
        print "project={}, host_name={}, host_ip={}, host_mac={}".format(prj_name, host_name, host_ip, host_mac)
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            target_host = Host.objects.filter(name=host_name, project=target_prj)
            if not target_host:
                try:
                    Host.objects.create(name=host_name, ip=host_ip, mac=host_mac, project=target_prj)
                except Exception as err:
                    return json_response('Host {} failed to create: {}'.format(host_name, err), -1)
                return json_response(host_select_options(target_prj, host_name))
            else:
                return json_response('Host {} has laready existed!'.format(host_name), -1)
        else:
            return json_response('Project {} does NOT exist!'.format(prj_name), -1)
    else:
        return json_response(form.errors, -1)
    
# Create your views here.
def home_page(request):
    return render(request, 'tbd/home.html')
        
def project_page(request):
    if request.method == 'POST':
        return project_page_post(request)
    else:
        return project_page_get(request)

def project_page_get(request):
    prj_name = request.GET.get('project_name', '')
    form = AddProjectForm()
    return render(request, 'tbd/project.html', {'form': form, 'projects': Project.objects.all(), 'flash': flash(request)})

def project_page_post(request):
    get_method = request.POST.get('method', None)
    if get_method:
        if get_method == 'delete':
            err_code, msg = del_project(request.POST['project_name'])
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash(request, {'type': 'danger', 'msg': 'Unsupport project operation {}!'.format(get_method)})
    else:
        form = AddProjectForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['project_name']
            prj_owner = form.cleaned_data['project_owner']
            err_code, msg = add_project(prj_name, prj_owner)
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, {'type': 'danger', 'msg': flash_err})
    return redirect('tbd_project')

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
        items_in_page = 5
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
                total_page = (total_builds+items_in_page-1)/items_in_page
                builds = builds[(cur_page-1)*items_in_page:cur_page*items_in_page]
        page_data['list'] = xrange(1, total_page+1) if total_page else []
        page_data['previous'] = cur_page - 1 if cur_page > 1 else 1
        page_data['next'] = cur_page + 1 if cur_page < total_page else total_page
        for no, build in enumerate(builds):
            setattr(build, 'no', no + 1 + items_in_page * (cur_page-1))
        return render(request, 'tbd/build.html', {'page': page_data, 'flash': flash(request), 
            'form': form, 'project': target_prj, 'builds': builds, 'projects': projects})

def testdata_page(request):
    if request.method == 'POST':
        # form = AddProjectForm(request.POST)
        # if form.is_valid():
        return redirect('tbd_testdata')
    else:
        prj_name = request.GET.get('project_name', '')
        version = request.GET.get('version', '')
        page_data = {}
        cur_page = request.GET.get('page', 1)
        try:
            cur_page = int(cur_page)
        except:
            cur_page = 1
        page_data['cur'] = cur_page
        total_page = None
        items_in_page = 5
        crash_form = AddCrashForm(initial={'crash_project_name': prj_name, 'crash_build_version': version})
        host_form = AddHostForm(initial={'host_project_name': prj_name})
        testcase_form = AddTestCaseForm(initial={'testcase_project_name': prj_name})
        form = {'crash':crash_form, 'host': host_form, 'testcase': testcase_form}
        projects = Project.objects.all()
        testcases = json.dumps(None)
        hosts = json.dumps(None)
        builds = []
        crashes = []
        target_prj = None
        target_build = None
        if prj_name:
            target_prj = Project.objects.filter(name=prj_name)
            if target_prj:
                target_prj = target_prj[0]
                hosts = json.dumps(host_select_options(target_prj))
                testcases = json.dumps(testcase_select_options(target_prj))
                builds = Build.objects.filter(project=target_prj).order_by('-create')
                if version:
                    target_build = Build.objects.filter(project=target_prj, version=version)
                    if target_build:
                        target_build = target_build[0]
                        crashes = Crash.objects.filter(build=target_build)
                total_crashes = len(crashes)
                total_page = (total_crashes+items_in_page-1)/items_in_page
                crashes = crashes[(cur_page-1)*items_in_page:cur_page*items_in_page]
        page_data['list'] = xrange(1, total_page+1) if total_page else []
        page_data['previous'] = cur_page - 1 if cur_page > 1 else 1
        page_data['next'] = cur_page + 1 if cur_page < total_page else total_page
        for no, crash in enumerate(crashes):
            setattr(crash, 'no', no + 1 + items_in_page * (cur_page-1))
        return render(request, 'tbd/testdata.html', {'page': page_data, 'flash': flash(request), 
            'form': form, 'project': target_prj, 'build': target_build, 'crashes': crashes, 'builds': builds, 'projects': projects,
            'testcases': testcases, 'hosts': hosts})