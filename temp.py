from requests import Session

sess = Session()
resp = sess.post('http://127.0.0.1:8000/auto/crash_info', {'project_name': 'MDM'})
print resp.json()
