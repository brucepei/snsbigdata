from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from tbd.models import Project, Build, Crash, TestCase, Host, JIRA
from .forms import AddProjectForm, AddBuildForm, AddCrashForm, AddHostForm, AddTestCaseForm
import time
import json

DEFAULT = {
    'jira': {'name': ''},
    'host': {'name': '!NULL!'},
    'testcase': {'name': '!NULL!'},
}

try:
    jira = JIRA.objects.filter(is_default=True)
    if jira:
        jira = jira[0]
        if jira.category != JIRA.NONE or jira.jira_id != DEFAULT['jira']['name']:
            jira.jira_id = DEFAULT['jira']['name']
            jira.category = JIRA.NONE
            jira.save()
    else:
        JIRA.objects.create(is_default=True, jira_id=DEFAULT['jira']['name'], category=JIRA.NONE)
    for prj in Project.objects.all():
        host = Host.objects.filter(project=prj, is_default=True)
        if host:
            host = host[0]
            if host.name != DEFAULT['host']['name']:
                host.name = DEFAULT['host']['name']
                host.save()
        else:
            Host.objects.create(is_default=True, project=prj, name=DEFAULT['host']['name'])
        testcase = TestCase.objects.filter(project=prj, is_default=True)
        if testcase:
            testcase = testcase[0]
            if testcase.name != DEFAULT['testcase']['name']:
                testcase.name = DEFAULT['testcase']['name']
                testcase.save()
        else:
            TestCase.objects.create(is_default=True, project=prj, name=DEFAULT['testcase']['name'])
    print "!!!!!!!!!!!!!Initial DB done!!!!!!!!!!!!!!!!"
except Exception as err:
    print err
    
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
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_host = Host.objects.filter(name=host_name, project=target_prj)
        if not target_host:
            try:
                target_host = Host.objects.create(name=host_name, ip=host_ip, mac=host_mac, project=target_prj)
            except Exception as err:
                return (-1, 'Host {} failed to create: {}'.format(host_name, err), None)
            return (0, "succeed to create Host {}".format(host_name), target_host)
        else:
            return (1, 'Host {} has already existed!'.format(host_name), target_host[0])
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name), None)
        
def del_host(prj_name, host_name, host_ip, host_mac, target_prj=None):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_host = Host.objects.filter(name=host_name, project=target_prj)
        if target_host:
            try:
                target_host[0].delete()
            except Exception as err:
                return (-1, 'Host {} failed to delete: {}'.format(host_name, err), None)
            return (0, "succeed to delete Host {}".format(host_name), target_host[0])
        else:
            return (1, 'Host {} is NOT existed!'.format(host_name), None)
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name), None)

def add_testcase(prj_name, tc_name, tc_platform, target_prj=None):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
        if not target_tc:
            try:
                target_tc = TestCase.objects.create(name=tc_name, platform=tc_platform, project=target_prj)
            except Exception as err:
                return (-1, 'TestCase {}({}) failed to create: {}'.format(tc_name, tc_platform, err), None)
            return (0, "succeed to add TestCase {}".format(tc_name), target_tc)
        else:
            return (1, 'TestCase {}({}) has already existed!'.format(tc_name, tc_platform), target_tc[0])
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name), None)

def del_testcase(prj_name, tc_name, tc_platform, target_prj=None):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_tc = TestCase.objects.filter(name=tc_name, platform=tc_platform, project=target_prj)
        if target_tc:
            try:
                target_tc[0].delete()
            except Exception as err:
                return (-1, 'TestCase {}({}) failed to delete: {}'.format(tc_name, tc_platform, err), None)
            return (0, "succeed to delete TestCase {}".format(tc_name), target_tc[0])
        else:
            return (1, 'TestCase {}({}) is NOT existed!'.format(tc_name, tc_platform), None)
    else:
        return (-1, 'Project {} does NOT exist!'.format(prj_name), None)

def add_project(name, owner):
    target_prj = Project.objects.filter(name=name)
    if not target_prj:
        try:
            target_prj = Project.objects.create(name=name, owner=owner)
        except Exception as err:
            return (-1, "Save Project {} failed: {}!".format(name, err), None)
        return (0, "Create Project {} successfully!".format(name), target_prj)
    else:
        return (1, 'Project {} has already existed!'.format(name), target_prj[0])

def add_build(prj_name, version, target_prj=None, **build_attrs):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        target_build = Build.objects.filter(project=target_prj, version=version)
        if not target_build:
            try:
                target_build = Build.objects.create(project=target_prj, version=version, **build_attrs)
            except Exception as err:
                return (-1, "Save Build {} in Project {} failed: {}!".format(version, prj_name, err), None)
            return (0, "Create Build {} in Project {} successfully!".format(version, prj_name), target_build)
        else:
            return (1, 'Build {} in Project {} is already existed!'.format(version, prj_name), target_build[0])
    else:
        return (-1, 'Project {} does NOT exist when create Build {}!'.format(prj_name, version), None)

def add_crash(prj_name, version, path, target_prj=None, target_build=None, target_host=None, target_tc=None, **crash_attrs):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_prj = target_prj[0]
        if (target_host or 'host_name' in crash_attrs) and (target_tc or ('testcase_name' in crash_attrs and 'testcase_platform' in crash_attrs)):
            target_tc = [target_tc] if target_tc else TestCase.objects.filter(name=crash_attrs['testcase_name'], platform=crash_attrs['testcase_platform'], project=target_prj)
            target_host = [target_host] if target_host else Host.objects.filter(name=crash_attrs['host_name'], project=target_prj)
            target_build = [target_build] if target_build else Build.objects.filter(project=target_prj, version=version)
            if target_tc and target_host and target_build:
                target_tc = target_tc[0]
                target_host = target_host[0]
                target_build = target_build[0]
                target_crash = Crash.objects.filter(build=target_build, path=path, testcase=target_tc, host=target_host)
                if not target_crash:
                    try:
                        target_crash = Crash.objects.create(build=target_build, path=path, testcase=target_tc, host=target_host)
                    except Exception as err:
                        return (-1, "Save Crash {} in Project {} Build {} failed: {}!".format(path, prj_name, version, err), None)
                    return (0, "Create Crash {} in Project {} Build {} successfully!".format(path, prj_name, version), target_crash)
                else:
                    return (1, "Crash {} in Project {} Build {} is already existed!".format(path, prj_name, version), target_crash[0])
            else:
                return (-1, 'Build {}/Host {}/TestCase {} is NOT existed in Project {} when create crash {}!'.format(version, crash_attrs['host_name'], crash_attrs['testcase_name'], prj_name, path), None)
        else:
            return (-1, 'Not found host_name/testcase_name/testcase_platform in Project {} when create crash {}!'.format(version, prj_name, path), None)
    else:
        return (-1, 'Project {} does NOT exist when create Build {}!'.format(prj_name, version), None)

def del_project(name):
    target_prj = Project.objects.filter(name=name)
    if target_prj:
        try:
            target_prj[0].delete()
        except Exception as err:
            return (-1, "Delete Project {} failed: {}!".format(name, err), None)
        return (0, "Delete Project {} successfully!".format(name), target_prj[0])
    else:
        return (1, 'Project {} is NOT existed, no necessary to delete!'.format(name), None)

def del_build(prj_name, version, target_prj=None):
    target_prj = [target_prj] if target_prj else Project.objects.filter(name=prj_name)
    if target_prj:
        target_build = Build.objects.filter(project=target_prj[0], version=version)
        if target_build:
            try:
                target_build[0].delete()
            except Exception as err:
                return (-1, "Delete Build {} in Project {} failed: {}!".format(version, prj_name, err), None)
            return (0, "Delete Build {} in Project {} successfully!".format(version, prj_name), target_build[0])
        else:
            return (1, 'Build {} in Project {} is NOT existed, no necessary to delete!'.format(version, prj_name), None)
    else:
        return (-1, 'Project {} is NOT existed when delete Build {}!'.format(prj_name, version), None)

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

def ajax_running_project_list(request):
    print "request list:" + repr(request)
    records = []
    if request.method == 'POST':
        start_index = int(request.GET.get('jtStartIndex', 0))
        page_size = int(request.GET.get('jtPageSize', 20))
        projects = Project.objects.all().order_by('-create')[start_index: page_size+start_index]
        for prj in projects:
            running_build_id = prj.attr('running_build')
            target_build = None
            crash_num = 0
            total_hours = 0
            if running_build_id:
                target_build = Build.objects.filter(id=running_build_id)
                if target_build:
                    target_build = target_build[0]
                    total_hours = target_build.test_hours
                    crash_num = Crash.objects.filter(build=target_build).count()
            record = {'prj_id': prj.id,
                      'prj_name': prj.name,
                      'prj_owner': prj.owner,
                      'running_build': running_build_id,
                      'os_type': prj.attr('os_type'),
                      'os_ver': prj.attr('os_ver'),
                      'board_type': prj.attr('board_type'),
                      'total_devices': prj.attr('total_devices'),
                      'total_hours': total_hours,
                      'crash_num': crash_num,
                      'cs_date': prj.attr('cs_date'),
                      'last_update': prj.last_update,
            }
            records.append(record)
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': Project.objects.count()})

def ajax_running_project_update(request):
    print request.POST
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        prj_name = request.POST.get('prj_name', None)
        prj_owner = request.POST.get('prj_owner', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                if target_prj:
                    is_set = False
                    if prj_name != target_prj.name:
                        target_prj.name = prj_name
                        is_set = True
                    if prj_owner != target_prj.owner:
                        target_prj.owner = prj_owner
                        is_set = True
                    for attr in ('running_build', 'cs_date', 'os_type', 'os_ver', 'board_type',
                                 'total_devices', 'last_update'):
                        attr_val = request.POST.get(attr, None)
                        if attr_val is not None:
                            if target_prj.attr(attr, attr_val):
                                is_set = True
                    if is_set:
                        target_prj.save()
                        print "Change project, save {}!".format(prj_name)
                    else:
                        print "Not change project, don't save!"
    return JsonResponse({'Result': 'OK'})

def ajax_running_project_list_builds(request):
    print request.POST
    options = [{
        "DisplayText": '--no build--',
        "Value": ''
    }]
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                for bld in Build.objects.filter(project=target_prj).order_by('-create'):
                    options.append({
                        "DisplayText": bld.short_name,
                        "Value": bld.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})
    
def ajax_project_list(request):
    print "request project list:" + repr(request)
    records = []
    if request.method == 'POST':
        start_index = int(request.GET.get('jtStartIndex', 0))
        page_size = int(request.GET.get('jtPageSize', 20))
        projects = Project.objects.all().order_by('-create')[start_index: page_size+start_index]
        for prj in projects:
            records.append({
                'prj_id': prj.id,
                'prj_name': prj.name,
                'prj_owner': prj.owner,
                'build_num': Build.objects.filter(project=prj).count(),
                'host_num': Host.objects.filter(project=prj, is_default=False).count(),
                'testcase_num': TestCase.objects.filter(project=prj, is_default=False).count(),
                'create_time': prj.create,
            })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': Project.objects.count()})

def ajax_project_delete(request):
    print "request project delete:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        target_prj = Project.objects.filter(id=prj_id)
        if target_prj:
            try:
                target_prj[0].delete()
            except Exception as err:
                message = "Delete Project {} failed: {}!".format(target_prj[0].name, err)
        else:
            message = 'Project id {} is NOT existed, no necessary to delete!'.format(prj_id)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_project_create(request):
    print "request project create:" + repr(request.POST)
    message = None
    record = None
    if request.method == 'POST':
        prj_name = request.POST.get('prj_name', None)
        prj_owner = request.POST.get('prj_owner', None)
        target_prj = Project.objects.filter(name=prj_name)
        if not target_prj:
            try:
                target_prj = Project.objects.create(name=prj_name, owner=prj_owner)
                record = {
                    'prj_id': target_prj.id,
                    'prj_name': target_prj.name,
                    'prj_owner': target_prj.owner,
                    'build_num': 0,
                    'host_num': 0,
                    'testcase_num': 0,
                    'create_time': target_prj.create,
                }
            except Exception as err:
                message = "Save Project {} failed: {}!".format(name, err)
            try:
                Host.objects.create(is_default=True, project=target_prj, name=DEFAULT['host']['name'])
                TestCase.objects.create(is_default=True, project=target_prj, name=DEFAULT['testcase']['name'])
            except Exception as err:
                message = "Failed to create related default host/testcase for project {}: {}!".format(target_prj.name, err)
        else:
            message = 'Project {} has already existed!'.format(name)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})
    
def ajax_build_list(request):
    print "request build list:" + repr(request)
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('prj_id', None)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                running_build_id = target_prj.attr('running_build')
                total_count = Build.objects.filter(project=target_prj).count()
                for bld in Build.objects.filter(project=target_prj).order_by('-create')[start_index: page_size+start_index]:
                    records.append({
                        'build_id': bld.id,
                        'running_build_id': running_build_id,
                        'build_version': bld.version,
                        'build_short_name': bld.short_name,
                        'build_server_path': bld.server_path,
                        'build_local_path': bld.local_path,
                        'build_crash_path': bld.crash_path,
                        'build_test_hours': bld.test_hours,
                        'build_use_server': 'true' if bld.use_server else 'false',
                        'crash_num': Crash.objects.filter(build=bld).count(),
                        'create_time': bld.create,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})
    
def ajax_build_create(request):
    print "request build create:" + repr(request.POST)
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                build_version = request.POST.get('build_version', None)
                if build_version:
                    target_build = Build.objects.filter(project=target_prj, version=build_version)
                    if not target_build:
                        use_server = True if request.POST.get('build_use_server', 'False').lower() == 'true' else False
                        test_hour = request.POST.get('build_test_hours', 0)
                        if not test_hour:
                            test_hour = 0
                        try:
                            target_build = Build.objects.create(
                                project=target_prj,
                                version=build_version,
                                short_name=request.POST.get('build_short_name', build_version),
                                server_path=request.POST.get('build_server_path', None),
                                local_path=request.POST.get('build_local_path', None),
                                crash_path=request.POST.get('build_crash_path', None),
                                test_hours=test_hour,
                                use_server=use_server,
                            )
                            record = {
                                'build_id': target_build.id,
                                'build_version': target_build.version,
                                'build_short_name': target_build.short_name,
                                'build_server_path': target_build.server_path,
                                'build_local_path': target_build.local_path,
                                'build_crash_path': target_build.crash_path,
                                'build_test_hours': target_build.test_hours,
                                'build_use_server': target_build.use_server,
                                'crash_num': 0,
                                'create_time': target_build.create,
                            }
                        except Exception as err:
                            message = "Save Build {} in Project {} failed: {}!".format(build_version, target_prj.name, err)
                    else:
                        message = 'Build {} has already existed!'.format(build_version)
                else:
                    message = 'Lack necessary arguement: build version!'
            else:
                message = 'Project id {} does NOT existed!'.format(prj_id)
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_build_update(request):
    print "request build update:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
                is_set = False
                for attr in ('build_server_path', 'build_local_path', 'build_crash_path', 'build_test_hours',
                             'build_use_server', 'build_short_name', 'build_version'):
                    attr_val = request.POST.get(attr, None)
                    if attr == 'build_use_server':
                        attr_val = True if attr_val and attr_val.lower() == 'true' else False
                    if attr_val is not None:
                        attr_name = attr[6:]
                        orig_val = getattr(target_build, attr_name, None)
                        if orig_val != attr_val:
                            setattr(target_build, attr_name, attr_val)
                            is_set = True
                if is_set:
                    try:
                        target_build.save()
                    except Exception as err:
                        message = "Save Build {} failed: {}!".format(target_build.version, err)
                    print "Change build, save {}!".format(target_build.version)
                else:
                    print "Not change build, don't save!"
            else:
                message = 'Build id {} does NOT existed!'.format(build_id)
        else:
            message = 'Lack necessary arguement: build id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_build_delete(request):
    print "request build delete:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
                try:
                    target_build.delete()
                except Exception as err:
                    message = "Delete Build {} failed: {}!".format(target_build.version, err)
            else:
                message = 'Build id {} is NOT existed, no necessary to delete!'.format(build_id)
        else:
            message = 'Lack necessary arguement: build id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_host_list(request):
    print "request host list:" + repr(request.POST)
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        target_build = None
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                total_count = Host.objects.filter(project=target_prj).count()
                for host in Host.objects.filter(project=target_prj).order_by('name')[start_index: page_size+start_index]:
                    if target_build:
                        crash_num = Crash.objects.filter(host=host, build=target_build).count()
                        print "crash num {}, in host {} build {}!".format(crash_num, host.name, target_build.version)
                    else:
                        crash_num = Crash.objects.filter(host=host).count()
                        print "crash num {}, in host {}!".format(crash_num, host.name)
                    records.append({
                        'host_id': host.id,
                        'host_name': host.name,
                        'host_ip': host.ip,
                        'host_mac': host.mac,
                        'crash_num': crash_num,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_host_create(request):
    print "request build create:" + repr(request.POST)
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                host_name = request.POST.get('host_name', None)
                host_ip = request.POST.get('host_ip', None)
                host_mac = request.POST.get('host_mac', None)
                try:
                    target_host = Host.objects.create(project=target_prj, name=host_name, ip=host_ip, mac=host_mac)
                    record = {
                        'id': target_host.id,
                        'name': target_host.name,
                        'ip': target_host.ip,
                        'mac': target_host.mac,
                        'crash_num': 0,
                    }
                except Exception as err:
                    message = "Save Host {} failed: {}!".format(host_name, err)
            else:
                message = 'Project id {} does NOT exist!'.format(prj_id)
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})
    
def ajax_host_update(request):
    print "request host update:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        host_id = request.POST.get('host_id', None)
        if host_id:
            target_host = Host.objects.filter(id=host_id)
            if target_host:
                target_host = target_host[0]
                if target_host.is_default:
                    message = "Default host {} cannot be edited!".format(target_host.name)
                else:
                    is_set = False
                    for attr in ('host_name', 'host_ip', 'host_mac'):
                        attr_val = request.POST.get(attr, None)
                        if attr_val is not None:
                            attr_name = attr[5:]
                            orig_val = getattr(target_host, attr_name, None)
                            if orig_val != attr_val:
                                setattr(target_host, attr_name, attr_val)
                                is_set = True
                    if is_set:
                        try:
                            target_host.save()
                        except Exception as err:
                            message = "Save Host {} failed: {}!".format(target_host.name, err)
                        print "Change Host, save {}!".format(target_host.name)
                    else:
                        print "Not change host, don't save!"
            else:
                message = 'Host id {} does NOT exist!'.format(host_id)
        else:
            message = 'Lack necessary arguement: host id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_host_delete(request):
    print "request host delete:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        host_id = request.POST.get('host_id', None)
        if host_id:
            target_host = Host.objects.filter(id=host_id)
            if target_host:
                target_host = target_host[0]
                if target_host.is_default:
                    message = "Default host {} cannot be deleted!".format(target_host.name)
                else:
                    try:
                        target_host.delete()
                    except Exception as err:
                        message = "Delete Host {} failed: {}!".format(target_host.name, err)
            else:
                message = 'Host id {} is NOT existed, no necessary to delete!'.format(host_id)
        else:
            message = 'Lack necessary arguement: host id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_testcase_list(request):
    print "request testcase list:" + repr(request.POST)
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        target_build = None
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                total_count = TestCase.objects.filter(project=target_prj).count()
                for tc in TestCase.objects.filter(project=target_prj).order_by('name')[start_index: page_size+start_index]:
                    if target_build:
                        crash_num = Crash.objects.filter(testcase=tc, build=target_build).count()
                        print "crash num {}, in testcase {} build {}!".format(crash_num, tc.name, target_build.version)
                    else:
                        crash_num = Crash.objects.filter(testcase=tc).count()
                        print "crash num {}, in testcase {}!".format(crash_num, tc.name)
                    records.append({
                        'testcase_id': tc.id,
                        'testcase_name': tc.name,
                        'testcase_platform': tc.platform,
                        'crash_num': crash_num,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_testcase_create(request):
    print "request testcase create:" + repr(request.POST)
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                testcase_name = request.POST.get('testcase_name', None)
                testcase_platform = request.POST.get('testcase_platform', None)
                try:
                    target_testcase = TestCase.objects.create(project=target_prj, name=testcase_name, platform=testcase_platform)
                    record = {
                        'id': target_testcase.id,
                        'name': target_testcase.name,
                        'platform': target_testcase.platform,
                        'crash_num': 0,
                    }
                except Exception as err:
                    message = "Save TestCase {} failed: {}!".format(testcase_name, err)
            else:
                message = 'Project id {} does NOT exist!'.format(prj_id)
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})
    
def ajax_testcase_update(request):
    print "request testcase update:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        testcase_id = request.POST.get('testcase_id', None)
        if testcase_id:
            target_testcase = TestCase.objects.filter(id=testcase_id)
            if target_testcase:
                target_testcase = target_testcase[0]
                if target_testcase.is_default:
                    message = "Default testcase {} cannot be edited!".format(target_testcase.name)
                else:
                    is_set = False
                    for attr in ('testcase_name', 'testcase_platform'):
                        attr_val = request.POST.get(attr, None)
                        if attr_val is not None:
                            attr_name = attr[9:]
                            orig_val = getattr(target_testcase, attr_name, None)
                            if orig_val != attr_val:
                                setattr(target_testcase, attr_name, attr_val)
                                is_set = True
                    if is_set:
                        try:
                            target_testcase.save()
                        except Exception as err:
                            message = "Save TestCase {} failed: {}!".format(target_testcase.name, err)
                        print "Change TestCase, save {}!".format(target_testcase.name)
                    else:
                        print "Not change Testcase, don't save!"
            else:
                message = 'TestCase id {} does NOT exist!'.format(testcase_id)
        else:
            message = 'Lack necessary arguement: testcase id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_testcase_delete(request):
    print "request testcase delete:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        testcase_id = request.POST.get('testcase_id', None)
        if testcase_id:
            target_testcase = TestCase.objects.filter(id=testcase_id)
            if target_testcase:
                target_testcase = target_testcase[0]
                if target_testcase.is_default:
                    message = "Default testcase {} cannot be deleted!".format(target_testcase.name)
                else:
                    try:
                        target_testcase.delete()
                    except Exception as err:
                        message = "Delete TestCase {} failed: {}!".format(target_testcase.name, err)
            else:
                message = 'TestCase id {} is NOT existed, no necessary to delete!'.format(testcase_id)
        else:
            message = 'Lack necessary arguement: testcase id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_crash_list(request):
    print "request crash list:" + repr(request.POST)
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        target_build = None
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                if target_build:
                    crashes = Crash.objects.filter(build=target_build).order_by('-create')[start_index: page_size+start_index]
                    total_count = Crash.objects.filter(build=target_build).count()
                    print "crash num {}, in build {}!".format(total_count, target_build.version)
                else:
                    crashes = Crash.objects.filter(build__project=target_prj).order_by('-create')[start_index: page_size+start_index]
                    total_count = Crash.objects.filter(build__project=target_prj).count()
                    print "crash num {}, in project {}!".format(total_count, target_prj.name)
                for crash in crashes:
                    records.append({
                        'crash_id': crash.id,
                        'crash_path': crash.path,
                        'build_id': crash.build.id,
                        'host_id': crash.host.id,
                        'testcase_id': crash.testcase.id,
                        'jira_id': crash.jira.jira_id,
                        'jira_category': crash.jira.category,
                        'create_time': crash.create,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_crash_list_hosts(request):
    print request.POST
    options = []
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                for host in Host.objects.filter(project=target_prj).order_by('name'):
                    options.append({
                        "DisplayText": str(host),
                        "Value": host.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_crash_list_testcases(request):
    print request.POST
    options = []
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = Project.objects.filter(id=prj_id)
            if target_prj:
                target_prj = target_prj[0]
                for tc in TestCase.objects.filter(project=target_prj).order_by('name'):
                    options.append({
                        "DisplayText": str(tc),
                        "Value": tc.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_crash_create(request):
    print "request crash create:" + repr(request.POST)
    message = None
    record = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = Build.objects.filter(id=build_id)
            if target_build:
                target_build = target_build[0]
                target_host = None
                target_testcase = None
                target_jira = None
                crash_path = request.POST.get('crash_path', None)
                host_id = request.POST.get('host_id', None)
                testcase_id = request.POST.get('testcase_id', None)
                jira_id = request.POST.get('jira_id', None)
                if host_id:
                    target_host = Host.objects.filter(id=host_id)
                else:
                    target_host = Host.objects.filter(is_default=True, project=target_build.project)
                if target_host:
                    target_host = target_host[0]
                if testcase_id:
                    target_testcase = TestCase.objects.filter(id=testcase_id)
                else:
                    target_testcase = TestCase.objects.filter(is_default=True, project=target_build.project)
                if target_testcase:
                    target_testcase = target_testcase[0]
                if jira_id:
                    try:
                        target_jira, created = JIRA.objects.get_or_create(jira_id=jira_id)
                    except Exception as err:
                        print "Failed to create JIRA by jira id {}: {}".format(jira_id, err)
                if not target_jira:
                    target_jira = JIRA.objects.filter(is_default=True)
                    if target_jira:
                        target_jira = target_jira[0]
                try:
                    target_crash = Crash.objects.create(build=target_build, path=crash_path, host=target_host, testcase=target_testcase, jira=target_jira)
                    record = {
                        'id': target_crash.id,
                        'path': target_crash.path,
                        'build_id': target_crash.build.id,
                        'host_id': target_crash.host.id,
                        'testcase_id': target_crash.testcase.id,
                        'jira_id': target_crash.jira.jira_id,
                        'jira_category': target_crash.jira.category,
                    }
                except Exception as err:
                    message = "Save Crash {} failed: {}!".format(crash_path, err)
            else:
                message = 'Build id {} does NOT exist!'.format(build_id)
        else:
            message = 'Lack necessary arguement: build id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_crash_delete(request):
    print "request crash delete:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        crash_id = request.POST.get('crash_id', None)
        if crash_id:
            target_crash = Crash.objects.filter(id=crash_id)
            if target_crash:
                target_crash = target_crash[0]
                try:
                    target_crash.delete()
                except Exception as err:
                    message = "Delete Crash {} failed: {}!".format(target_crash.path, err)
            else:
                message = 'Crash id {} is NOT existed, no necessary to delete!'.format(crash_id)
        else:
            message = 'Lack necessary arguement: Crash id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_crash_update(request):
    print "request crash create:" + repr(request.POST)
    message = None
    if request.method == 'POST':
        crash_id = request.POST.get('crash_id', None)
        if crash_id:
            target_crash = Crash.objects.filter(id=crash_id)
            if target_crash:
                target_crash = target_crash[0]
                is_set = False
                build_id = request.POST.get('build_id', None)
                host_id = request.POST.get('host_id', None)
                testcase_id = request.POST.get('testcase_id', None)
                jira_id = request.POST.get('jira_id', None)
                if target_crash.build and build_id != target_crash.build.id:
                    target_build = Build.objects.filter(id=build_id)
                    if target_build:
                        target_crash.build = target_build[0]
                        is_set = True
                if target_crash.host and host_id != target_crash.host.id:
                    target_host = Host.objects.filter(id=host_id)
                    if target_host:
                        target_crash.host = target_host[0]
                        is_set = True
                if target_crash.testcase and testcase_id != target_crash.testcase.id:
                    target_testcase = TestCase.objects.filter(id=testcase_id)
                    if target_testcase:
                        target_crash.testcase = target_testcase[0]
                        is_set = True
                if jira_id != target_crash.jira_id:
                    try:
                        target_jira, created = JIRA.objects.get_or_create(jira_id=jira_id)
                    except Exception as err:
                        print "Failed to get/create JIRA by jira id {}: {}".format(jira_id, err)
                    if target_jira:
                        target_crash.jira = target_jira
                        is_set = True
                for attr in ('crash_path',):
                    attr_val = request.POST.get(attr, None)
                    if attr_val is not None:
                        attr_name = attr[6:]
                        orig_val = getattr(target_crash, attr_name, None)
                        #print "set {} from {} to {}!".format(attr_name, orig_val, attr_val)
                        if orig_val != attr_val:
                            setattr(target_crash, attr_name, attr_val)
                            is_set = True
                if is_set:
                    try:
                        target_crash.save()
                    except Exception as err:
                        message = "Save Crash {} failed: {}!".format(target_crash.path, err)
                    print "Change Crash, save {}!".format(target_crash.path)
                else:
                    print "Not change Crash, don't save!"
            else:
                message = 'Crash id {} does NOT exist!'.format(crash_id)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

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
        err_code, msg, tc = op_func(prj_name, tc_name, tc_platform)
        if err_code:
            return json_response(msg, err_code)
        else:
            return json_response(testcase_select_options(tc.project, tc_name, tc_platform))
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
        err_code, msg, host = op_func(prj_name, host_name, host_ip, host_mac)
        if err_code:
            return json_response(msg, err_code)
        else:
            return json_response(host_select_options(host.project, host_name))
    else:
        return json_response(form.errors, -1)

def ajax_add_host(request):
    return _ajax_op_host(request, add_host)

def ajax_del_host(request):
    return _ajax_op_host(request, del_host)
    
# Create auto API here, no CSRF
@csrf_exempt
def auto(request, action):
    global_vars = globals()
    action = 'auto_' + action
    if action in global_vars and callable(global_vars[action]):
        func = global_vars[action]
        return func(request)
    else:
        return json_response("Unknown auto action: {!r}!".format(action), -1)
    
def auto_crash_info(request):
    err_code = None
    msg = None
    if request.method == 'POST':
        prj_name = request.POST.get('project_name', None)
        #prj_owner = request.POST.get('project_owner', '')
        build_version = request.POST.get('build_version', None)
        path = request.POST.get('path', None)
        host_name = request.POST.get('host_name', None)
        host_ip = request.POST.get('host_ip', '')
        host_mac = request.POST.get('host_mac', '')
        tc_name = request.POST.get('testcase_name', None)
        tc_platform = request.POST.get('testcase_platform', '')
        jira_id = request.POST.get('jira_id', None)
        if path and prj_name and build_version and host_name and tc_name:
            build = Build.objects.filter(project__name=prj_name, version=build_version)
            if build:
                build = build[0]
                try:
                    host, created = Host.objects.get_or_create(project=build.project, name=host_name, ip=host_ip, mac=host_mac)
                    testcase, created = TestCase.objects.get_or_create(project=build.project, name=tc_name, platform=tc_platform)
                    jira = None
                    if jira_id:
                        jira, created = JIRA.objects.get_or_create(jira_id=jira_id, category='OP')
                    if not jira:
                        jira = JIRA.objects.filter(is_default=True)
                        if jira:
                            jira = jira[0]
                    crash, created = Crash.objects.get_or_create(path=path, build=build, host=host, testcase=testcase, jira=jira)
                    if created:
                        msg = "Create crash done!"
                    else:
                        msg = "Crash already existed!"
                except Exception as err:
                    msg = "Failed to create crash record: {}".format(err)
                    err_code = -1
                    return json_response(msg, err_code)
                return json_response(msg, 0)
            else:
                return json_response("Not found build {}!".format(build_version), -1)
        else:
            return json_response("Need necessary arguments when auto create crash!", -1)
    return json_response(msg, err_code)

# Create your views here.
def home_page(request):
    #cur_page = request.GET.get('page', 1)
    #item_per_page = 20
    #page_data = slice_page(Project.objects.all().order_by('-create'), cur_page, item_per_page)
    #return render(request, 'tbd/home.html', {'page': page_data})
    return render(request, 'tbd/home.html')
        
def project_page(request):
    #if request.method == 'POST':
    #    return project_page_post(request)
    #else:
    #    return project_page_get(request)
    return render(request, 'tbd/project.html')

def project_page_get(request):
    cur_page = request.GET.get('page', 1)
    form = AddProjectForm()
    page_data = slice_page(Project.objects.all().order_by('-create'), cur_page)
    return render(request, 'tbd/project.html', {'form': form, 'page': page_data, 'flash': flash(request)})

def project_page_post(request):
    get_method = request.POST.get('method', None)
    if get_method:
        if get_method == 'delete':
            err_code, msg, _ = del_project(request.POST['project_name'])
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash(request, {'type': 'danger', 'msg': 'Unsupport project operation {}!'.format(get_method)})
    else:
        form = AddProjectForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['project_name']
            prj_owner = form.cleaned_data['project_owner']
            err_code, msg, _ = add_project(prj_name, prj_owner)
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash_err = ''
            for field, msg in form.errors.items():
                flash_err += "{}:{}".format(field, msg)
            flash(request, {'type': 'danger', 'msg': flash_err})
    return redirect('tbd_project')

def build_page(request):
    #if request.method == 'POST':
    #    return build_page_post(request)
    #else:
    #    return build_page_get(request)
    prj_id = request.GET.get('prj_id', '')
    projects = Project.objects.all()
    target_prj = None
    builds = []
    if prj_id:
        target_prj = Project.objects.filter(id=prj_id)
        if target_prj:
            target_prj = target_prj[0]
    return render(request, 'tbd/build.html', {'project': target_prj, 'projects': projects})

def host_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    projects = Project.objects.all()
    target_prj = None
    target_build = None
    builds = []
    if build_id:
        target_build = Build.objects.filter(id=build_id)
        if target_build:
            target_build = target_build[0]
            target_prj = target_build.project
            builds = target_prj.build_set.order_by('-create')
    elif prj_id:
        target_prj = Project.objects.filter(id=prj_id)
        if target_prj:
            target_prj = target_prj[0]
            builds = Build.objects.filter(project=target_prj).order_by('-create')
    return render(request, 'tbd/host.html', {'project': target_prj, 'projects': projects, 'build': target_build, 'builds': builds})

def testcase_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    projects = Project.objects.all()
    target_prj = None
    target_build = None
    builds = []
    if build_id:
        target_build = Build.objects.filter(id=build_id)
        if target_build:
            target_build = target_build[0]
            target_prj = target_build.project
            builds = target_prj.build_set.order_by('-create')
    elif prj_id:
        target_prj = Project.objects.filter(id=prj_id)
        if target_prj:
            target_prj = target_prj[0]
            builds = Build.objects.filter(project=target_prj).order_by('-create')
    return render(request, 'tbd/testcase.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'testcase_platform_choice': json.dumps(dict(TestCase.PLATFORM_CHOICE)),
    })

def crash_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    projects = Project.objects.all()
    target_prj = None
    target_build = None
    builds = []
    if build_id:
        target_build = Build.objects.filter(id=build_id)
        if target_build:
            target_build = target_build[0]
            target_prj = target_build.project
            builds = target_prj.build_set.order_by('-create')
    elif prj_id:
        target_prj = Project.objects.filter(id=prj_id)
        if target_prj:
            target_prj = target_prj[0]
            builds = Build.objects.filter(project=target_prj).order_by('-create')
    return render(request, 'tbd/crash.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'jira_category_choice': json.dumps(dict(JIRA.CATEGORY_CHOICE)),
    })

def build_page_post(request):
    get_method = request.POST.get('method', None)
    if get_method:
        prj_name = request.POST.get('project_name', '')
        if get_method == 'delete':
            err_code, msg, _ = del_build(prj_name, request.POST['version'])
            err_type = 'danger' if err_code else 'success'
            flash(request, {'type': err_type, 'msg': msg})
        else:
            flash(request, {'type': 'danger', 'msg': 'Unsupport Build operation {}!'.format(get_method)})
    else:
        form = AddBuildForm(request.POST)
        if form.is_valid():
            prj_name = form.cleaned_data['build_project_name']
            version = form.cleaned_data['build_version']
            err_code, msg, _ = add_build(prj_name, version, short_name=form.cleaned_data['build_short_name'],
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
            for item in page_data['items']:
                crashes = Crash.objects.filter(build=item)
                item.total_dump = len(crashes)
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
        err_code, msg, _ = add_crash(prj_name, version, form.cleaned_data['crash_path'],
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
                        item.total_dump = len(crashes)
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
