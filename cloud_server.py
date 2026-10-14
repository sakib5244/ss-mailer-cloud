"""SS Mailer cloud auth API. Deploy on a trusted HTTPS host."""
import os, sqlite3, secrets, hashlib, hmac, time
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, g

APP_DIR=os.path.dirname(os.path.abspath(__file__))
DB_PATH=os.environ.get('SSMAILER_DB', os.path.join(APP_DIR,'ssmailer_cloud.db'))
ADMIN_PASSWORD=os.environ.get('SSMAILER_ADMIN_PASSWORD','')
SECRET=os.environ.get('SSMAILER_TOKEN_SECRET','')
app=Flask(__name__)

def connect():
    c=sqlite3.connect(DB_PATH, timeout=20, isolation_level=None)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA foreign_keys=ON')
    return c

def init_db():
    c=connect()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, pw_hash TEXT NOT NULL, pw_salt TEXT NOT NULL, expires_at TEXT NOT NULL, device_limit INTEGER NOT NULL, sending_limit INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, owner_subadmin TEXT);
    CREATE TABLE IF NOT EXISTS devices(username TEXT NOT NULL, device_id TEXT NOT NULL, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL, PRIMARY KEY(username,device_id), FOREIGN KEY(username) REFERENCES users(username) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, username TEXT NOT NULL, role TEXT NOT NULL, device_id TEXT, expires_at REAL NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS reservations(id TEXT PRIMARY KEY, username TEXT NOT NULL, created_at TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'reserved');
    CREATE TABLE IF NOT EXISTS subadmins(username TEXT PRIMARY KEY, pw_hash TEXT NOT NULL, pw_salt TEXT NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL, device_limit INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1);
    ''')
    cols=[r['name'] for r in c.execute('PRAGMA table_info(users)').fetchall()]
    if 'owner_subadmin' not in cols: c.execute('ALTER TABLE users ADD COLUMN owner_subadmin TEXT')
    c.close()

def now(): return datetime.now(timezone.utc)
def iso(dt): return dt.astimezone(timezone.utc).isoformat(timespec='seconds')
def hashpw(p,s): return hashlib.pbkdf2_hmac('sha256',(p+SECRET).encode(),bytes.fromhex(s),310000).hex()
def token_hash(t): return hashlib.sha256(t.encode()).hexdigest()
def get_auth():
    h=request.headers.get('Authorization','')
    if not h.startswith('Bearer '): return None
    tok=h[7:]; c=connect(); row=c.execute('SELECT * FROM sessions WHERE token_hash=? AND expires_at>?',(token_hash(tok),time.time())).fetchone(); c.close()
    if row: g.token=tok; return row
    return None
def require(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapped(*a,**kw):
            s=get_auth()
            if not s or (role and s['role']!=role): return jsonify(error='Unauthorized'),401
            g.session=s
            return fn(*a,**kw)
        return wrapped
    return deco
def issue_session(username,role,device=None):
    raw=secrets.token_urlsafe(40); c=connect(); c.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?)',(token_hash(raw),username,role,device,time.time()+60*60*24*14,iso(now()))); c.close(); return raw

def user_public(c,r):
    dev=c.execute('SELECT COUNT(*) n FROM devices WHERE username=?',(r['username'],)).fetchone()['n']
    return {'username':r['username'],'expires_at':r['expires_at'],'validity_days_left':max(0,(datetime.fromisoformat(r['expires_at'])-now()).days),'device_limit':r['device_limit'],'devices_used':dev,'sending_limit':r['sending_limit'],'used':r['used'],'limit_left':max(0,r['sending_limit']-r['used']),'active':bool(r['active']),'created_at':r['created_at']}

@app.get('/health')
def health(): return jsonify(status='ok',service='SS Mailer Cloud API')

@app.post('/api/admin/login')
def admin_login():
    if not ADMIN_PASSWORD: return jsonify(error='Server admin password is not configured'),503
    p=str(request.json.get('password','')) if request.is_json else ''
    if not hmac.compare_digest(p,ADMIN_PASSWORD): return jsonify(error='Invalid admin password'),401
    return jsonify(token=issue_session('admin','admin'),role='admin')

@app.post('/api/subadmin/login')
def subadmin_login():
    d=request.get_json(silent=True) or {}; u=str(d.get('username','')).strip(); p=str(d.get('password',''))
    c=connect(); r=c.execute('SELECT * FROM subadmins WHERE username=? AND active=1',(u,)).fetchone(); c.close()
    if not r or not hmac.compare_digest(hashpw(p,r['pw_salt']),r['pw_hash']): return jsonify(error='Invalid subadmin credentials'),401
    return jsonify(token=issue_session(u,'subadmin'),subadmin={'username':u,'name':r['name'],'phone':r['phone'],'device_limit':r['device_limit']})

@app.get('/api/admin/subadmins')
@require('admin')
def list_subadmins():
    c=connect(); rows=c.execute('SELECT * FROM subadmins ORDER BY username').fetchall(); out=[]
    for r in rows:
        counts=c.execute('SELECT COUNT(*) n, SUM(CASE WHEN active=1 AND expires_at>? THEN 1 ELSE 0 END) active FROM users WHERE owner_subadmin=?',(iso(now()),r['username'])).fetchone()
        out.append({'username':r['username'],'name':r['name'],'phone':r['phone'],'device_limit':r['device_limit'],'active':bool(r['active']),'user_count':counts['n'],'active_user_count':counts['active'] or 0})
    c.close(); return jsonify(subadmins=out)

@app.post('/api/admin/subadmins')
@require('admin')
def create_subadmin():
    d=request.get_json(silent=True) or {}; u=str(d.get('username','')).strip(); p=str(d.get('password','')); name=str(d.get('name','')).strip(); phone=str(d.get('phone','')).strip()
    try: dev=int(d.get('device_limit',1))
    except: return jsonify(error='Device limit must be a number'),400
    if not u or not name or not phone or len(p)<8 or dev<1: return jsonify(error='Name, phone, username, password (8+ chars) and positive device limit are required'),400
    salt=secrets.token_hex(16); c=connect()
    try: c.execute('INSERT INTO subadmins(username,pw_hash,pw_salt,name,phone,device_limit,created_at,active) VALUES(?,?,?,?,?,?,?,1)',(u,hashpw(p,salt),salt,name,phone,dev,iso(now())))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Subadmin username already exists'),409
    c.close(); return jsonify(ok=True),201

@app.put('/api/admin/subadmins/<username>')
@require('admin')
def edit_subadmin(username):
    d=request.get_json(silent=True) or {}; c=connect(); r=c.execute('SELECT * FROM subadmins WHERE username=?',(username,)).fetchone()
    if not r: c.close(); return jsonify(error='Subadmin not found'),404
    newu=str(d.get('username',username)).strip(); name=str(d.get('name',r['name'])).strip(); phone=str(d.get('phone',r['phone'])).strip(); pw=str(d.get('password',''))
    try: dev=int(d.get('device_limit',r['device_limit']))
    except: c.close(); return jsonify(error='Device limit must be a number'),400
    active=1 if d.get('active',bool(r['active'])) else 0
    if not newu or not name or not phone or dev<1 or (pw and len(pw)<8): c.close(); return jsonify(error='Invalid subadmin fields'),400
    try:
        if pw:
            salt=secrets.token_hex(16); c.execute('UPDATE subadmins SET username=?,pw_hash=?,pw_salt=?,name=?,phone=?,device_limit=?,active=? WHERE username=?',(newu,hashpw(pw,salt),salt,name,phone,dev,active,username))
        else: c.execute('UPDATE subadmins SET username=?,name=?,phone=?,device_limit=?,active=? WHERE username=?',(newu,name,phone,dev,active,username))
        c.execute('UPDATE users SET owner_subadmin=? WHERE owner_subadmin=?',(newu,username)); c.execute('UPDATE sessions SET username=? WHERE username=? AND role=?',(newu,username,'subadmin'))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Username already exists'),409
    c.close(); return jsonify(ok=True)

@app.delete('/api/admin/subadmins/<username>')
@require('admin')
def delete_subadmin(username):
    c=connect(); c.execute('UPDATE users SET owner_subadmin=NULL WHERE owner_subadmin=?',(username,)); c.execute('DELETE FROM subadmins WHERE username=?',(username,)); c.execute('DELETE FROM sessions WHERE username=? AND role=?',(username,'subadmin')); c.close(); return jsonify(ok=True)

@app.get('/api/subadmin/profile')
@require('subadmin')
def subadmin_profile():
    c=connect(); r=c.execute('SELECT username,name,phone,device_limit,active FROM subadmins WHERE username=?',(g.session['username'],)).fetchone(); c.close()
    if not r or not r['active']: return jsonify(error='Subadmin disabled'),403
    return jsonify(subadmin=dict(r))

@app.get('/api/subadmin/users')
@require('subadmin')
def subadmin_users():
    q=request.args.get('q','').strip().lower(); c=connect(); rows=c.execute('SELECT * FROM users WHERE owner_subadmin=? AND lower(username) LIKE ? ORDER BY username',(g.session['username'],'%'+q+'%')).fetchall(); out=[user_public(c,r) for r in rows]; c.close(); return jsonify(users=out)

@app.post('/api/subadmin/users')
@require('subadmin')
def subadmin_create_user():
    d=request.get_json(silent=True) or {}; u=str(d.get('username','')).strip(); p=str(d.get('password',''))
    try: days=int(d.get('validity_days')); dev=int(d.get('device_limit')); lim=int(d.get('sending_limit'))
    except: return jsonify(error='Validity, device limit and sending limit must be integers'),400
    c=connect(); sa=c.execute('SELECT * FROM subadmins WHERE username=? AND active=1',(g.session['username'],)).fetchone()
    owned=c.execute('SELECT COUNT(*) n FROM users WHERE owner_subadmin=?',(g.session['username'],)).fetchone()['n']
    if not sa or owned>=sa['device_limit']: c.close(); return jsonify(error='Subadmin user/device limit reached'),403
    if not u or len(p)<8 or min(days,dev,lim)<1: c.close(); return jsonify(error='Username, password (8+ chars) and positive numeric values are required'),400
    salt=secrets.token_hex(16); exp=iso(now()+timedelta(days=days))
    try: c.execute('INSERT INTO users(username,pw_hash,pw_salt,expires_at,device_limit,sending_limit,used,created_at,active,owner_subadmin) VALUES(?,?,?,?,?,?,0,?,1,?)',(u,hashpw(p,salt),salt,exp,dev,lim,iso(now()),g.session['username']))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Username already exists'),409
    c.close(); return jsonify(ok=True),201

@app.put('/api/subadmin/users/<username>')
@require('subadmin')
def subadmin_edit_user(username):
    d=request.get_json(silent=True) or {}; c=connect(); r=c.execute('SELECT * FROM users WHERE username=? AND owner_subadmin=?',(username,g.session['username'])).fetchone()
    if not r: c.close(); return jsonify(error='User not found'),404
    try: days=int(d.get('validity_days',max(1,(datetime.fromisoformat(r['expires_at'])-now()).days))); dev=int(d.get('device_limit',r['device_limit'])); lim=int(d.get('sending_limit',r['sending_limit']))
    except: c.close(); return jsonify(error='Numeric values must be integers'),400
    newu=str(d.get('username',username)).strip(); pw=str(d.get('password','')); active=1 if d.get('active',bool(r['active'])) else 0
    if not newu or min(days,dev,lim)<1 or (pw and len(pw)<8): c.close(); return jsonify(error='Invalid user fields'),400
    exp=iso(now()+timedelta(days=days))
    try:
        if pw:
            salt=secrets.token_hex(16); c.execute('UPDATE users SET username=?,pw_hash=?,pw_salt=?,expires_at=?,device_limit=?,sending_limit=?,active=? WHERE username=? AND owner_subadmin=?',(newu,hashpw(pw,salt),salt,exp,dev,lim,active,username,g.session['username']))
        else: c.execute('UPDATE users SET username=?,expires_at=?,device_limit=?,sending_limit=?,active=? WHERE username=? AND owner_subadmin=?',(newu,exp,dev,lim,active,username,g.session['username']))
        c.execute('UPDATE devices SET username=? WHERE username=?',(newu,username)); c.execute('UPDATE sessions SET username=? WHERE username=?',(newu,username)); c.execute('UPDATE reservations SET username=? WHERE username=?',(newu,username))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Username already exists'),409
    c.close(); return jsonify(ok=True)

@app.delete('/api/subadmin/users/<username>')
@require('subadmin')
def subadmin_delete_user(username):
    c=connect(); r=c.execute('SELECT 1 FROM users WHERE username=? AND owner_subadmin=?',(username,g.session['username'])).fetchone()
    if not r: c.close(); return jsonify(error='User not found'),404
    c.execute('DELETE FROM users WHERE username=?',(username,)); c.execute('DELETE FROM devices WHERE username=?',(username,)); c.execute('DELETE FROM sessions WHERE username=?',(username,)); c.execute('DELETE FROM reservations WHERE username=?',(username,)); c.close(); return jsonify(ok=True)

@app.post('/api/user/login')
def user_login():
    data=request.get_json(silent=True) or {}; u=str(data.get('username','')).strip(); p=str(data.get('password','')); dev=str(data.get('device_id',''))[:128]
    if not u or not p or not dev: return jsonify(error='Username, password and device ID are required'),400
    c=connect(); c.execute('BEGIN IMMEDIATE'); r=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not r or not r['active'] or not hmac.compare_digest(hashpw(p,r['pw_salt']),r['pw_hash']): c.rollback(); c.close(); return jsonify(error='Invalid credentials or disabled account'),401
    if datetime.fromisoformat(r['expires_at']) <= now(): c.rollback(); c.close(); return jsonify(error='Account validity has expired'),403
    if r['used']>=r['sending_limit']: c.rollback(); c.close(); return jsonify(error='Sending limit exhausted'),403
    d=c.execute('SELECT 1 FROM devices WHERE username=? AND device_id=?',(u,dev)).fetchone()
    if not d:
        count=c.execute('SELECT COUNT(*) n FROM devices WHERE username=?',(u,)).fetchone()['n']
        if count>=r['device_limit']: c.rollback(); c.close(); return jsonify(error='Device limit reached'),403
        c.execute('INSERT INTO devices VALUES(?,?,?,?)',(u,dev,iso(now()),iso(now())))
    else: c.execute('UPDATE devices SET last_seen=? WHERE username=? AND device_id=?',(iso(now()),u,dev))
    c.commit(); c.close()
    return jsonify(token=issue_session(u,'user',dev),user={'username':u,'expires_at':r['expires_at'],'sending_limit':r['sending_limit'],'limit_left':max(0,r['sending_limit']-r['used'])})

@app.get('/api/me')
@require()
def me():
    s=g.session
    if s['role']=='admin': return jsonify(role='admin',username='admin')
    c=connect(); r=c.execute('SELECT * FROM users WHERE username=?',(s['username'],)).fetchone(); c.close()
    if not r or not r['active'] or datetime.fromisoformat(r['expires_at'])<=now(): return jsonify(error='Account expired or disabled'),403
    return jsonify(role='user',user={'username':r['username'],'expires_at':r['expires_at'],'limit_left':max(0,r['sending_limit']-r['used']),'sending_limit':r['sending_limit']})

@app.post('/api/logout')
@require()
def logout():
    c=connect(); c.execute('DELETE FROM sessions WHERE token_hash=?',(token_hash(g.token),)); c.close(); return jsonify(ok=True)

@app.get('/api/admin/users')
@require('admin')
def list_users():
    q=request.args.get('q','').strip().lower(); c=connect(); rows=c.execute('SELECT * FROM users WHERE lower(username) LIKE ? ORDER BY username',('%'+q+'%',)).fetchall(); out=[user_public(c,r) for r in rows]; c.close(); return jsonify(users=out)

@app.post('/api/admin/users')
@require('admin')
def create_user():
    d=request.get_json(silent=True) or {}; u=str(d.get('username','')).strip(); p=str(d.get('password','')); days=d.get('validity_days'); dev=d.get('device_limit'); lim=d.get('sending_limit')
    try: days=int(days); dev=int(dev); lim=int(lim)
    except (ValueError,TypeError): return jsonify(error='Validity, device limit and sending limit must be integers'),400
    if not u or len(u)>80 or len(p)<8 or min(days,dev,lim)<1: return jsonify(error='Username required; password must be 8+ characters; numeric values must be positive'),400
    salt=secrets.token_hex(16); exp=iso(now()+timedelta(days=days)); c=connect()
    try: c.execute('INSERT INTO users(username,pw_hash,pw_salt,expires_at,device_limit,sending_limit,used,created_at,active) VALUES(?,?,?,?,?,?,0,?,1)',(u,hashpw(p,salt),salt,exp,dev,lim,iso(now())))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Username already exists'),409
    r=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone(); out=user_public(c,r); c.close(); return jsonify(user=out),201

@app.put('/api/admin/users/<username>')
@require('admin')
def edit_user(username):
    d=request.get_json(silent=True) or {}; c=connect(); r=c.execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    if not r: c.close(); return jsonify(error='User not found'),404
    try: days=int(d.get('validity_days',max(1,(datetime.fromisoformat(r['expires_at'])-now()).days))); dev=int(d.get('device_limit',r['device_limit'])); lim=int(d.get('sending_limit',r['sending_limit']))
    except (ValueError,TypeError): c.close(); return jsonify(error='Numeric values must be integers'),400
    newu=str(d.get('username',username)).strip(); active=1 if d.get('active',bool(r['active'])) else 0; pw=str(d.get('password',''))
    if not newu or min(days,dev,lim)<1 or (pw and len(pw)<8): c.close(); return jsonify(error='Invalid fields or password too short'),400
    exp=iso(now()+timedelta(days=days))
    try:
        if pw:
            salt=secrets.token_hex(16); c.execute('UPDATE users SET username=?,pw_hash=?,pw_salt=?,expires_at=?,device_limit=?,sending_limit=?,active=? WHERE username=?',(newu,hashpw(pw,salt),salt,exp,dev,lim,active,username))
        else: c.execute('UPDATE users SET username=?,expires_at=?,device_limit=?,sending_limit=?,active=? WHERE username=?',(newu,exp,dev,lim,active,username))
    except sqlite3.IntegrityError: c.close(); return jsonify(error='Username already exists'),409
    c.execute('UPDATE devices SET username=? WHERE username=?',(newu,username)); c.execute('UPDATE sessions SET username=? WHERE username=?',(newu,username)); r=c.execute('SELECT * FROM users WHERE username=?',(newu,)).fetchone(); out=user_public(c,r); c.close(); return jsonify(user=out)

@app.delete('/api/admin/users/<username>')
@require('admin')
def delete_user(username):
    c=connect(); c.execute('DELETE FROM users WHERE username=?',(username,)); c.execute('DELETE FROM sessions WHERE username=?',(username,)); c.execute('DELETE FROM reservations WHERE username=?',(username,)); c.commit(); c.close(); return jsonify(ok=True)

@app.post('/api/send/reserve')
@require('user')
def reserve_send():
    """Atomic quota reservation; call once per recipient before sending."""
    s=g.session; c=connect(); c.execute('BEGIN IMMEDIATE'); r=c.execute('SELECT * FROM users WHERE username=?',(s['username'],)).fetchone()
    if not r or not r['active'] or datetime.fromisoformat(r['expires_at'])<=now(): c.rollback(); c.close(); return jsonify(error='Account expired or disabled'),403
    if r['used']>=r['sending_limit']: c.rollback(); c.close(); return jsonify(error='Sending limit exhausted'),403
    rid=secrets.token_urlsafe(24); c.execute('UPDATE users SET used=used+1 WHERE username=? AND used<sending_limit',(s['username'],));
    if c.execute('SELECT changes()').fetchone()[0]!=1: c.rollback(); c.close(); return jsonify(error='Sending limit exhausted'),403
    c.execute("INSERT INTO reservations(id,username,created_at,state) VALUES(?,?,?,'reserved')",(rid,s['username'],iso(now()))); c.commit(); left=c.execute('SELECT sending_limit-used AS n FROM users WHERE username=?',(s['username'],)).fetchone()['n']; c.close(); return jsonify(reservation_id=rid,limit_left=left)

@app.post('/api/send/finish')
@require('user')
def finish_send():
    d=request.get_json(silent=True) or {}; rid=str(d.get('reservation_id','')); success=bool(d.get('success')); c=connect(); c.execute('BEGIN IMMEDIATE'); r=c.execute('SELECT * FROM reservations WHERE id=? AND username=?',(rid,g.session['username'])).fetchone()
    if not r or r['state']!='reserved': c.rollback(); c.close(); return jsonify(error='Reservation not found or already finalized'),409
    # Failed sends refund the quota exactly once; successful sends keep the reservation charged.
    if not success: c.execute('UPDATE users SET used=MAX(0,used-1) WHERE username=?',(g.session['username'],))
    c.execute('UPDATE reservations SET state=? WHERE id=?',('sent' if success else 'refunded',rid)); c.commit(); left=c.execute('SELECT sending_limit-used AS n FROM users WHERE username=?',(g.session['username'],)).fetchone()['n']; c.close(); return jsonify(ok=True,limit_left=left)

init_db()

if __name__=='__main__':
    if not ADMIN_PASSWORD or not SECRET:
        raise SystemExit('Set SSMAILER_ADMIN_PASSWORD and SSMAILER_TOKEN_SECRET environment variables before running.')
    # Development only. Production deployment must use HTTPS via a WSGI server/reverse proxy.
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT','8443')),debug=False)
