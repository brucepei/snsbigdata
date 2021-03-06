from __future__ import division
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from collections import Iterable
from tbd.models import Project, TestAction, Build, Crash, TestCase, Host, JIRA, TestResult,TestTime
from .forms import AddProjectForm, AddBuildForm, AddCrashForm, AddHostForm, AddTestCaseForm
from .tasks import query_issue_frequency
from celery.result import AsyncResult
from SnSBigData import celery_app
import time
import json,datetime
from .tools.write_excel_result import write_excel
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum
# from dwebsocket.decorators import accept_websocket,require_websocket

DEFAULT = {
    'jira': {'name': ''},
    'host': {'name': '!NULL!'},
    'testaction': {'name': '!COMMON_TA!'},
    'testcase': {'name': '!NULL!'},
}


ONE_DAY = 24 * 60 * 60
ONE_HOUR = 60 * 60
ONE_MINUTE = 60

Cache_Issue_Frequency_Buffer = 'ifb_{}'
Cache_Issue_Frequency_Timeout = 15 * ONE_DAY
# Issue_Frequency_Buffer = {
#     # issue1 => {result: {}, assoc_issues: [], orig_issue_id: issue1, start_at: ?, update_at: ?}
# }
# Issue_Frequency_Buffer = set()


def seconds_to_humanable(seconds):
    if seconds > ONE_DAY:
        humanable_str = "{:.1f} days".format(seconds/ONE_DAY)
    elif seconds > ONE_HOUR:
        humanable_str = "{:.1f} hours".format(seconds/ONE_HOUR)
    elif seconds > ONE_MINUTE:
        humanable_str = "{:.1f} minutes".format(seconds/ONE_MINUTE)
    else:
        humanable_str = "{:.1f} seconds".format(seconds)
    return humanable_str

def get_cached_issue_frequency(target_issue_id, check_result=False):
    target_issue_id = target_issue_id.upper()
    cached_key = Cache_Issue_Frequency_Buffer.format(target_issue_id)
    cached_issue = cache.get(cached_key)
    if (cached_issue is not None) and (not isinstance(cached_issue, dict)):
        print("get associated cached issue: {} for {}".format(cached_issue, target_issue_id))
        cached_key = Cache_Issue_Frequency_Buffer.format(cached_issue)
        cached_issue = cache.get(cached_key)
    if isinstance(cached_issue, dict):
        if (not check_result) or (check_result and (cached_issue.get('result', None) or cached_issue.get('exception', None))):
            print("get cached issue: {}".format(target_issue_id))
            return cached_issue
    print("Cannot get cached issue!")
    return None

def update_issue_frequency(issue_id, result=None, assoc_issues=None, exception=None):
    issue_id = issue_id.upper()
    cached_key = Cache_Issue_Frequency_Buffer.format(issue_id)
    need_cached_result = get_cached_issue_frequency(issue_id)
    if need_cached_result:
        if result:
            need_cached_result['result'] = result
            need_cached_result['update_at'] = time.time()
        elif exception:
            need_cached_result['exception'] = exception
            need_cached_result['update_at'] = time.time()
        else:
            print("Update cached issue {}, but no result found!".format(issue_id))
    else:
        need_cached_result = {
            'start_at': time.time(),
            'orig_issue_id': issue_id,
        }
        if result:
            need_cached_result['update_at'] = time.time() #start_at and update_at at the same time
            need_cached_result['result'] = result
    if assoc_issues is not None:
        try:
            assoc_issues = json.loads(assoc_issues)
        except Exception as err:
            print("Failed to deserialize json: {}, error: {}".format(assoc_issues, err))
        if isinstance(assoc_issues, list):
            assoc_issues_dict = {}
            for assoc_issue in assoc_issues:
                assoc_cached_key = Cache_Issue_Frequency_Buffer.format(assoc_issue.upper())
                assoc_issues_dict[assoc_cached_key] = issue_id
            if assoc_issues_dict:
                cache.set_many(assoc_issues_dict, Cache_Issue_Frequency_Timeout)
    cache.set(cached_key, need_cached_result, Cache_Issue_Frequency_Timeout)

def query_cached_issue_frequency(issue_id, result_url, force_refresh):
    issue_id = issue_id.upper()
    cached_result = get_cached_issue_frequency(issue_id, True) #True: must get completed result, but not pending result!
    if cached_result:
        if force_refresh:
            orig_cached_key = Cache_Issue_Frequency_Buffer.format(cached_result['orig_issue_id'])
            print("Force refresh, and delete cached result with orig id: {}".format(cached_result['orig_issue_id']))
            cache.delete(orig_cached_key)
        else:
            return
    query_issue_frequency.delay(issue_id, result_url)
    update_issue_frequency(issue_id)

def set_default_records(prj_name=None, project=None, set_jira=False, set_host=False, set_testcase=False, set_testaction=False):
    result = None
    try:
        if set_jira:
            jira = None
            try:
                jira = JIRA.objects.get(is_default=True)
            except Exception as err:
                print("Not found default JIRA, need to create!")
            if jira:
                if jira.category != JIRA.NONE or jira.jira_id != DEFAULT['jira']['name']:
                    print("Rset default JIRA attribution!")
                    jira.jira_id = DEFAULT['jira']['name']
                    jira.category = JIRA.NONE
                    jira.save()
            else:
                print("Create default JIRA!")
                JIRA.objects.create(is_default=True, jira_id=DEFAULT['jira']['name'], category=JIRA.NONE)
        prj_list = None
        if project:
            prj_list = [project]
        elif prj_name:
            prj_list = Project.objects.filter(name=prj_name)
        else:
            prj_list = Project.objects.all()
        for prj in prj_list:
            if set_host:
                host = None
                try:
                    host = Host.objects.get(project=prj, is_default=True)
                except Exception as err:
                    print("Not found default Host, need to create!")
                if host:
                    if host.name != DEFAULT['host']['name']:
                        print("Rset default host attribution for project {}!".format(prj.name))
                        host.name = DEFAULT['host']['name']
                        host.save()
                else:
                    print("Create default host for project {}!".format(prj.name))
                    Host.objects.create(is_default=True, project=prj, name=DEFAULT['host']['name'], ip='', mac='')
            if set_testcase:
                testcase = None
                try:
                    testcase = TestCase.objects.get(project=prj, is_default=True)
                except Exception as err:
                    print("Not found default TestCase, need to create!")
                if testcase:
                    if testcase.name != DEFAULT['testcase']['name']:
                        print("Rset default testcase attribution for project {}!".format(prj.name))
                        testcase.name = DEFAULT['testcase']['name']
                        testcase.save()
                else:
                    print("Create default testcase for project {}!".format(prj.name))
                    TestCase.objects.create(is_default=True, project=prj, name=DEFAULT['testcase']['name'], platform='')
            if set_testaction:
                testaction = None
                try:
                    testaction = TestAction.objects.get(project=prj, is_default=True)
                except Exception as err:
                    print("Not found default TestAction, need to create!")
                if testaction:
                    if testaction.name != DEFAULT['testaction']['name']:
                        print("Rset default TestAction attribution for project {}!".format(prj.name))
                        testaction.name = DEFAULT['testaction']['name']
                        testaction.save()
                else:
                    print("Create default TestAction for project {}!".format(prj.name))
                    TestAction.objects.create(is_default=True, project=prj, name=DEFAULT['testaction']['name'])
    except Exception as err:
        result = "Failed to set default records: {}".format(err)
        print(result)
    return result

set_default_records(set_jira=True, set_testcase=True, set_host=True, set_testaction=True)
#internal func
def json_response(json, code=0):
    if code and hasattr(json, 'items'):
        err_str = ''
        for k, v in json.items():
            err_str += "<span>{}</span>{}".format(k, v)
        json = err_str
    return JsonResponse({'code': code, 'result': json})

def calc_crash_num(build=None, host=None, testcase=None):
    total_crash = 0
    valid_crash = 0
    cnss_crash = 0
    user_filter = {}
    if build:
        user_filter['build'] = build
    if host:
        user_filter['host'] = host
    if testcase:
        user_filter['testcase'] = testcase
    if user_filter:
        crashes = Crash.objects.filter(**user_filter)
        total_crash = len(crashes)
        for crash in crashes:
            if crash.jira.is_cnss():
                cnss_crash += 1
                valid_crash += 1
            elif crash.jira.is_valid():
                valid_crash += 1
    else:
        print("%Error%: no filter found when calculate crash number!")
    return "{}({})/{}".format(valid_crash, cnss_crash, total_crash)

#ajax views
def ajax(request, action):
    global_vars = globals()
    action = 'ajax_' + action
    if action in global_vars and callable(global_vars[action]):
        func = global_vars[action]
        return func(request)
    else:
        return json_response("Unknown ajax action: {!r}!".format(action), -1)
#running_project
def ajax_running_project_list(request):
    print("request list:" + repr(request))
    records = []
    if request.method == 'POST':
        start_index = int(request.GET.get('jtStartIndex', 0))
        page_size = int(request.GET.get('jtPageSize', 20))
        projects = Project.objects.filter(is_stop=False).order_by('owner', 'name')[start_index: page_size+start_index]
        for prj in projects:
            running_build_id = prj.attr('running_build')
            target_build = None
            total_hours = 0
            last_crash = None
            build_options = [{
                "DisplayText": '--no build--',
                "Value": ''
            }]
            for bld in Build.objects.filter(project=prj, is_stop=False).order_by('-create'):
                build_options.append({
                    "DisplayText": bld.short_name,
                    "Value": bld.id
                })
                if running_build_id and str(bld.id) == running_build_id:
                    target_build = bld
                    total_hours = target_build.test_hours
                    try:
                        last_crash = Crash.objects.filter(build=target_build).latest('create')
                    except Exception:
                        pass
            record = {'prj_id': prj.id,
                      'prj_name': prj.name,
                      'prj_owner': prj.owner,
                      'running_build': running_build_id,
                      'os_type': prj.attr('os_type'),
                      'os_ver': prj.attr('os_ver'),
                      'board_type': prj.attr('board_type'),
                      'total_devices': prj.attr('total_devices'),
                      'total_hours': total_hours,
                      'crash_num': calc_crash_num(build=target_build),
                      'build_create': timezone.localtime(target_build.create).strftime("%Y-%m-%d %H:%M:%S") if target_build else None,
                      'last_crash': timezone.localtime(last_crash.create).strftime("%Y-%m-%d %H:%M:%S") if last_crash else None,
                      'build_options': build_options,
            }
            records.append(record)
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': Project.objects.filter(is_stop=False).count()})

def ajax_running_project_update(request):
    print(request.POST)
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
                    for attr in ('running_build', 'os_type', 'os_ver', 'board_type',
                                 'total_devices'):
                        attr_val = request.POST.get(attr, None)
                        if attr_val is not None:
                            if target_prj.attr(attr, attr_val):
                                is_set = True
                    if is_set:
                        target_prj.save()
                        print("Change project, save {}!".format(prj_name))
                    else:
                        print("Not change project, don't save!")
    return JsonResponse({'Result': 'OK'})
#project
def ajax_project_list(request):
    print("request project list:" + repr(request))
    records = []
    if request.method == 'POST':
        start_index = int(request.GET.get('jtStartIndex', 0))
        page_size = int(request.GET.get('jtPageSize', 20))
        projects = Project.objects.all().order_by('is_stop', 'name')[start_index: page_size+start_index]
        for prj in projects:
            records.append({
                'prj_id': prj.id,
                'prj_name': prj.name,
                'prj_owner': prj.owner,
                'prj_is_stop': 'true' if prj.is_stop else 'false',
                'build_num': Build.objects.filter(project=prj).count(),
                'host_num': Host.objects.filter(project=prj, is_default=False).count(),
                'testaction_num': TestAction.objects.filter(project=prj, is_default=False).count(),
                'testcase_num': TestCase.objects.filter(project=prj, is_default=False).count(),
                'es_date': prj.attr('es_date'),
                'fc_date': prj.attr('fc_date'),
                'cs_date': prj.attr('cs_date'),
                'create_time': timezone.localtime(prj.create).strftime("%Y-%m-%d %H:%M:%S") if prj.create else None,
            })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': Project.objects.count()})

def ajax_project_delete(request):
    print("request project delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        target_prj = None
        try:
            target_prj = Project.objects.get(id=prj_id)
        except Exception as err:
            message = "Failed to get project with id {}: {}!".format(prj_id, err)
        if target_prj:
            try:
                hosts = Host.objects.filter(project=target_prj)
                if len(hosts) == 1 and hosts[0].is_default == True:
                    hosts[0].delete()
                testcases = TestCase.objects.filter(project=target_prj)
                if len(testcases) == 1 and testcases[0].is_default == True:
                    testcases[0].delete()
                testactions = TestAction.objects.filter(project=target_prj)
                if len(testactions) == 1 and testactions[0].is_default == True:
                    testactions[0].delete()
                target_prj.delete()
            except Exception as err:
                message = "Delete Project {} failed: {}!".format(target_prj.name, err)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_project_update(request):
    print(request.POST)
    message = None
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        prj_name = request.POST.get('prj_name', None)
        prj_owner = request.POST.get('prj_owner', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                is_set = False
                for attr in ('prj_name', 'prj_owner', 'prj_is_stop'):
                    attr_val = request.POST.get(attr, None)
                    if attr == 'prj_is_stop':
                        attr_val = True if attr_val and attr_val.lower() == 'true' else False
                    if attr_val is not None:
                        attr_name = attr[4:]
                        orig_val = getattr(target_prj, attr_name, None)
                        if orig_val != attr_val:
                            setattr(target_prj, attr_name, attr_val)
                            is_set = True
                for attr in ('es_date', 'fc_date', 'cs_date', ):
                    attr_val = request.POST.get(attr, None)
                    if attr_val is not None:
                        if target_prj.attr(attr, attr_val):
                            is_set = True
                if is_set:
                    try:
                        target_prj.save()
                    except Exception as err:
                        message = "Save project {} failed: {}!".format(target_prj.name, err)
                    print("Change project, save {}!".format(target_prj.name))
                else:
                    print("Not change project, don't save!")
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_project_create(request):
    print("request project create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        prj_name = request.POST.get('prj_name', None)
        prj_owner = request.POST.get('prj_owner', None)
        es_date = request.POST.get('es_date', None)
        fc_date = request.POST.get('fc_date', None)
        cs_date = request.POST.get('cs_date', None)
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
                    'testaction_num': 0,
                    'es_date': es_date,
                    'fc_date': fc_date,
                    'cs_date': cs_date,
                    'create_time': timezone.localtime(target_prj.create).strftime("%Y-%m-%d %H:%M:%S") if target_prj.create else None,
                }
                target_prj.attr('es_date', es_date)
                target_prj.attr('fc_date', fc_date)
                target_prj.attr('cs_date', cs_date)
                target_prj.save()
            except Exception as err:
                message = "Save Project {} failed: {}!".format(prj_name, err)
            set_default_result = set_default_records(project=target_prj, set_testcase=True, set_host=True, set_testaction=True)
            if set_default_result:
                message = "Failed to create related default host/testcase for project {}: {}!".format(target_prj.name, set_default_result)
        else:
            message = 'Project {} has already existed!'.format(prj_name)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})
#testaction
def ajax_testaction_list(request):
    print("request testaction list:" + repr(request))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            total_count = TestAction.objects.filter(project__id=prj_id).count()
            for testaction in TestAction.objects.filter(project__id=prj_id)[start_index: page_size+start_index]:
                records.append({
                    'testaction_id': testaction.id,
                    'testaction_name': testaction.name,
                })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_testaction_create(request):
    print("request testaction create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                testaction_name = request.POST.get('testaction_name', None)
                if testaction_name:
                    target_testaction = TestAction.objects.filter(project=target_prj, name=testaction_name)
                    if not target_testaction:
                        try:
                            target_testaction = TestAction.objects.create(
                                project=target_prj,
                                name=testaction_name,
                            )
                            record = {
                                'testaction_id': target_testaction.id,
                                'testaction_name': target_testaction.name,
                            }
                        except Exception as err:
                            message = "Save TestAction {} in Project {} failed: {}!".format(testaction_name, target_prj.name, err)
                    else:
                        message = 'TestAction {} has already existed!'.format(testaction_name)
                else:
                    message = 'Lack necessary arguement: testaction name!'
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_testaction_update(request):
    print("request testaction update:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testaction_id = request.POST.get('testaction_id', None)
        if testaction_id:
            target_testaction = None
            try:
                target_testaction = TestAction.objects.get(id=testaction_id)
            except Exception as err:
                message = "Failed to get TestAction with id {}: {}!".format(testaction_id, err)
            if target_testaction:
                is_set = False
                for attr in ('testaction_name', ):
                    attr_val = request.POST.get(attr, None)
                    if attr_val is not None:
                        attr_name = attr[11:]
                        orig_val = getattr(target_testaction, attr_name, None)
                        if orig_val != attr_val:
                            setattr(target_testaction, attr_name, attr_val)
                            is_set = True
                if is_set:
                    try:
                        target_testaction.save()
                    except Exception as err:
                        message = "Save TestAction {} failed: {}!".format(target_testaction.version, err)
                    print("Change testaction, save {}!".format(target_testaction.name))
                else:
                    print("Not change TestAction, don't save!")
        else:
            message = 'Lack necessary arguement: testaction id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_testaction_delete(request):
    print("request testaction delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testaction_id = request.POST.get('testaction_id', None)
        if testaction_id:
            target_testaction = None
            try:
                target_testaction = TestAction.objects.get(id=testaction_id)
            except Exception as err:
                message = "Failed to get TestAction with id {}: {}!".format(testaction_id, err)
            if target_testaction:
                try:
                    target_testaction.delete()
                except Exception as err:
                    message = "Delete TestAction {} failed: {}!".format(target_testaction.name, err)
        else:
            message = 'Lack necessary arguement: testaction id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})
#build
def ajax_build_list(request):
    print("request build list:" + repr(request))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('prj_id', None)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                running_build_id = target_prj.attr('running_build')
                total_count = Build.objects.filter(project=target_prj).count()
                for bld in Build.objects.filter(project=target_prj).order_by('-create')[start_index: page_size+start_index]:
                    records.append({
                        'build_id': bld.id,
                        'running_build_id': running_build_id,
                        'build_version': bld.version,
                        'build_short_name': bld.short_name,
                        'build_is_stop': 'true' if bld.is_stop else 'false',
                        'build_server_path': bld.server_path,
                        'build_local_path': bld.local_path,
                        'build_crash_path': bld.crash_path,
                        'build_test_hours': bld.test_hours,
                        'build_use_server': 'true' if bld.use_server else 'false',
                        'crash_num': calc_crash_num(build=bld),
                        'create_time': timezone.localtime(bld.create).strftime("%Y-%m-%d %H:%M:%S") if bld.create else None,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_build_create(request):
    print("request build create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
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
                                server_path=request.POST.get('build_server_path', ''),
                                local_path=request.POST.get('build_local_path', ''),
                                crash_path=request.POST.get('build_crash_path', ''),
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
                                'create_time': timezone.localtime(target_build.create).strftime("%Y-%m-%d %H:%M:%S") if target_build.create else None,
                            }
                            target_prj.attr('running_build', target_build.id)
                            target_prj.save()
                        except Exception as err:
                            message = "Save Build {} in Project {} failed: {}!".format(build_version, target_prj.name, err)
                    else:
                        message = 'Build {} has already existed!'.format(build_version)
                else:
                    message = 'Lack necessary arguement: build version!'
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_build_update(request):
    print("request build update:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = None
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
            if target_build:
                is_set = False
                for attr in ('build_server_path', 'build_local_path', 'build_crash_path', 'build_test_hours',
                             'build_use_server', 'build_is_stop', 'build_short_name', 'build_version'):
                    attr_val = request.POST.get(attr, None)
                    if attr == 'build_use_server' or attr == 'build_is_stop':
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
                    print("Change build, save {}!".format(target_build.version))
                else:
                    print("Not change build, don't save!")
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
    print("request build delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = None
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
            if target_build:
                try:
                    target_build.delete()
                except Exception as err:
                    message = "Delete Build {} failed: {}!".format(target_build.version, err)
        else:
            message = 'Lack necessary arguement: build id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})
#host
def ajax_host_list(request):
    print("request host list:" + repr(request.POST))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        target_build = None
        if build_id:
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                total_count = Host.objects.filter(project=target_prj).count()
                for host in Host.objects.filter(project=target_prj).order_by('name')[start_index: page_size+start_index]:
                    if target_build:
                        crash_num = calc_crash_num(host=host, build=target_build)
                        print("crash num {}, in host {} build {}!".format(crash_num, host.name, target_build.version))
                    else:
                        crash_num = calc_crash_num(host=host)
                        print("crash num {}, in host {}!".format(crash_num, host.name))
                    records.append({
                        'host_id': host.id,
                        'host_name': host.name,
                        'host_ip': host.ip,
                        'host_mac': host.mac,
                        'crash_num': crash_num,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_host_create(request):
    print("request build create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
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
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_host_update(request):
    print("request host update:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        host_id = request.POST.get('host_id', None)
        if host_id:
            target_host = None
            try:
                target_host = Host.objects.get(id=host_id)
            except Exception as err:
                message = "Failed to get Host with id {}: {}!".format(host_id, err)
            if target_host:
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
                        print("Change Host, save {}!".format(target_host.name))
                    else:
                        print("Not change host, don't save!")
        else:
            message = 'Lack necessary arguement: host id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_host_delete(request):
    print("request host delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        host_id = request.POST.get('host_id', None)
        if host_id:
            target_host = None
            try:
                target_host = Host.objects.get(id=host_id)
            except Exception as err:
                message = "Failed to get Host with id {}: {}!".format(host_id, err)
            if target_host:
                if target_host.is_default:
                    message = "Default host {} cannot be deleted!".format(target_host.name)
                else:
                    try:
                        target_host.delete()
                    except Exception as err:
                        message = "Delete Host {} failed: {}!".format(target_host.name, err)
        else:
            message = 'Lack necessary arguement: host id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})
#testcase
def ajax_testcase_list(request):
    print("request testcase list:" + repr(request.POST))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        target_build = None
        if build_id:
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                total_count = TestCase.objects.filter(project=target_prj).count()
                testcase_testactions = []
                for testaction in TestAction.objects.filter(project=target_prj):
                    testcase_testactions.append({
                        'Value': testaction.id,
                        'DisplayText': testaction.name
                    })
                for tc in TestCase.objects.filter(project=target_prj).order_by('name')[start_index: page_size+start_index]:
                    if target_build:
                        crash_num = calc_crash_num(testcase=tc, build=target_build)
                        print("crash num {}, in testcase {} build {}!".format(crash_num, tc.name, target_build.version))
                    else:
                        crash_num = calc_crash_num(testcase=tc)
                        print("crash num {}, in testcase {}!".format(crash_num, tc.name))
                    testcase_testaction_values = []
                    for tc_ta in tc.testactions.all():
                        testcase_testaction_values.append(tc_ta.id)
                    records.append({
                        'testcase_id': tc.id,
                        'testcase_name': tc.name,
                        'testcase_platform': tc.platform,
                        'crash_num': crash_num,
                        'testcase_testactions': {
                            'Options': testcase_testactions,
                            'Values': testcase_testaction_values,
                        },
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_testcase_create(request):
    print("request testcase create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                testcase_name = request.POST.get('testcase_name', None)
                testcase_platform = request.POST.get('testcase_platform', None)
                user_testactions_id = [int(ta_id) for ta_id in request.POST.getlist('testcase_testactions', [])]
                print("user: " + repr(user_testactions_id))
                all_testactions = TestAction.objects.filter(project=target_prj)
                try:
                    target_testcase = TestCase.objects.create(project=target_prj, name=testcase_name, platform=testcase_platform)
                    record = {
                        'id': target_testcase.id,
                        'name': target_testcase.name,
                        'platform': target_testcase.platform,
                        'crash_num': 0,
                    }
                    for ta in all_testactions:
                        if ta.id in user_testactions_id:
                            target_testcase.testactions.add(ta)
                except Exception as err:
                    message = "Save TestCase {} failed: {}!".format(testcase_name, err)
        else:
            message = 'Lack necessary arguement: project id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK', "Record": record})

def ajax_testcase_update(request):
    print("request testcase update:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testcase_id = request.POST.get('testcase_id', None)
        if testcase_id:
            target_testcase = None
            try:
                target_testcase = TestCase.objects.get(id=testcase_id)
            except Exception as err:
                message = "Failed to get TestCase with id {}: {}!".format(testcase_id, err)
            if target_testcase:
                if target_testcase.is_default:
                    message = "Default testcase {} cannot be edited!".format(target_testcase.name)
                else:
                    is_set = False
                    user_testactions_id = sorted([int(ta_id) for ta_id in request.POST.getlist('testcase_testactions', [])])
                    orig_testactions_id = sorted([ta.id for ta in target_testcase.testactions.all()])
                    print("origin: " + repr(orig_testactions_id))
                    print("user: " + repr(user_testactions_id))
                    all_testactions = TestAction.objects.filter(project=target_testcase.project)
                    if user_testactions_id != orig_testactions_id:
                        is_set = True
                        target_testcase.testactions.clear()
                        for ta in all_testactions:
                            if ta.id in user_testactions_id:
                                target_testcase.testactions.add(ta)
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
                        print("Change TestCase, save {}!".format(target_testcase.name))
                    else:
                        print("Not change TestCase, don't save!")
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
    print("request testcase delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testcase_id = request.POST.get('testcase_id', None)
        if testcase_id:
            target_testcase = None
            try:
                target_testcase = TestCase.objects.get(id=testcase_id)
            except Exception as err:
                message = "Failed to get TestCase with id {}: {}!".format(testcase_id, err)
            if target_testcase:
                if target_testcase.is_default:
                    message = "Default testcase {} cannot be deleted!".format(target_testcase.name)
                else:
                    try:
                        target_testcase.delete()
                    except Exception as err:
                        message = "Delete TestCase {} failed: {}!".format(target_testcase.name, err)
        else:
            message = 'Lack necessary arguement: testcase id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})
#crash
def ajax_crash_list(request):
    print("request crash list:" + repr(request.POST))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        testcase_id = request.POST.get('testcase_id', None)
        host_id = request.POST.get('host_id', None)
        target_build = None; target_testcase = None; target_host = None
        if build_id:
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
        if testcase_id:
            try:
                target_testcase = TestCase.objects.get(id=testcase_id)
            except Exception as err:
                message = "Failed to get TestCase with id {}: {}!".format(testcase_id, err)
        if host_id:
            try:
                target_host = Host.objects.get(id=host_id)
            except Exception as err:
                message = "Failed to get Host with id {}: {}!".format(host_id, err)
        if prj_id:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                user_filter = {}
                if target_build:
                    user_filter['build'] = target_build
                else:
                    user_filter['build__project'] = target_prj
                if target_host:
                    user_filter['host'] = target_host
                if target_testcase:
                    user_filter['testcase'] = target_testcase
                crashes = Crash.objects.filter(**user_filter).order_by('-create')[start_index: page_size+start_index]
                total_count = Crash.objects.filter(**user_filter).count()
                print("crash num {}, in {}!".format(total_count, user_filter.keys()))
                for crash in crashes:
                    records.append({
                        'crash_id': crash.id,
                        'crash_path': crash.path,
                        'build_id': crash.build.id,
                        'host_id': crash.host.id,
                        'testcase_id': crash.testcase.id,
                        'jira_id': crash.jira.jira_id,
                        'jira_category': crash.jira.category,
                        'create_time': timezone.localtime(crash.create).strftime("%Y-%m-%d %H:%M:%S") if crash.create else None,
                    })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_crash_create(request):
    print("request crash create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = None
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
            if target_build:
                target_host = None
                target_testcase = None
                target_jira = None
                crash_path = request.POST.get('crash_path', None)
                host_id = request.POST.get('host_id', None)
                testcase_id = request.POST.get('testcase_id', None)
                jira_id = request.POST.get('jira_id', None)
                try:
                    if host_id:
                        target_host = Host.objects.get(id=host_id)
                    else:
                        target_host = Host.objects.get(is_default=True, project=target_build.project)
                except Exception as err:
                    message = "Failed to get Host: id {}: {}!".format(host_id, err)
                try:
                    if testcase_id:
                        target_testcase = TestCase.objects.get(id=testcase_id)
                    else:
                        target_testcase = TestCase.objects.get(is_default=True, project=target_build.project)
                except Exception as err:
                    message = "Failed to get TestCase: id {}: {}!".format(testcase_id, err)
                if jira_id:
                    try:
                        target_jira, created = JIRA.objects.get_or_create(jira_id=jira_id)
                    except Exception as err:
                        message = "Failed to create JIRA by jira id {}: {}".format(jira_id, err)
                if not target_jira:
                    try:
                        target_jira = JIRA.objects.get(is_default=True)
                    except Exception as err:
                        message = "Failed to get default JIRA: {}".format(err)
                if not message:
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
    print("request crash delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        crash_id = request.POST.get('crash_id', None)
        if crash_id:
            target_crash = None
            try:
                target_crash = Crash.objects.get(id=crash_id)
            except Exception as err:
                message = "Failed to get Crash with id {}: {}!".format(crash_id, err)
            if target_crash:
                try:
                    target_crash.delete()
                except Exception as err:
                    message = "Delete Crash {} failed: {}!".format(target_crash.path, err)
        else:
            message = 'Lack necessary arguement: Crash id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_crash_update(request):
    print("request crash create:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        crash_id = request.POST.get('crash_id', None)
        if crash_id:
            target_crash = None
            try:
                target_crash = Crash.objects.get(id=crash_id)
            except Exception as err:
                message = "Failed to get Crash with id {}: {}!".format(crash_id, err)
            if target_crash:
                is_set = False
                build_id = request.POST.get('build_id', None)
                host_id = request.POST.get('host_id', None)
                testcase_id = request.POST.get('testcase_id', None)
                jira_id = request.POST.get('jira_id', None)
                if target_crash.build and build_id != target_crash.build.id:
                    target_build = None
                    try:
                        target_build = Build.objects.get(id=build_id)
                    except Exception as err:
                        message = "Failed to get Build with id {}: {}!".format(build_id, err)
                    if target_build:
                        target_crash.build = target_build
                        is_set = True
                if target_crash.host and host_id != target_crash.host.id:
                    target_host = None
                    try:
                        target_host = Host.objects.get(id=host_id)
                    except Exception as err:
                        message = "Failed to get Host with id {}: {}!".format(host_id, err)
                    if target_host:
                        target_crash.host = target_host
                        is_set = True
                if target_crash.testcase and testcase_id != target_crash.testcase.id:
                    try:
                        target_testcase = TestCase.objects.get(id=testcase_id)
                    except Exception as err:
                        message = "Failed to get TestCase with id {}: {}!".format(testcase_id, err)
                    if target_testcase:
                        target_crash.testcase = target_testcase
                        is_set = True
                if jira_id != target_crash.jira_id:
                    try:
                        target_jira, created = JIRA.objects.get_or_create(jira_id=jira_id)
                    except Exception as err:
                        print("Failed to get/create JIRA by jira id {}: {}".format(jira_id, err))
                    if target_jira:
                        target_crash.jira = target_jira
                        is_set = True
                for attr in ('crash_path',):
                    attr_val = request.POST.get(attr, None)
                    if attr_val is not None:
                        attr_name = attr[6:]
                        orig_val = getattr(target_crash, attr_name, None)
                        #print("set {} from {} to {}!".format(attr_name, orig_val, attr_val))
                        if orig_val != attr_val:
                            setattr(target_crash, attr_name, attr_val)
                            is_set = True
                if is_set:
                    try:
                        target_crash.save()
                    except Exception as err:
                        message = "Save Crash {} failed: {}!".format(target_crash.path, err)
                    print("Change Crash, save {}!".format(target_crash.path))
                else:
                    print("Not change Crash, don't save!")
            else:
                message = 'Crash id {} does NOT exist!'.format(crash_id)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

#testresult
def ajax_testresult_list(request):
    print("request testresult list:" + repr(request.POST))
    records = []
    total_count = 0
    if request.method == 'POST':
        prj_id = request.POST.get('prj_id', None)
        build_id = request.POST.get('build_id', None)
        host_id = request.POST.get('host_id', None)
        target_prj = None; target_build = None; target_host = None
        if build_id:
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
        if host_id:
            try:
                target_host = Host.objects.get(id=host_id)
            except Exception as err:
                message = "Failed to get Host with id {}: {}!".format(host_id, err)
        if (not target_build) and prj_id:
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
        if target_prj or target_build:
            start_index = int(request.GET.get('jtStartIndex', 0))
            page_size = int(request.GET.get('jtPageSize', 20))
            user_filter = {}
            if target_build:
                user_filter['build'] = target_build
                target_prj = target_build.project
            else:
                user_filter['build__project'] = target_prj
            if target_host:
                user_filter['host'] = target_host
            testresults = TestResult.objects.filter(**user_filter)
            all_ta = TestAction.objects.filter(project=target_prj).order_by('name')[start_index: page_size+start_index]
            total_count = TestAction.objects.filter(project=target_prj).count()
            for ta in all_ta:
                pass_count = 0
                fail_count = 0
                last_update = None
                tr_id = 0
                for tr in testresults:
                    if tr.testaction.id == ta.id:
                        if target_build and target_host:
                            tr_id = tr.id
                        pass_count += tr.pass_count
                        fail_count += tr.fail_count
                        if (not last_update) or last_update < tr.last_update:
                            last_update = tr.last_update
                records.append({
                    'testresult_id': tr_id,
                    'testresult_pass_count': pass_count,
                    'testresult_fail_count': fail_count,
                    'testaction_id': ta.id,
                    'build_id': build_id,
                    'host_id': host_id,
                    'last_update': timezone.localtime(last_update).strftime("%Y-%m-%d %H:%M:%S") if last_update else None,
                })
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def ajax_testresult_create(request):
    print("request testresult create:" + repr(request.POST))
    message = None
    record = None
    if request.method == 'POST':
        build_id = request.POST.get('build_id', None)
        if build_id:
            target_build = None
            try:
                target_build = Build.objects.get(id=build_id)
            except Exception as err:
                message = "Failed to get Build with id {}: {}!".format(build_id, err)
            if target_build:
                target_host = None
                target_testaction = None
                testresult_fail_count = request.POST.get('testresult_fail_count', None)
                testresult_pass_count = request.POST.get('testresult_pass_count', None)
                testaction_id = request.POST.get('testaction_id', None)
                host_id = request.POST.get('host_id', None)
                try:
                    if host_id:
                        target_host = Host.objects.get(id=host_id)
                    else:
                        target_host = Host.objects.get(is_default=True, project=target_build.project)
                except Exception as err:
                    message = "Failed to get Host: id {}: {}!".format(host_id, err)
                try:
                    if testaction_id:
                        target_testaction = TestAction.objects.get(id=testaction_id)
                    else:
                        target_testaction = TestAction.objects.get(is_default=True, project=target_build.project)
                except Exception as err:
                    message = "Failed to get TestAction: id {}: {}!".format(testaction_id, err)
                if not message:
                    try:
                        target_testresult = TestResult.objects.create(build=target_build, pass_count=testresult_pass_count, fail_count=testresult_fail_count, host=target_host, testaction=target_testaction)
                        record = {
                            'id': target_testresult.id,
                            'testresult_pass_count': target_testresult.pass_count,
                            'testresult_fail_count': target_testresult.fail_count,
                            'host_id': target_testresult.host.id,
                            'testaction_id': target_testresult.testaction.id,
                            'build_id': target_testresult.build.id,
                        }
                    except Exception as err:
                        message = "Save TestResult failed: {}!".format(err)
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

def ajax_testresult_delete(request):
    print("request testresult delete:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testresult_id = request.POST.get('testresult_id', None)
        if testresult_id:
            target_testresult = None
            try:
                target_testresult = TestResult.objects.get(id=testresult_id)
            except Exception as err:
                message = "Failed to get TestResult with id {}: {}!".format(testresult_id, err)
            if target_testresult:
                try:
                    target_testresult.delete()
                except Exception as err:
                    message = "Delete TestResult failed: {}!".format(target_testresult.id, err)
        else:
            message = 'Lack necessary arguement: TestResult id!'
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

def ajax_testresult_update(request):
    print("request testresult create:" + repr(request.POST))
    message = None
    if request.method == 'POST':
        testresult_id = request.POST.get('testresult_id', None)
        if testresult_id:
            target_testresult = None
            try:
                target_testresult = TestResult.objects.get(id=testresult_id)
            except Exception as err:
                message = "Failed to get TestResult with id {}: {}!".format(testresult_id, err)
            if target_testresult:
                is_set = False
                build_id = request.POST.get('build_id', None)
                host_id = request.POST.get('host_id', None)
                testaction_id = request.POST.get('testaction_id', None)
                if target_testresult.build and build_id != target_testresult.build.id:
                    target_build = None
                    try:
                        target_build = Build.objects.get(id=build_id)
                    except Exception as err:
                        message = "Failed to get Build with id {}: {}!".format(build_id, err)
                    if target_build:
                        target_testresult.build = target_build
                        is_set = True
                if target_testresult.host and host_id != target_testresult.host.id:
                    target_host = None
                    try:
                        target_host = Host.objects.get(id=host_id)
                    except Exception as err:
                        message = "Failed to get Host with id {}: {}!".format(host_id, err)
                    if target_host:
                        target_testresult.host = target_host
                        is_set = True
                if target_testresult.testaction and testaction_id != target_testresult.testaction.id:
                    try:
                        target_testaction = TestAction.objects.get(id=testaction_id)
                    except Exception as err:
                        message = "Failed to get TestAction with id {}: {}!".format(testaction_id, err)
                    if target_testaction:
                        target_testresult.testaction = target_testaction
                        is_set = True
                for attr in ('testresult_pass_count', 'testresult_fail_count'):
                    attr_val = request.POST.get(attr, None)
                    if attr_val is not None:
                        attr_name = attr[11:]
                        orig_val = getattr(target_testresult, attr_name, None)
                        #print("set {} from {} to {}!".format(attr_name, orig_val, attr_val))
                        if orig_val != attr_val:
                            setattr(target_testresult, attr_name, attr_val)
                            is_set = True
                if is_set:
                    try:
                        target_testresult.save()
                    except Exception as err:
                        message = "Save TestResult id {} failed: {}!".format(target_testresult.id, err)
                    print("Change TestResult, save with id {}!".format(target_testresult.id))
                else:
                    print("Not change TestResult, don't save!")
            else:
                message = 'Testresult id {} does NOT exist!'.format(testresult_id)
    else:
        message = "Incorrect request method: {}, only support POST now!".format(request.method)
    if message:
        return JsonResponse({'Result': 'ERROR', 'Message': message})
    else:
        return JsonResponse({'Result': 'OK'})

#list_options
def ajax_list_options_testactions_in_project(request):
    print(request.POST)
    options = []
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                for testaction in TestAction.objects.filter(project=target_prj).order_by('name'):
                    options.append({
                        "DisplayText": str(testaction.name),
                        "Value": testaction.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_list_options_builds_in_project(request):
    print(request.POST)
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
                for bld in Build.objects.filter(project=target_prj, is_stop=False).order_by('-create'):
                    options.append({
                        "DisplayText": bld.short_name,
                        "Value": bld.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_list_options_hosts_in_project(request):
    print(request.POST)
    options = []
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                for host in Host.objects.filter(project=target_prj).order_by('name'):
                    options.append({
                        "DisplayText": host.name,
                        "Value": host.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_list_options_testcases_in_project(request):
    print(request.POST)
    options = []
    if request.method == 'POST':
        prj_id = request.GET.get('prj_id', None)
        if prj_id:
            target_prj = None
            try:
                target_prj = Project.objects.get(id=prj_id)
            except Exception as err:
                message = "Failed to get project with id {}: {}!".format(prj_id, err)
            if target_prj:
                for tc in TestCase.objects.filter(project=target_prj).order_by('name'):
                    options.append({
                        "DisplayText": tc.name,
                        "Value": tc.id
                    })
    return JsonResponse({'Result': 'OK', 'Options': options})

def ajax_issue_frequency_result(request):
    err_code = None
    msg = None
    if request.method == 'POST':
        print(request.POST)
        issue_id = request.POST.get('issue_id', None)
        if issue_id:
            cached_result = get_cached_issue_frequency(issue_id) #check_result default is False, it might get pending result
            msg = {'done': 0, 'result': None, 'life_time': 0}
            if cached_result:
                result = cached_result.get('result', None)
                exception = cached_result.get('exception', None)
                if result:
                    life_time = time.time() - cached_result['update_at']
                    msg['done'] = 1
                    msg['result'] = result
                    msg['life_time'] = seconds_to_humanable(life_time)
                elif exception:
                    life_time = time.time() - cached_result['update_at']
                    msg['done'] = 1
                    msg['exception'] = exception
                    msg['life_time'] = seconds_to_humanable(life_time)
                else:
                    msg['result'] = "querying for {}...".format(seconds_to_humanable(time.time() - cached_result['start_at']))
                    AsyncResult
            else:
                err_code = -3
                msg = "not found this issue_id {} in the queue, illeagel request?!".format(issue_id)
        else:
            err_code = -2
            msg = "no issue_id in the request!"
    else:
        err_code = -1
        msg = "not support request method: {}!".format(request.method)
    return json_response(msg, err_code)

def ajax_ping_results(request):
    err_code = None
    msg = None
    if request.method == 'POST':
        ping_result = celery_app.control.ping()
        print("Ping result: {}".format(ping_result))
        err_code = 0
        msg = ping_result
    return json_response(msg, err_code)

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

def auto_project_info(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        prj_name = request.POST.get('project_name', None)
        prj_owner = request.POST.get('project_owner', None)
        prj_is_stop = request.POST.get('project_is_stop', None)
        prj_is_stop = True if prj_is_stop and ( prj_is_stop == '1' or prj_is_stop.lower() == 'true' ) else False
        if prj_name:
            target_prj = None
            try:
                target_prj = Project.objects.get(name=prj_name)
            except Exception as err:
                pass
            if target_prj:
                changed = False
                if prj_owner and target_prj.owner != prj_owner:
                    target_prj.owner = prj_owner
                    changed = True
                if prj_is_stop != target_prj.is_stop:
                    target_prj.is_stop = prj_is_stop
                    changed = True
                if changed:
                    try:
                        target_prj.save()
                        msg = 'Project {} has changed!'.format(prj_name)
                    except Exception as err:
                        msg = 'Chnage Project {} failed!'.format(prj_name)
                        err_code = -1
                else:
                    msg = 'Project {} no change!'.format(prj_name)
            else:
                try:
                    target_prj = Project.objects.create(name=prj_name, owner=prj_owner, is_stop=prj_is_stop)
                    msg = 'Project {} has created!'.format(prj_name)
                except Exception as err:
                    msg = "Create Project {} failed: {}!".format(prj_name, err)
                    err_code = -1
                set_default_result = set_default_records(project=target_prj, set_testcase=True, set_host=True, set_testaction=True)
                if set_default_result:
                    msg = "Failed to create related default host/testcase for project {}: {}!".format(prj_name, set_default_result)
        else:
            err_code = -1
            msg = "Need necessary argument: project_name!"
    else:
        err_code = -1
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
    return json_response(msg, err_code)

def auto_build_info(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        prj_name = request.POST.get('project_name', None)
        if prj_name:
            target_prj = None
            try:
                target_prj = Project.objects.get(name=prj_name)
            except Exception as err:
                msg = "Failed to get Project {}: {}".format(prj_name, err)
            if target_prj:
                build_version = request.POST.get('build_version', None)
                if build_version:
                    target_build = None
                    try:
                        target_build = Build.objects.get(project=target_prj, version=build_version)
                    except Exception as err:
                        pass
                    if target_build:
                        is_set = False
                        for attr in ('build_server_path', 'build_local_path', 'build_crash_path', 'build_test_hours',
                                     'build_use_server', 'build_is_stop', 'build_short_name', 'build_version'):
                            attr_val = request.POST.get(attr, None)
                            if attr == 'build_use_server' or attr == 'build_is_stop':
                                attr_val = True if attr_val and (attr_val.lower() == 'true' or attr_val.lower() == '1') else False
                            if attr_val is not None:
                                attr_name = attr[6:]
                                orig_val = getattr(target_build, attr_name, None)
                                if str(orig_val) != str(attr_val):
                                    #print("attr name {}: {}={}".format(attr, orig_val, attr_val))
                                    setattr(target_build, attr_name, attr_val)
                                    is_set = True
                        if is_set:
                            try:
                                target_build.save()
                                msg = "Build {} changed!".format(build_version)
                            except Exception as err:
                                msg = "Change Build {} failed: {}!".format(build_version, err)
                                err_code = -1
                        else:
                            msg = "Build {} has no changed!".format(build_version)
                    else:
                        use_server = request.POST.get('build_use_server', None)
                        use_server = True if use_server and (use_server == 'true' or use_server == '1') else False
                        test_hour = request.POST.get('build_test_hours', 0)
                        if not test_hour:
                            test_hour = 0
                        try:
                            target_build = Build.objects.create(
                                project=target_prj,
                                version=build_version,
                                short_name=request.POST.get('build_short_name', build_version),
                                server_path=request.POST.get('build_server_path', ''),
                                local_path=request.POST.get('build_local_path', ''),
                                crash_path=request.POST.get('build_crash_path', ''),
                                test_hours=test_hour,
                                use_server=use_server,
                            )
                            msg = 'Build {} has created!'.format(build_version)
                            target_prj.attr('running_build', target_build.id)
                            target_prj.save()
                        except Exception as err:
                            msg = "Create Build {} failed: {}!".format(build_version, err)
                            err_code = -1
                else:
                    msg = "Need necessary argument: build_version!"
                    err_code = -1
            else:
                msg = "Cannot find Project {}!".format(prj_name)
                err_code = -1
        else:
            msg = "Need necessary argument: project_name!"
            err_code = -1
    else:
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
        err_code = -1
    return json_response(msg, err_code)

def auto_query_project(request):
    err_code = None
    msg = None
    if request.method == 'POST':
        print(request.POST)
        projects = Project.objects.filter(is_stop=False).order_by('-create')
        msg = []
        err_code = 0
        for prj in projects:
            msg.append({
                'id': prj.id,
                'name': prj.name,
                'owner': prj.owner,
            })
    return json_response(msg, err_code)

def auto_query_build(request):
    err_code = None
    msg = None
    if request.method == 'POST':
        print(request.POST)
        prj_name = request.POST.get('project_name', None)
        builds = Build.objects.filter(project__name=prj_name, is_stop=False).order_by('-create')
        msg = []
        err_code = 0
        for bld in builds:
            msg.append({
                'id': bld.id,
                'version': bld.version,
                'name': bld.short_name,
                'server_path': bld.server_path,
                'local_path': bld.local_path,
                'crash_path': bld.crash_path,
                'use_server': bld.use_server,
            })
    return json_response(msg, err_code)

def auto_crash_info(request):
    err_code = 0
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
        if path and prj_name and build_version:
            build = None
            try:
                build = Build.objects.get(project__name=prj_name, version=build_version)
            except Exception as err:
                err_code = -1
                msg = "Failed to get build {} in project {}: {}".format(prj_name, build_version, err)
            if build:
                try:
                    if host_name:
                        try:
                            host = Host.objects.get(project=build.project, name=host_name)
                        except Exception as err:
                            host = Host.objects.create(project=build.project, name=host_name, ip=host_ip, mac=host_mac)
                    else:
                        host = Host.objects.get(is_default=True, project=build.project)
                except Exception as err:
                    err_code = -1
                    msg = "Failed to get/create Host with name {}: {}!".format(host_name, err)
                    return json_response(msg, err_code)
                try:
                    if tc_name:
                        try:
                            testcase = TestCase.objects.get(project=build.project, name=tc_name)
                        except Exception as err:
                            testcase = TestCase.objects.create(project=build.project, name=tc_name, platform=tc_platform)
                    else:
                        testcase = TestCase.objects.get(is_default=True, project=build.project)
                except Exception as err:
                    err_code = -1
                    msg = "Failed to get/create TestCase with name {}: {}!".format(tc_name, err)
                    return json_response(msg, err_code)
                try:
                    if jira_id:
                        try:
                            jira = JIRA.objects.get(jira_id=jira_id)
                        except Exception as err:
                            jira = JIRA.objects.create(is_default=False, jira_id=jira_id, category=JIRA.OPEN)
                    else:
                        jira = JIRA.objects.get(is_default=True)
                except Exception as err:
                    err_code = -1
                    msg = "Failed to get/create JIRA with jira_id {}: {}!".format(jira_id, err)
                    return json_response(msg, err_code)
                try:
                    changed = False
                    need_change = False
                    try:
                        crash = Crash.objects.get(path=path)
                        need_change = True
                    except Exception as err:
                        crash = Crash.objects.create(path=path, build=build, host=host, testcase=testcase, jira=jira)
                        msg = "Create crash done!"
                    if need_change:
                        for attr in ('build', 'jira', 'host', 'testcase'):
                            val = locals().get(attr, None)
                            if hasattr(crash, attr) and val and getattr(crash, attr) != val:
                                setattr(crash, attr, val)
                                print("attr name {}: {}={}".format(attr, getattr(crash, attr), val))
                                changed = True
                        if changed:
                            crash.save()
                            msg = "Crash changed!"
                        else:
                            msg = "Crash no change!"
                except Exception as err:
                    msg = "Failed to change/create crash record: {}".format(err)
                    err_code = -1
            else:
                msg = "Not found build {}!".format(build_version)
                err_code = -1
        else:
            msg = "Need necessary arguments when auto create crash!"
            err_code = -1
    return json_response(msg, err_code)

def auto_testaction_info(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        prj_name = request.POST.get('project_name', None)
        #prj_owner = request.POST.get('project_owner', '')
        #build_version = request.POST.get('build_version', None)
        ta_name = request.POST.get('ta_name', None)
        is_pass = request.POST.get('is_pass', None)
        count = request.POST.get('count', 1)
        try:
            count = int(count)
        except Exception as err:
            log.error("Failed to transform count {} into integer: {}, so set default count=1!".format(count, err))
            count = 1
        is_pass = True if is_pass and (is_pass == '1' or is_pass.lower() == 'true') else False
        host_name = request.POST.get('host_name', None)
        host_ip = request.POST.get('host_ip', '')
        host_mac = request.POST.get('host_mac', '')
        if ta_name and prj_name and host_name:
            project = None
            build = None
            running_build_id = None
            try:
                project = Project.objects.get(name=prj_name)
            except Exception as err:
                err_code = -1
                msg = "Failed to get Project {}: {}".format(prj_name, err)
            if project:
                running_build_id = project.attr('running_build')
            if running_build_id:
                try:
                    build = Build.objects.get(id=running_build_id)
                except Exception as err:
                    err_code = -1
                    msg = "Failed to get running build with id {} in Project {}: {}".format(running_build_id, prj_name, err)
            if build:
                try:
                    host = None
                    try:
                        host = Host.objects.get(project=project, name=host_name)
                    except Exception as err:
                        host = Host.objects.create(project=project, name=host_name, ip=host_ip, mac=host_mac)
                    testaction = None
                    testresult = None
                    if ta_name:
                        testaction, created = TestAction.objects.get_or_create(name=ta_name, project=project)
                    if host and testaction:
                        if is_pass:
                            testtime=record_test_time(test_build =build,test_dut = host,actionpass=True,test_date = str(datetime.date.today()))
                        else:
                            testtime=record_test_time(test_build =build,test_dut = host,actionfail=True,test_date = str(datetime.date.today()))
                        try:
                            testresult = TestResult.objects.get(testaction=testaction, build=build, host=host)
                        except Exception as err:
                            testresult = TestResult.objects.create(testaction=testaction, build=build, host=host, pass_count=0, fail_count=0)
                    if testresult:
                        if is_pass:
                            testresult.pass_count += count
                            msg = "Add {} pass to {} in build {}!".format(ta_name, testresult.pass_count, build.version)
                        else:
                            testresult.fail_count += count
                            msg = "Add {} fail to {} in build {}!".format(ta_name, testresult.fail_count, build.version)
                        testresult.save()
                    else:
                        err_code = -1
                        msg = "Failed to set test result: TA={} is_pass: {} in build {} with unknown reason!".format(ta_name, is_pass, build.version)
                except Exception as err:
                    msg = "Failed to set test result: TA={} is_pass: {} in build {}: {}".format(ta_name, is_pass, build.version, err)
                    err_code = -1
                    return json_response(msg, err_code)
                return json_response(msg, err_code)
            else:
                return json_response("Not found running build in project {}!".format(prj_name), -1)
        else:
            return json_response("Need necessary arguments when auto update action: TA={}, Project={}, Host={}!".format(ta_name, prj_name, host_name), -1)
    return json_response(msg, err_code)

def auto_get_jira(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        start_id = request.POST.get('start_id', 0)
        length = request.POST.get('length', 100)
        try:
            start_id = int(start_id)
            length = int(length)
        except Exception as err:
            err_code = -1
            msg = "start_id({!r})/length({!r}) is not integer: {}!".format(start_id, length, err)
        if not err_code:
            jiras = JIRA.objects.filter(is_default=False, category=JIRA.OPEN, id__gt=start_id)[0:length]
            msg = [{'id': jira.id, 'jira': jira.jira_id, 'cr': jira.cr_id, 'category': JIRA.OPEN} for jira in jiras]
    else:
        err_code = -1
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
    return json_response(msg, err_code)

def auto_get_running_jira(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        project_name = request.POST.get('project_name', None)
        project_id = request.POST.get('project_id', None)
        if not (project_name or project_id):
            err_code = -1
            msg = "no project name or project id when query running build JIRA!"
        if not err_code:
            user_filter = {}
            if project_id:
                user_filter['id'] = project_id
            elif project_name:
                user_filter['name'] = project_name
            target_prj = None
            try:
                target_prj = Project.objects.get(**user_filter)
            except Exception as err:
                err_code = -1
                msg = "Failed to get project with id {}/name {}: {}!".format(project_id, project_name, err)
            if target_prj:
                running_build_id = target_prj.attr('running_build')
                if running_build_id:
                    crashes = Crash.objects.filter(build__id=running_build_id)
                    msg = []
                    for crash in crashes:
                        if crash.jira.cr_id or (crash.jira.category in (JIRA.CNSS, JIRA.NONCNSS)):
                            msg.append({'id': crash.jira.id, 'jira': crash.jira.jira_id, 'cr': crash.jira.cr_id, 'category': crash.jira.category})
                else:
                    err_code = -1
                    msg = "No running build found in project: {}!".format(target_prj.name)
    else:
        err_code = -1
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
    return json_response(msg, err_code)

def auto_jira_info(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        jid = request.POST.get('id', None)
        jira_id = request.POST.get('jira_id', None)
        cr_id = request.POST.get('cr_id', '')
        category = request.POST.get('category', JIRA.OPEN)
        if jid:
            target_jira = None
            try:
                target_jira = JIRA.objects.get(id=jid)
            except Exception as err:
                pass
            if target_jira:
                changed = False
                if jira_id and target_jira.jira_id != jira_id:
                    target_jira.jira_id = jira_id
                    changed = True
                if cr_id and target_jira.cr_id != cr_id:
                    target_jira.cr_id = cr_id
                    changed = True
                if category != target_jira.category:
                    target_jira.category = category
                    changed = True
                if changed:
                    try:
                        target_jira.save()
                        msg = 'JIRA {}({}) has changed!'.format(jid, jira_id)
                    except Exception as err:
                        msg = 'Change JIRA {}({}) failed: {}!'.format(jid, jira_id, err)
                        err_code = -1
                else:
                    msg = 'JIRA {}({}) no change!'.format(jid, jira_id)
            else:
                msg = 'JIRA {}({}) cannot be found!'.format(jid, jira_id)
        elif jira_id:
            try:
                target_jira = JIRA.objects.create(jira_id=jira_id, category=category, cr_id=cr_id)
                msg = 'JIRA {} has created!'.format(jira_id)
            except Exception as err:
                msg = "Create JIRA {} failed: {}!".format(jira_id, err)
                err_code = -1
        else:
            err_code = -1
            msg = "Need necessary argument: JIRA id(update) or jira_id(create new)!"
    else:
        err_code = -1
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
    return json_response(msg, err_code)

def auto_task_result(request):
    err_code = 0
    msg = None
    if request.method == 'POST':
        print("auto_task_result body={}".format(request.body))
        issue_id = request.POST.get('issue_id', None)
        issue_result = request.POST.get('issue_result', None)
        assoc_issues = request.POST.get('assoc_issues', None)
        exception = request.POST.get('exception', None)
        if issue_id is not None:
            print("Got issue {} result={}".format(issue_id, issue_result))
            update_issue_frequency(issue_id, issue_result, assoc_issues, exception)
            msg = "Update cached request!"
        else:
            err_code = -2
            msg = "Not found issue id in the request!"
    else:
        err_code = -1
        msg = "Incorrect request method: {}, only support POST now!".format(request.method)
    return json_response(msg, err_code)

# Create your views here.
def home_page(request):
    return render(request, 'tbd/home.html')

def project_page(request):
    return render(request, 'tbd/project.html')

def build_page(request):
    prj_id = request.GET.get('prj_id', '')
    projects = Project.objects.filter(is_stop=False)
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
    projects = Project.objects.filter(is_stop=False)
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
            builds = Build.objects.filter(project=target_prj, is_stop=False).order_by('-create')
    return render(request, 'tbd/host.html', {'project': target_prj, 'projects': projects, 'build': target_build, 'builds': builds})

def testaction_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    projects = Project.objects.filter(is_stop=False)
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
            builds = Build.objects.filter(project=target_prj, is_stop=False).order_by('-create')
    return render(request, 'tbd/testaction.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'testcase_platform_choice': json.dumps(dict(TestCase.PLATFORM_CHOICE)),
    })

def testcase_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    projects = Project.objects.filter(is_stop=False)
    target_prj = None
    target_build = None
    builds = []
    all_testactions = []
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
            builds = Build.objects.filter(project=target_prj, is_stop=False).order_by('-create')
    if target_prj:
        all_testactions = TestAction.objects.filter(project=target_prj)
    return render(request, 'tbd/testcase.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'testcase_platform_choice': json.dumps(dict(TestCase.PLATFORM_CHOICE)),
        'all_testactions': json.dumps([{'Value': ta.id, 'DisplayText': ta.name} for ta in all_testactions]),
    })

def testresult_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    host_id = request.GET.get('host_id', '')
    projects = Project.objects.filter(is_stop=False)
    target_prj = None
    target_build = None
    target_host = None
    builds = []
    hosts = []
    if build_id:
        try:
            target_build = Build.objects.get(id=build_id)
            target_prj = target_build.project
            builds = target_prj.build_set.order_by('-create')
        except Exception as err:
            print("Failed to get Project with id {}: {}!".format(prj_id, err))
    elif prj_id:
        try:
            target_prj = Project.objects.get(id=prj_id)
            builds = Build.objects.filter(project=target_prj, is_stop=False).order_by('-create')
        except Exception as err:
            print("Failed to get Project with id {}: {}!".format(prj_id, err))
    if target_prj:
        hosts = Host.objects.filter(project=target_prj).order_by('name')
    if host_id:
        try:
            target_host = Host.objects.get(id=host_id)
        except Exception as err:
            print("Failed to get Host with id {}: {}!".format(host_id, err))
    return render(request, 'tbd/testresult.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'host': target_host, 'hosts': hosts,
    })

def crash_page(request):
    prj_id = request.GET.get('prj_id', '')
    build_id = request.GET.get('build_id', '')
    host_id = request.GET.get('host_id', '')
    testcase_id = request.GET.get('testcase_id', '')
    projects = Project.objects.filter(is_stop=False)
    target_prj = None
    target_build = None
    target_host = None
    target_testcase = None
    builds = []
    hosts = []
    testcases = []
    if build_id:
        try:
            target_build = Build.objects.get(id=build_id)
            target_prj = target_build.project
            builds = target_prj.build_set.order_by('-create')
        except Exception as err:
            print("Failed to get Project with id {}: {}!".format(prj_id, err))
    elif prj_id:
        try:
            target_prj = Project.objects.get(id=prj_id)
            builds = Build.objects.filter(project=target_prj, is_stop=False).order_by('-create')
        except Exception as err:
            print("Failed to get Project with id {}: {}!".format(prj_id, err))
    if target_prj:
        hosts = Host.objects.filter(project=target_prj).order_by('name')
        testcases = TestCase.objects.filter(project=target_prj).order_by('name')
    if host_id:
        try:
            target_host = Host.objects.get(id=host_id)
        except Exception as err:
            print("Failed to get Host with id {}: {}!".format(host_id, err))
    if testcase_id:
        try:
            target_testcase = TestCase.objects.get(id=testcase_id)
        except Exception as err:
            print("Failed to get TestCase with id {}: {}!".format(testcase_id, err))
    return render(request, 'tbd/crash.html', {
        'project': target_prj, 'projects': projects,
        'build': target_build, 'builds': builds,
        'host': target_host, 'hosts': hosts,
        'testcase': target_testcase, 'testcases': testcases,
        'jira_category_choice': json.dumps(dict(JIRA.CATEGORY_CHOICE)),
    })

def utility_page(request):
    utility_name = request.GET.get('name', None)
    support_utilities = {
        'issue_frequency': 'Issue Frequency',
        'ping_workers': 'Ping Workers',
        'test_time':'testtime',
        'get_result':'getresult',
    }
    utility_args = {'support_utilities': support_utilities}
    if utility_name == "issue_frequency":
        utility_args['utility_name'] = utility_name
        utility_template = 'tbd/utility_{}.html'.format(utility_name)
        issue_id = request.GET.get('issue_id', None)
        force_refresh = request.GET.get('force_refresh', None)
        result_url = request.build_absolute_uri(reverse('auto', args=['task_result']))
        if issue_id:
            utility_args['issue_id'] = issue_id
            query_cached_issue_frequency(issue_id, result_url, force_refresh)
    elif utility_name == "ping_workers":
        utility_args['utility_name'] = utility_name
        utility_template = 'tbd/utility_{}.html'.format(utility_name)
    elif utility_name == "test_time":
        utility_args['utility_name'] = utility_name
        utility_template = 'tbd/utility_{}.html'.format(utility_name)

        test_build = request.GET.get('testbuild', '')
        test_dut = request.GET.get('testdut', '')
        test_date = request.GET.get('testdate', '')
        if test_build:
            test_build = Build.objects.filter(version=test_build)[0]
        if test_dut:
            test_dut = Host.objects.get(name=test_dut,project=test_build.project)

        testbuilds = Build.objects.values("version").distinct()
        if test_build :
            testduts = TestTime.objects.filter(testbuild=test_build).values("testdut__name").distinct()
            if test_dut:
                testdates_array = TestTime.objects.filter(testbuild=test_build,testdut=test_dut).values("testdate").distinct()
                testdates = []
                for i in testdates_array:
                    testdates.append(str(i['testdate']))
            else:
                testdates_array = TestTime.objects.filter(testbuild=test_build).values("testdate").distinct()
                testdates = []
                for i in testdates_array:
                    testdates.append(str(i['testdate']))
        else:
            testduts = []
            testdates = []
        utility_args.update({'testbuild': test_build.version if test_build else '', 'testbuilds': testbuilds,'testdut': test_dut.name if test_dut else '', 'testduts': testduts,'testdate': test_date, 'testdates': testdates})
        return render(request, utility_template, utility_args)
    elif utility_name == 'get_result':
        testbuilds = Build.objects.values("version").distinct()
        utility_args['utility_name'] = utility_name
        utility_template = 'tbd/utility_{}.html'.format(utility_name)

        query_build = request.GET.get('query_build', '')
        utility_args['query_build']=query_build
        utility_args['testbuilds']=testbuilds
        if query_build:
            try:
                if "SDM845" in query_build and "1.0.1" not in query_build:
                    project_ = Project.objects.get(name="SDM845")
                    query_tst_build = Build.objects.filter(version=query_build,project=project_)[0]
                else:
                    query_tst_build = Build.objects.filter(version=query_build)[0]
                test_result=TestResult.objects.filter(build=query_tst_build)
                res = write_excel([test_result,])

                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = 'attachment; filename=beifen'+time.strftime('%Y%m%d',time.localtime(time.time()))+'.xls'
                res.save(response)
                return response
            except Exception as error:
                print("error: {}".format(error))
        return render(request, utility_template, utility_args)
    else:
        utility_template = 'tbd/utility.html'
    return render(request, utility_template, utility_args)

@csrf_exempt
def ajax_test_time(request):
    post_data = json.loads(request.body)
    test_build = post_data.get("testbuild",None)
    test_dut = post_data.get("testdut",None)
    test_date = post_data.get("testdate",None)
    test_project = post_data.get("testproject",None)
    passfail = post_data.get("actionpassfail",None)
    if passfail == 1:
        passfail = True
    else:
        passfail = False
    #test_time = post_data.get("testtime",None)
    try:
        test_project = Project.objects.get(name=test_project)
    except Exception as err:
        return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})

    try:
        if test_build:
            test_build = Build.objects.filter(version=test_build)[0]
        else:
            test_build = test_project.build_set.filter(is_stop=False)
            if test_build:
                test_build = test_build[0]
        test_dut = Host.objects.get(name=test_dut,project=test_project)
    except Exception as err:
        return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})

    if not test_date:
        test_date = str(datetime.date.today())
    if (test_build is not None) and (test_dut is not None) and (test_date is not None):
        if passfail:
            testtime=record_test_time(test_build =test_build,test_dut = test_dut,actionpass=True,test_date = test_date)
        else:
            testtime=record_test_time(test_build =test_build,test_dut = test_dut,actionfail=True,test_date = test_date)
        return JsonResponse({'Result':'OK', 'dut':test_dut.name if test_dut else '','build':test_build.version if test_build else '','testcount':testtime})
    return JsonResponse({'Result':'Fail', 'reason':'build/dut/date exist None'})

def record_test_time(test_build = None,test_dut = None,test_date = None):
    test_date = datetime.date(*map(lambda x:int(x),test_date.split('-')))
    today_date = str(datetime.datetime.today())[:10]
    start_time = datetime.datetime.strptime('{} 00:00:00'.format(today_date),'%Y-%m-%d %H:%M:%S')
    time_section = int((datetime.datetime.now() - start_time).seconds/(30*60))
    if ACTION_RECORD['record_date'] != datetime.date.today():
        for r_keys in ACTION_RECORD.keys():
            if str(ACTION_RECORD['record_date']) in r_keys:
                del ACTION_RECORD[r_keys]
        ACTION_RECORD['record_date'] = datetime.date.today()
        
    if record_key not in ACTION_RECORD.keys():
        ACTION_RECORD[record_key]=[0,0,0]
        
    if actionpass:
        ACTION_RECORD[record_key][0] += 1
    else:
        ACTION_RECORD[record_key][1] += 1
        
    if time_section != ACTION_RECORD[record_key][2]:
        testtime = TestTime.objects.get_or_create(testbuild=test_build,testdut=test_dut,testdate=test_date,timesection=ACTION_RECORD[record_key][2])[0]
        testtime.actionpass=ACTION_RECORD[record_key][0]
        testtime.actionfail=ACTION_RECORD[record_key][1]
        # if actionpass and testtime.testcount != 1:
        if (testtime.actionpass + testtime.actionfail) != 0 and round(testtime.actionpass/(testtime.actionpass + testtime.actionfail),2) * 100 > PASS_RATE:
            testtime.testcount = 1
        else:
            testtime.testcount = 0
        testtime.save()
        ACTION_RECORD[record_key][0]=0
        ACTION_RECORD[record_key][1]=0
        ACTION_RECORD[record_key][2] = time_section
        return 'Update'
    else:
        return 'Keep'
    
def testtime_page(request):
    test_build = request.GET.get('testbuild', '')
    test_dut = request.GET.get('testdut', '')
    test_date = request.GET.get('testdate', '')

    try:
        if test_build:
            test_build = Build.objects.filter(version=test_build)[0]
        if test_dut:
            test_dut = Host.objects.get(name=test_dut,project=test_build.project)
    except Exception as err:
        return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})

    testbuilds = Build.objects.values("version").distinct()
    if test_build :
        testduts = TestTime.objects.filter(testbuild=test_build).values("testdut__name").distinct()
        if test_dut:
            testdates_array = TestTime.objects.filter(testbuild=test_build,testdut=test_dut).values("testdate").distinct()
            testdates = []
            for i in testdates_array:
                testdates.append(str(i['testdate']))
        else:
            testdates = []
    else:
        testduts = []
        testdates = []

    return render(request, 'tbd/testtime.html', {
        'testbuild': test_build.version if test_build else '', 'testbuilds': testbuilds,
        'testdut': test_dut.name if test_dut else '', 'testduts': testduts,
        'testdate': test_date, 'testdates': testdates,
    })


def testtime_api(request):
    print("request testresult list:" + repr(request.POST))
    records = []
    total_count = 0
    if request.method == 'POST':
        test_build = request.POST.get('test_build', None)
        record_build= test_build
        test_dut = request.POST.get('test_dut', None)
        record_dut = test_dut
        test_date = request.POST.get('test_date', None)
        record_date = test_date
        start_index = int(request.GET.get('jtStartIndex', 0))
        page_size = int(request.GET.get('jtPageSize', 20))

        try:
            if test_build:
                test_build = Build.objects.filter(version=test_build)[0]
            if test_dut:
                test_dut = Host.objects.get(name=test_dut,project=test_build.project)

        except Exception as err:
            return JsonResponse({'Result':'Error','Records': [],'Message':'error info : {}'.format(str(err))})

        if test_build:
            if test_date:
                test_date = datetime.date(*map(lambda x:int(x),test_date.split('-')))

            if test_dut and test_date:
                time_objs = TestTime.objects.filter(testbuild=test_build,testdut=test_dut,testdate=test_date)
                time_objs = time_objs.values('testbuild__version','testdut__name','testdate').annotate(testcount=Sum('testcount'),testpass=Sum('actionpass'),testfail=Sum('actionfail'))
            elif not test_dut and not test_date:
                time_objs = TestTime.objects.filter(testbuild=test_build)
                #time_objs = time_objs.values('testbuild__version').annotate(testcount=Sum('testcount'))
                time_objs = time_objs.values('testdut__name').annotate(testcount=Sum('testcount'),testpass=Sum('actionpass'),testfail=Sum('actionfail'))
            elif not test_dut:
                time_objs = TestTime.objects.filter(testbuild=test_build,testdate=test_date)
                time_objs = time_objs.values('testdut__name').annotate(testcount=Sum('testcount'),testpass=Sum('actionpass'),testfail=Sum('actionfail'))
            else:
                time_objs = TestTime.objects.filter(testbuild=test_build,testdut=test_dut)
                time_objs = time_objs.values('testdate').annotate(testcount=Sum('testcount'),testpass=Sum('actionpass'),testfail=Sum('actionfail'))
                
            #time_objs = time_objs.values('testbuild__version','testdut__name','testdate').annotate(testcount=Sum('testcount'))
        else:
            time_objs = []
        if len(time_objs) > start_index and len(time_objs) > page_size+start_index:
            all_ta = time_objs[start_index: page_size+start_index]
        else:
            all_ta = time_objs[start_index:]
        for ta in all_ta:
            if test_dut and test_date:
                records.append({
                    #'test_time_id':ta['id'],
                    'test_build': ta['testbuild__version'],
                    'test_dut': ta['testdut__name'],
                    'test_date': str(ta['testdate']),
                    'test_count': ta['testcount'],
                    'test_pass': ta['testpass'],
                    'test_fail': ta['testfail'],
                    #'test_section':ta['timesection'],
                })
            elif not test_dut and not test_date:
                records.append({
                    #'test_time_id':ta['id'],
                    'test_build': record_build,
                    'test_dut': ta['testdut__name'],
                    'test_date': record_date,
                    'test_count': ta['testcount'],
                    'test_pass': ta['testpass'],
                    'test_fail': ta['testfail'],
                    #'test_section':ta['timesection'],
                })
            elif not test_dut:
                records.append({
                    #'test_time_id':ta['id'],
                    'test_build': record_build,
                    'test_dut': ta['testdut__name'],
                    'test_date': record_date,
                    'test_count': ta['testcount'],
                    'test_pass': ta['testpass'],
                    'test_fail': ta['testfail'],
                    #'test_section':ta['timesection'],
                })
            else:
                records.append({
                    #'test_time_id':ta['id'],
                    'test_build': record_build,
                    'test_dut': record_dut,
                    'test_date': str(ta['testdate']),
                    'test_count': ta['testcount'],
                    'test_pass': ta['testpass'],
                    'test_fail': ta['testfail'],
                    #'test_section':ta['timesection'],
                })
        total_count = len(time_objs)
    return JsonResponse({'Result': 'OK', 'Records': records, 'TotalRecordCount': total_count})

def testtime_create(request):
    #{u'test_times': [u'13'], u'test_dut': [u'0'], u'test_date': [u'0'], u'test_build': [u'wert']}>
    test_count=request.POST.get('test_count',None)
    test_section=request.POST.get('test_section',None)
    test_dut=request.POST.get('test_dut',None)
    test_date=datetime.date.today()
    test_build=request.POST.get('test_build',None)

    try:
        if test_build:
            test_build = Build.objects.filter(version=test_build)[0]
        if test_dut:
            test_dut = Host.objects.get(name=test_dut,project=test_build.project)
    except Exception as err:
        return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})
    if test_build and test_dut and test_count and test_section:
        try:
            record = {}
            Add_time = TestTime.objects.get_or_create(testdate=test_date,testbuild=test_build,testdut=test_dut,testcount=int(test_count),timesection=int(test_section))
            if Add_time:
                Add_time = Add_time[0]
                record={'test_time_id':Add_time.id,'test_section':Add_time.timesection,'test_count':Add_time.testcount,'test_dut':Add_time.testdut.name,'test_build':Add_time.testbuild.version,'test_date':str(Add_time.testdate)}
                return JsonResponse({'Result': 'OK', "Record": record})
        except Exception as err:
            return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})

def testtime_update(request):
    #print request.POST
    test_count=request.POST.get('test_count',None)
    test_time_id=request.POST.get('test_time_id',None)
    if test_time_id and test_count:
        try:
            record={}
            mdfy_time = TestTime.objects.filter(id=int(test_time_id))
            if mdfy_time:
                update_time = mdfy_time[0]
                update_time.testcount = test_count
                update_time.save()
                record={'test_time_id':update_time.id,'test_count':update_time.testcount,'test_dut':update_time.testdut.name,'test_build':update_time.testbuild.version,'test_date':str(update_time.testdate)}
            return JsonResponse({'Result': 'OK', "Record": record})
        except Exception as err:
            return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})

def testtime_delete(request):
    test_time_id=request.POST.get('test_time_id',None)
    if test_time_id:
        try:
            delete_time = TestTime.objects.filter(id=int(test_time_id))
            if delete_time:
                delete_time[0].delete()
            return JsonResponse({'Result': 'OK'})
        except Exception as err:
            return JsonResponse({'Result':'Error','Message':'error info : {}'.format(str(err))})


# @accept_websocket
# def echo(request):
    # if not request.is_websocket():
        # try:
            # message = request.GET['message']
            # return HttpResponse(message)
        # except:
            # return render(request,'index.html')
    # else:
        # while True:
            # time.sleep(5)
            # request.websocket.send("hahawolaile")