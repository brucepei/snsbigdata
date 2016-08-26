from requests import Session

sess = Session()
resp = sess.post('http://127.0.0.1/auto/crash_info', {
    'project_name': "Naples.LA.1.0.7",
    'build_version': "version001",
    'path': "\\\\mdm\\c002",
    'host_name': "SDC-CNSS-031",
    'host_ip': "1.1.1.1",
    'testcase_name': "testplan1_s3_s4_traffic",
})
print resp.json()
