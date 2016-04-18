from requests import Session

sess = Session()
resp = sess.post('http://127.0.0.1:8000/auto/crash_info', {
    'project_name': "MDM.LE.1.0.1",
    'project_owner': "junjiang",
    'build_version': "version001",
    'path': "\\\\mdm\\c007",
    'host_name': "pc3",
    'host_ip': "1.1.1.1",
    'testcase_name': "reboot.xml",
    'testcase_platform': "PH",
})
print resp.json()
