from requests import Session

sess = Session()
if 1:
    resp = sess.post('http://127.0.0.1/auto/crash_info', {
        'project_name': "TF2.1.5.1.0",
        'build_version': "version001",
        'path': "\\\\mdm\\c003",
        'host_name': "",
        'host_ip': "1.1.1.2",
        'testcase_name': "testplan1_s3_s4_udp_traffic",
    })
    print resp.json()

if 0:
    resp = sess.post('http://127.0.0.1/auto/query_build', {
        'project_name': "MDM9607.LE.1.1",
    })
    print resp.json()
    
if 0:
    resp = sess.post('http://127.0.0.1/auto/testaction_info', {
        'project_name': "TF2.1.5.1.0",
        'build_version': "version001",
        'ta_name': "Enable_WIFI",
        'is_pass': "0",
        'host_name': "sdc-cnss-001",
        'host_ip': "1.1.1.1",
    })
    print resp.json()

if 1:
    resp = sess.post('http://127.0.0.1/auto/project_info', {
        'project_name': "TF2.1.5.1.0",
        'project_owner': "xiaoming",
        'project_is_stop': "",
    })
    print resp.json()

if 1:
    resp = sess.post('http://127.0.0.1/auto/build_info', {
        'project_name': "TF2.1.5.1.0",
        'build_version': "version002",
        'build_short_name': "v2",
        'build_test_hours': "10",
        'build_use_server': '0',
        'build_server_path': '\\\\s\\v2',
        'build_local_path': '\\\\l\\v2',
        'build_crash_path': '\\\\c\\v2',
        'build_is_stop': '0',
    })
    print resp.json()