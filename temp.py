from requests import Session

sess = Session()
if 0:
    resp = sess.post('http://127.0.0.1/auto/crash_info', {
        'project_name': "Naples.LA.1.0.7",
        'build_version': "version001",
        'path': "\\\\mdm\\c002",
        'host_name': "SDC-CNSS-031",
        'host_ip': "1.1.1.1",
        'testcase_name': "testplan1_s3_s4_traffic",
    })
    print resp.json()

if 1:
    resp = sess.post('http://127.0.0.1/auto/query_build', {
        'project_name': "MDM9607.LE.1.1",
    })
    print resp.json()

