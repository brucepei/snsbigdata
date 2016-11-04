import sys
from requests import Session

sess = Session()
if 0:
    resp = sess.post('http://10.231.194.75:8080/auto/crash_info', {
        'project_name': "QCA9377.WIN.1.1.7_win10",
        'build_version': "win10",
        'path': "\\\\mdm\\c003",
        'host_name': "",
        'host_ip': "",
        'testcase_name': "",
    })
    print resp.json()

if 0:
    resp = sess.post('http://10.231.194.75:8080/auto/query_project', {
    }).json()
    print resp
    if not resp['code']:
        for sp in resp['result']:
            rs = sess.post('http://10.231.194.75:8080/auto/get_running_jira', {
                'project_id':  sp['id'],
            })
            print "SP {}:\n{}".format(sp['name'], rs.json())
            # sys.exit(-1)
    
if 0:
    resp = sess.post('http://127.0.0.1/auto/query_build', {
        'project_name': "TF2.1.5.1.0",
    })
    print resp.json()
   
if 0:
    resp = sess.post('http://127.0.0.1/auto/testaction_info', {
        'project_name': "TF2.1.5.1.0",
        'ta_name': "Enable_WIFI",
        'is_pass': "1",
        'count': 4,
        'host_name': "sdc-cnss-002",
        #'host_ip': "1.1.1.1",
    })
    print resp.json()

if 0:
    resp = sess.post('http://127.0.0.1/auto/project_info', {
        'project_name': "TF2.1.5.1.0",
        'project_owner': "xiaoming",
        'project_is_stop': "",
    })
    print resp.json()

if 0:
    resp = sess.post('http://127.0.0.1/auto/build_info', {
        'project_name': "TF2.1.5.1.0",
        'build_version': "version004",
        'build_short_name': "v4",
        'build_test_hours': "10",
        'build_use_server': '0',
        'build_server_path': '\\\\s\\v2',
        'build_local_path': '\\\\l\\v2',
        'build_crash_path': '\\\\c\\v2',
        'build_is_stop': '0',
    })
    print resp.json()
    
if 1:
    resp = sess.post('http://127.0.0.1/auto/get_jira', {
        'start_id': 0,
        'length': 50,
    })
    print resp.json()
    
if 0:
    resp = sess.post('http://127.0.0.1/auto/jira_info', {
        'id': 2,
        'jira_id': 'CNSSDEBUG-001',
        'category': 'IN',
    })
    print resp.json()