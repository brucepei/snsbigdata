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

def slice_page(all_items, cur_page=1, items_in_page=5):
    page_data = {}
    if not isinstance(cur_page, int):
        try:
            cur_page = int(cur_page)
        except:
            print "Cannot translate cur_page {!r} to integer, so reset it to default 1!".format(cur_page)
            cur_page = 1
    page_data['cur'] = cur_page
    total_items = len(all_items)
    total_page = (total_items + items_in_page - 1) / items_in_page #round 1 once mod > 0 (but not 0.5)
    page_data['items'] = all_items[(cur_page - 1) * items_in_page : cur_page * items_in_page]
    page_data['list'] = xrange(1, total_page + 1) if total_page else []
    page_data['previous'] = cur_page - 1 if cur_page > 1 else 1
    page_data['next'] = cur_page + 1 if cur_page < total_page else total_page
    for no, item in enumerate(page_data['items']):
        setattr(item, 'no', no + 1 + items_in_page * (cur_page-1))
    return page_data

def add_host(prj_name, host_name, host_ip, host_mac, target_prj=None):
    if not target_prj:
        target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_host = Host.objects.filter(name=host_name, project=target_prj)
        if not target_host:
            try:
                Host.objects.create(name=host_name, ip=host_ip, mac=host_mac, project=target_prj)
            except Exception as err:
                return (-1, 'Host {} failed to create: {}'.format(host_name, err))
            return (0, "succeed to create Host {}".format(host_name))
        else:
            return (1, 'Host {} has already existed!'.format(host_name))
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name))
        
def del_host(prj_name, host_name, host_ip, host_mac, target_prj=None):
    if not target_prj:
        target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_host = Host.objects.filter(name=host_name, project=target_prj)
        if target_host:
            try:
                target_host.delete()
            except Exception as err:
                return (-1, 'Host {} failed to delete: {}'.format(host_name, err))
            return (0, "succeed to delete Host {}".format(host_name))
        else:
            return (1, 'Host {} is NOT existed!'.format(host_name))
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name))

def add_testcase(prj_name, tc_name, tc_platform, target_prj=None):
    if not target_prj:
        target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
        if not target_tc:
            try:
                TestCase.objects.create(name=tc_name, platform=tc_platform, project=target_prj)
            except Exception as err:
                return (-1, 'TestCase {}({}) failed to create: {}'.format(tc_name, tc_platform, err))
            return (0, "succeed to add TestCase {}".format(tc_name))
        else:
            return (1, 'TestCase {}({}) has already existed!'.format(tc_name, tc_platform))
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name))

def del_testcase(prj_name, tc_name, tc_platform, target_prj=None):
    if not target_prj:
        target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
        if target_tc:
            try:
                target_tc.delete()
            except Exception as err:
                return (-1, 'TestCase {}({}) failed to delete: {}'.format(tc_name, tc_platform, err))
            return (0, "succeed to delete TestCase {}".format(tc_name))
        else:
            return (1, 'TestCase {}({}) is NOT existed!'.format(tc_name, tc_platform))
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name))

def add_project(name, owner):
    target_prj = Project.objects.filter(name=name)
    if not target_prj:
        try:
            Project.objects.create(name=name, owner=owner)
        except Exception as err:
            return (-1, "Save Project {} failed: {}!".format(name, err))
        return (0, "Create Project {} successfully!".format(name))
    else:
        return (1, 'Project {} has already existed!'.format(name))

def add_build(prj_name, version, **build_attrs):
    target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_build = Build.objects.filter(project=target_prj, version=version)
        if not target_build:
            try:
                Build.objects.create(project=target_prj, version=version, **build_attrs)
            except Exception as err:
                return (-1, "Save Build {} in Project {} failed: {}!".format(version, prj_name, err))
            return (0, "Create Build {} in Project {} successfully!".format(version, prj_name))
        else:
            return (1, 'Build {} in Project {} is already existed!'.format(version, prj_name))
    else:
        return (-1, 'Project {} does NOT exist when create Build {}!'.format(prj_name, version))

def add_crash(prj_name, version, path, **crash_attrs):
    target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        if 'host_name' in crash_attrs and 'testcase_name' in crash_attrs and 'testcase_platform' in crash_attrs:
            target_tc = TestCase.objects.filter(name=crash_attrs['testcase_name'], platform=crash_attrs['testcase_platform'], project=target_prj)
            target_host = Host.objects.filter(name=crash_attrs['host_name'], project=target_prj)
            target_build = Build.objects.filter(project=target_prj, version=version)
            if target_tc and target_host and target_build:
                target_tc = target_tc[0]
                target_host = target_host[0]
                target_build = target_build[0]
                target_crash = Crash.objects.filter(build=target_build, path=path, testcase=target_tc, host=target_host)
                if not target_crash:
                    try:
                        Crash.objects.create(build=target_build, path=path, testcase=target_tc, host=target_host)
                    except Exception as err:
                        return (-1, "Save Crash {} in Project {} Build {} failed: {}!".format(path, prj_name, version, err))
                    return (0, "Create Crash {} in Project {} Build {} successfully!".format(path, prj_name, version))
                else:
                    return (1, "Crash {} in Project {} Build {} is already existed!".format(path, prj_name, version))
            else:
                return (-1, 'Build {}/Host {}/TestCase {} is NOT existed in Project {} when create crash {}!'.format(version, crash_attrs['host_name'], crash_attrs['testcase_name'], prj_name, path))
        else:
            return (-1, 'Not found host_name/testcase_name/testcase_platform in Project {} when create crash {}!'.format(version, prj_name, path))
    else:
        return (-1, 'Project {} does NOT exist when create Build {}!'.format(prj_name, version))

def del_project(name):
    target_prj = Project.objects.filter(name=name)
    if target_prj:
        try:
            target_prj[0].delete()
        except Exception as err:
            return (-1, "Delete Project {} failed: {}!".format(name, err))
        return (0, "Delete Project {} successfully!".format(name))
    else:
        return (0, 'Project {} is NOT existed, no necessary to delete!'.format(name))

def del_build(prj_name, version):
    target_prj = Project.objects.filter(name=prj_name)
    if target_prj:
        target_build = Build.objects.filter(project=target_prj[0], version=version)
        if target_build:
            try:
                target_build[0].delete()
            except Exception as err:
                return (-1, "Delete Build {} in Project {} failed: {}!".format(version, prj_name, err))
            return (0, "Delete Build {} in Project {} successfully!".format(version, prj_name))
        else:
            return (0, 'Build {} in Project {} is NOT existed, no necessary to delete!'.format(version, prj_name))
    else:
        return (-1, 'Project {} is NOT existed when delete Build {}!'.format(prj_name, version))

def project_select_options(select_prj_name=None):
    options = []
    for prj in Project.objects.all():
        is_select = False
        if select_prj_name and prj.name == select_prj_name:
            is_select = True
        options.append((
            {'name': prj.name, 'owner': prj.owner},
            "{}".format(prj.name),
            is_select
        ))
    return options

def build_select_options(target_prj, select_version=None):
    options = []
    for bld in Build.objects.filter(project=target_prj).order_by('-create'):
        is_select = False
        if select_version and bld.version == select_version:
            is_select = True
        options.append((
            {'version': bld.version, 'short_name': bld.short_name},
            "{}".format(bld.version),
            is_select
        ))
    return options

def host_select_options(target_prj, select_host=None, hosts=None):
    options = []
    if not hosts:
        hosts = Host.objects.filter(project=target_prj)
    for host in hosts:
        is_select = False
        if select_host and host.name == select_host:
            is_select = True
        options.append((
            {'host_name': host.name, 'host_ip': host.ip, 'host_mac': host.mac},
            "{}({})".format(host.name, host.ip),
            is_select
        ))
    return options

def testcase_select_options(target_prj, select_tc_name=None, select_tc_platform=None, testcases=None):
    options = []
    if not testcases:
        testcases = TestCase.objects.filter(project=target_prj)
    for tc in testcases:
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
    builds = None
    if prj_name:
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            builds = build_select_options(target_prj)
    return json_response(builds)

def _ajax_op_tc(request, op_func):
    form = AddTestCaseForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['testcase_project_name']
        tc_name = form.cleaned_data['testcase_name']
        tc_platform = form.cleaned_data['testcase_platform']
        target_prj = Project.objects.filter(name=prj_name)
        err_code, msg = op_func(prj_name, tc_name, tc_platform, target_prj)
        if err_code:
            return json_response(msg, err_code)
        else:
            return json_response(testcase_select_options(target_prj, tc_name, tc_platform))
    else:
        return json_response(form.errors, -1)

def ajax_add_tc(request):
    return _ajax_op_tc(request, add_testcase)

def ajax_del_tc(request):
    return _ajax_op_tc(request, del_testcase)

def _ajax_op_host(request, op_func):
    form = AddHostForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['host_project_name']
        host_name = form.cleaned_data['host_name']
        host_ip = form.cleaned_data['host_ip']
        host_mac = form.cleaned_data['host_mac']
        target_prj = Project.objects.filter(name=prj_name)
        err_code, msg = op_func(prj_name, host_name, host_ip, host_mac, target_prj)
        if err_code:
            return json_response(msg, err_code)
        else:
            return json_response(host_select_options(target_prj, host_name))
    else:
        return json_response(form.errors, -1)

def ajax_add_host(request):
    return _ajax_op_host(request, add_host)

def ajax_del_host(request):
    return _ajax_op_host(request, del_host)
    
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
    cur_page = request.GET.get('page', 1)
    form = AddProjectForm()
    page_data = slice_page(Project.objects.all().order_by('-create'), cur_page)
    return render(request, 'tbd/project.html', {'form': form, 'page': page_data, 'flash': flash(request)})

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
        return build_page_post(request)
    else:
        return build_page_get(request)

def build_page_post(request):
    get_method = request.POST.get('method', None)
    if get_method:
        prj_name = request.POST.get('project_name', '')
        if get_method == 'delete':
            err_code, msg = del_build(prj_name, request.POST['version'])
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash(request, {'type': 'danger', 'msg': 'Unsupport Build operation {}!'.format(get_method)})
    else:
        form = AddBuildForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['build_project_name']
            version = form.cleaned_data['build_version']
            err_code, msg = add_build(prj_name, version, short_name=form.cleaned_data['build_name'],
                server_path=form.cleaned_data['build_server_path'], crash_path=form.cleaned_data['build_crash_path'],
                local_path=form.cleaned_data['build_local_path'], use_server=form.cleaned_data['build_use_server'])
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
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

def build_page_get(request):
    prj_name = request.GET.get('project_name', '')
    get_method = request.GET.get('method', None)
    target_version = request.GET.get('version', None)
    cur_page = request.GET.get('page', 1)
    page_data = None
    form = AddBuildForm(initial={'build_project_name': prj_name})
    projects = Project.objects.all()
    target_prj = None
    if prj_name:
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            builds = Build.objects.filter(project=target_prj).order_by('-create')
            page_data = slice_page(builds, cur_page)
    return render(request, 'tbd/build.html', {'page': page_data, 'flash': flash(request), 
        'form': form, 'project': target_prj, 'projects': projects})

def testdata_page(request):
    if request.method == 'POST':
        return testdata_page_post(request)
    else:
        return testdata_page_get(request)

def testdata_page_post(request):
    form = AddCrashForm(request.POST)
    if form.is_valid():
        prj_name = form.cleaned_data['crash_project_name']
        version = form.cleaned_data['crash_build_version']
        err_code, msg = add_crash(prj_name, version, form.cleaned_data['crash_path'],
            host_name=form.cleaned_data['crash_host_name'], testcase_name=form.cleaned_data['crash_testcase_name'],
            testcase_platform=form.cleaned_data['crash_testcase_platform'])
        err_type = 'danger' if err_code else 'success'
        flash(request, {'type': err_type, 'msg': msg})
    else:
        prj_name = request.POST.get('crash_project_name', '')
        version = request.POST.get('crash_build_version', '')
        flash_err = ''
        for field, msg in form.errors.items():
            flash_err += "{}:{}".format(field, msg)
        flash(request, {'type': 'danger', 'msg': flash_err})
    redirect_url = reverse('tbd_testdata')
    if prj_name and version:
        redirect_url += '?project_name={}&version={}'.format(prj_name, version)
    return redirect(redirect_url)

def testdata_page_get(request):
    prj_name = request.GET.get('project_name', '')
    version = request.GET.get('version', '')
    sort_by = request.GET.get('sort_by', 'Host')
    cur_page = request.GET.get('page', 1)
    crash_form = AddCrashForm(initial={'crash_project_name': prj_name, 'crash_build_version': version})
    host_form = AddHostForm(initial={'host_project_name': prj_name})
    testcase_form = AddTestCaseForm(initial={'testcase_project_name': prj_name})
    form = {'crash':crash_form, 'host': host_form, 'testcase': testcase_form}
    page_data = None
    target_prj = None
    target_build = None
    json_vars = {key: 'null' for key in ('builds', 'testcases', 'hosts')}
    json_vars['projects'] = json.dumps(project_select_options(prj_name))
    if prj_name:
        target_prj = Project.objects.filter(name=prj_name)
        if target_prj:
            target_prj = target_prj[0]
            all_hosts = Host.objects.filter(project=target_prj)
            all_testcases = TestCase.objects.filter(project=target_prj)
            json_vars['hosts'] = json.dumps(host_select_options(target_prj, None, all_hosts))
            json_vars['testcases'] = json.dumps(testcase_select_options(target_prj, None, all_testcases))
            json_vars['builds'] = json.dumps(build_select_options(target_prj, version))
            if version:
                target_build = Build.objects.filter(project=target_prj, version=version)
                if target_build:
                    target_build = target_build[0]
                    if sort_by == 'Host':
                        all_items = all_hosts
                        key_item = 'host'
                    else:
                        all_items = all_testcases
                        key_item = 'testcase'
                    for item in all_items:
                        crashes = Crash.objects.filter(build=target_build, **{key_item: item})
                        item.total_crash = len(crashes)
                        item.valid_crash = 0
                        item.open_crash = 0
                        for crash in crashes:
                            if crash.jira:
                                item.valid_crash += 1
                                item.open_crash += 1
                    page_data = slice_page(all_items, cur_page)
    return render(request, 'tbd/testdata.html', {'page': page_data, 'flash': flash(request), 'sort_by': sort_by,
        'form': form, 'project': target_prj, 'build': target_build, 'json_vars': json_vars,
    })
