import os, configparser, requests
from pathlib import Path
BASE=os.path.dirname(os.path.abspath(__import__('sys').executable if getattr(__import__('sys'),'frozen',False) else __file__))
CONFIG=os.path.join(BASE,'cloud_config.ini')
def set_server_url(url):
    url=str(url).strip().rstrip('/')
    if not url.startswith(('https://','http://localhost','http://127.0.0.1')):
        raise RuntimeError('Use a public HTTPS URL (localhost is allowed for testing).')
    cp=configparser.ConfigParser(); cp.read(CONFIG)
    if not cp.has_section('server'): cp.add_section('server')
    cp.set('server','url',url)
    with open(CONFIG,'w',encoding='utf-8') as f: cp.write(f)
    return url
def test_server_url(url=None):
    target=(url or server_url()).rstrip('/')
    try:
        r=requests.get(target+'/health',timeout=90); data=r.json()
        if not r.ok or data.get('status')!='ok': raise RuntimeError('Server health check failed.')
        return data
    except Exception as e: raise RuntimeError('Connection test failed: '+str(e))
def server_url():
    cp=configparser.ConfigParser(); cp.read(CONFIG); url=cp.get('server','url',fallback='https://YOUR-SERVER-DOMAIN').strip().rstrip('/')
    if 'YOUR-SERVER-DOMAIN' in url or not url: url='https://ss-mailer-cloud.onrender.com'
    if not url.startswith('https://') and 'localhost' not in url and '127.0.0.1' not in url: raise RuntimeError('Cloud server URL must use HTTPS.')
    return url
def call(method,path,token=None,**kwargs):
    headers=kwargs.pop('headers',{})
    if token: headers['Authorization']='Bearer '+token
    try: r=requests.request(method,server_url()+path,headers=headers,timeout=90,**kwargs)
    except requests.RequestException as e: raise RuntimeError('Cannot connect to cloud server after waiting up to 90 seconds. If Render Free is waking up, wait 1-2 minutes and try again. Details: '+str(e))
    try: data=r.json()
    except ValueError: data={'error':'Server returned an invalid response'}
    if not r.ok: raise RuntimeError(data.get('error','Request failed'))
    return data
