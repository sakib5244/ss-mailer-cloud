import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, hashlib, os, sys, socket, uuid, json
from datetime import datetime, timedelta
from ss_mailer import App

BASE=os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__))
DB=os.path.join(BASE,'ssmailer_users.db')
BG='#030d22'; PANEL='#061a38'; PANEL2='#08244b'; CYAN='#00c8ff'; PURPLE='#a100ff'; WHITE='#eef6ff'; MUTED='#a7c8ef'; GREEN='#00d49a'; RED='#ff3d77'
DEVICE=hashlib.sha256((socket.gethostname()+str(uuid.getnode())).encode()).hexdigest()[:24]
def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.execute('''CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY,password TEXT NOT NULL,expires TEXT NOT NULL,device_limit INTEGER NOT NULL,sending_limit INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0,devices TEXT NOT NULL DEFAULT '[]',created TEXT NOT NULL)''')
 c.execute('''CREATE TABLE IF NOT EXISTS settings(k TEXT PRIMARY KEY,v TEXT NOT NULL)''')
 if not c.execute("SELECT 1 FROM settings WHERE k='admin_hash'").fetchone(): c.execute("INSERT INTO settings VALUES('admin_hash',?)",(digest('admin123'),))
 c.commit(); return c

def styled_button(parent,text,cmd,bg='#0869f7'):
 return tk.Button(parent,text=text,command=cmd,bg=bg,fg='white',activebackground=PURPLE,activeforeground='white',relief='flat',bd=0,font=('Segoe UI',10,'bold'),cursor='hand2',padx=12,pady=8)
def entry(parent,show=None): return tk.Entry(parent,bg='#03152f',fg=WHITE,insertbackground='white',relief='flat',highlightbackground=CYAN,highlightthickness=1,font=('Segoe UI',11),show=show)
class Auth:
 def __init__(self, mode='user'):
  self.mode=mode
  self.root=tk.Tk(); self.root.title('SS Mailer • '+('Admin Panel' if mode=='admin' else 'Secure Login')); self.root.geometry('480x520'); self.root.configure(bg=BG); self.root.resizable(False,False)
  try: self.root.iconbitmap(os.path.join(BASE,'ss_mailer.ico'))
  except: pass
  if mode=='admin': self.admin_gate()
  else: self.login_page()
  self.root.mainloop()
 def admin_gate(self):
  f=self.card('ADMINISTRATOR LOGIN')
  tk.Label(f,text='Admin Password',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=24,pady=(35,5))
  self.admin_pw=entry(f,'●'); self.admin_pw.pack(fill='x',padx=24,ipady=8)
  styled_button(f,'OPEN ADMIN PANEL',self.admin_login,'#5a19bb').pack(fill='x',padx=24,pady=24)
  tk.Label(f,text='AUTHORIZED ADMIN ACCESS ONLY',bg=PANEL,fg=CYAN,font=('Segoe UI',9)).pack(pady=12)
  self.admin_pw.bind('<Return>',lambda e:self.admin_login())
 def card(self,title):
  for w in self.root.winfo_children(): w.destroy()
  tk.Label(self.root,text='✉  SS Mailer V0.1',bg=BG,fg=CYAN,font=('Segoe UI',22,'bold')).pack(pady=(28,4))
  tk.Label(self.root,text=title,bg=BG,fg=WHITE,font=('Segoe UI',14,'bold')).pack(pady=(0,20))
  f=tk.Frame(self.root,bg=PANEL,highlightbackground=PURPLE,highlightthickness=2); f.pack(fill='both',expand=True,padx=28,pady=(0,22)); return f
 def login_page(self):
  f=self.card('SECURE USER LOGIN')
  tk.Label(f,text='Username',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=24,pady=(25,5)); self.un=entry(f); self.un.pack(fill='x',padx=24,ipady=8)
  tk.Label(f,text='Password',bg=PANEL,fg=MUTED,font=('Segoe UI',10)).pack(anchor='w',padx=24,pady=(15,5)); self.pw=entry(f,'●'); self.pw.pack(fill='x',padx=24,ipady=8)
  styled_button(f,'LOGIN',self.login,'#075ff5').pack(fill='x',padx=24,pady=22)
  tk.Label(f,text='RGB • SECURE • PROFESSIONAL',bg=PANEL,fg=CYAN,font=('Segoe UI',9)).pack(pady=16)
  self.pw.bind('<Return>',lambda e:self.login())
 def login(self):
  u=self.un.get().strip(); p=self.pw.get()
  c=db(); r=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone(); c.close()
  if not r or r['password']!=digest(p): messagebox.showerror('Login Failed','Invalid username or password.'); return
  if datetime.fromisoformat(r['expires']) < datetime.now(): messagebox.showerror('Expired','This account validity has expired.'); return
  if r['used']>=r['sending_limit']: messagebox.showerror('Limit Reached','Your sending limit is exhausted.'); return
  devices=json.loads(r['devices'])
  if DEVICE not in devices:
   if len(devices)>=r['device_limit']: messagebox.showerror('Device Limit','This account has reached its device limit.'); return
   devices.append(DEVICE); c=db(); c.execute('UPDATE users SET devices=? WHERE username=?',(json.dumps(devices),u)); c.commit(); c.close()
  self.root.destroy(); launch_mailer(u)
 def admin_login(self):
  if self.mode=='admin':
   c=db(); r=c.execute("SELECT v FROM settings WHERE k='admin_hash'").fetchone(); c.close()
   if r and digest(self.admin_pw.get())==r['v']:
    for child in self.root.winfo_children(): child.destroy()
    self.admin_panel(); self.root.withdraw()
   else: messagebox.showerror('Access Denied','Incorrect admin password.',parent=self.root)
   return
  w=tk.Toplevel(self.root); w.title('Admin Authentication'); w.geometry('350x210'); w.configure(bg=BG); w.transient(self.root); w.grab_set()
  tk.Label(w,text='ADMIN PASSWORD',bg=BG,fg=CYAN,font=('Segoe UI',14,'bold')).pack(pady=20)
  e=entry(w,'●'); e.pack(fill='x',padx=24,ipady=8)
  def check():
   c=db(); r=c.execute("SELECT v FROM settings WHERE k='admin_hash'").fetchone(); c.close()
   if r and digest(e.get())==r['v']: w.destroy(); self.admin_panel()
   else: messagebox.showerror('Access Denied','Incorrect admin password.',parent=w)
  styled_button(w,'ENTER ADMIN PANEL',check).pack(fill='x',padx=24,pady=16)
 def admin_panel(self):
  w=tk.Toplevel(self.root); w.title('SS Mailer • Admin Panel'); w.geometry('1020x700'); w.configure(bg=BG); w.minsize(900,620)
  try:w.iconbitmap(os.path.join(BASE,'ss_mailer.ico'))
  except:pass
  tk.Label(w,text='✉ SS Mailer  |  ADMIN PANEL',bg=BG,fg=CYAN,font=('Segoe UI',20,'bold')).pack(anchor='w',padx=20,pady=15)
  main=tk.Frame(w,bg=BG); main.pack(fill='both',expand=True,padx=16,pady=5)
  left=tk.Frame(main,bg=PANEL,highlightbackground=CYAN,highlightthickness=1); left.pack(side='left',fill='y',padx=(0,12))
  right=tk.Frame(main,bg=PANEL,highlightbackground=PURPLE,highlightthickness=1); right.pack(side='left',fill='both',expand=True)
  fields={}
  for label,key,default in [('Username','username',''),('Password','password',''),('Validity (days)','days','30'),('Device Limit','devices','1'),('Sending Limit','limit','100')]:
   tk.Label(left,text=label,bg=PANEL,fg=WHITE,font=('Segoe UI',10)).pack(anchor='w',padx=14,pady=(10,3)); e=entry(left,'●' if key=='password' else None); e.insert(0,default); e.pack(fill='x',padx=14,ipady=5); fields[key]=e
  selected=[None]
  def refresh(select=None):
   for i in tree.get_children(): tree.delete(i)
   c=db(); rows=c.execute('SELECT * FROM users ORDER BY username').fetchall(); c.close()
   for r in rows: tree.insert('', 'end', values=(r['username'],r['expires'],r['device_limit'],f"{max(0,r['sending_limit']-r['used'])}/{r['sending_limit']}",len(json.loads(r['devices']))))
   if select:
    for i in tree.get_children():
     if tree.item(i,'values')[0]==select: tree.selection_set(i); tree.see(i); break
  def create():
   u=fields['username'].get().strip(); p=fields['password'].get();
   try: days=int(fields['days'].get()); dev=int(fields['devices'].get()); lim=int(fields['limit'].get())
   except: messagebox.showerror('Invalid','Days, device limit and sending limit must be numbers.',parent=w); return
   if not u or not p or min(days,dev,lim)<1: messagebox.showerror('Invalid','Enter all fields. Numeric values must be at least 1.',parent=w); return
   c=db()
   try:c.execute('INSERT INTO users(username,password,expires,device_limit,sending_limit,used,devices,created) VALUES(?,?,?,?,?,0,?,?)',(u,digest(p),(datetime.now()+timedelta(days=days)).isoformat(timespec='seconds'),dev,lim,'[]',datetime.now().isoformat(timespec='seconds'))); c.commit()
   except sqlite3.IntegrityError: messagebox.showerror('Exists','Username already exists.',parent=w); c.close(); return
   c.close(); refresh(u); messagebox.showinfo('Created','User created successfully.',parent=w)
  def load(_=None):
   sel=tree.selection()
   if not sel:return
   u=tree.item(sel[0],'values')[0]; c=db(); r=c.execute('SELECT * FROM users WHERE username=?',(u,)).fetchone(); c.close()
   if not r:return
   for key,val in [('username',r['username']),('password',''),('days',max(1,(datetime.fromisoformat(r['expires'])-datetime.now()).days)),('devices',r['device_limit']),('limit',r['sending_limit'])]: fields[key].delete(0,'end'); fields[key].insert(0,str(val))
   selected[0]=u
  def edit():
   u=selected[0]
   if not u: messagebox.showwarning('Select User','Select a user in the table first.',parent=w); return
   try: days=int(fields['days'].get()); dev=int(fields['devices'].get()); lim=int(fields['limit'].get())
   except: messagebox.showerror('Invalid','Numeric fields are invalid.',parent=w); return
   newu=fields['username'].get().strip(); p=fields['password'].get()
   if not newu or min(days,dev,lim)<1:return
   c=db(); exp=(datetime.now()+timedelta(days=days)).isoformat(timespec='seconds')
   if p: c.execute('UPDATE users SET username=?,password=?,expires=?,device_limit=?,sending_limit=? WHERE username=?',(newu,digest(p),exp,dev,lim,u))
   else:c.execute('UPDATE users SET username=?,expires=?,device_limit=?,sending_limit=? WHERE username=?',(newu,exp,dev,lim,u))
   c.commit(); c.close(); selected[0]=newu; refresh(newu); messagebox.showinfo('Updated','User details updated.',parent=w)
  def delete():
   sel=tree.selection()
   if not sel:return
   u=tree.item(sel[0],'values')[0]
   if messagebox.askyesno('Delete User',f'Delete {u}?',parent=w):
    c=db(); c.execute('DELETE FROM users WHERE username=?',(u,)); c.commit(); c.close(); selected[0]=None; refresh()
  styled_button(left,'CREATE USER',create,'#0869f7').pack(fill='x',padx=14,pady=(18,6)); styled_button(left,'EDIT SELECTED',edit,'#6b18c9').pack(fill='x',padx=14,pady=6); styled_button(left,'DELETE SELECTED',delete,'#c51b50').pack(fill='x',padx=14,pady=6)
  tk.Label(left,text='Default admin password:\nadmin123 (change in Settings)',bg=PANEL,fg='#ffcc66',font=('Segoe UI',9),justify='left').pack(anchor='w',padx=14,pady=14)
  search=tk.Frame(right,bg=PANEL); search.pack(fill='x',padx=12,pady=12); tk.Label(search,text='User Search',bg=PANEL,fg=WHITE,font=('Segoe UI',11,'bold')).pack(side='left'); q=entry(search); q.pack(side='left',fill='x',expand=True,padx=10,ipady=5)
  def search_user():
   term=q.get().strip().lower()
   for i in tree.get_children():
    tree.detach(i)
   c=db(); rows=c.execute('SELECT * FROM users WHERE lower(username) LIKE ? ORDER BY username',('%'+term+'%',)).fetchall(); c.close()
   for r in rows: tree.insert('', 'end', values=(r['username'],r['expires'],r['device_limit'],f"{max(0,r['sending_limit']-r['used'])}/{r['sending_limit']}",len(json.loads(r['devices']))))
  styled_button(search,'SEARCH',search_user).pack(side='left')
  cols=('Username','Validity Until','Device Limit','Limit Left / Total','Devices Used'); tree=ttk.Treeview(right,columns=cols,show='headings',height=18)
  for col in cols:tree.heading(col,text=col); tree.column(col,width=140,anchor='center')
  tree.pack(fill='both',expand=True,padx=12,pady=(0,12)); tree.bind('<<TreeviewSelect>>',load)
  sty=ttk.Style(); sty.theme_use('clam'); sty.configure('Treeview',background='#06152d',foreground=WHITE,fieldbackground='#06152d',rowheight=28); sty.configure('Treeview.Heading',background='#103362',foreground=CYAN)
  settings=tk.Frame(right,bg=PANEL); settings.pack(fill='x',padx=12,pady=(0,12)); np=entry(settings,'●'); np.pack(side='left',fill='x',expand=True,ipady=5); np.insert(0,'New admin password')
  def change_admin():
   v=np.get()
   if len(v)<8 or v=='New admin password': messagebox.showwarning('Password','Use at least 8 characters.',parent=w); return
   c=db(); c.execute("UPDATE settings SET v=? WHERE k='admin_hash'",(digest(v),)); c.commit(); c.close(); np.delete(0,'end'); messagebox.showinfo('Admin','Admin password changed.',parent=w)
  styled_button(settings,'CHANGE ADMIN PASSWORD',change_admin,'#5a19bb').pack(side='left',padx=8); refresh()
def launch_mailer(username):
 root=tk.Tk(); app=App(root)
 # User badge on the main application header
 try:
  header=root.winfo_children()[0]
  badge=tk.Frame(header,bg='#061a38'); badge.pack(side='right',padx=12)
  c=db(); r=c.execute('SELECT sending_limit,used FROM users WHERE username=?',(username,)).fetchone(); c.close()
  txt=tk.StringVar(value=f'👤  Account: {username}  |  Sent: {r["used"]}/{r["sending_limit"]}  |  Limit Left: {max(0,r["sending_limit"]-r["used"])}' if r else username)
  tk.Label(badge,textvariable=txt,bg='#061a38',fg=CYAN,font=('Segoe UI',9,'bold')).pack(side='left',padx=4)
  tk.Button(badge,text='Logout',command=root.destroy,bg='#b71c50',fg='white',relief='flat').pack(side='left',padx=4)
  app.auth_username=username; app.auth_limit_label=txt
  app._auth_refresh_limit=lambda: refresh_limit(username,txt)
 except Exception: pass
 root.mainloop()
def refresh_limit(username,var):
 c=db(); r=c.execute('SELECT sending_limit,used FROM users WHERE username=?',(username,)).fetchone(); c.close()
 if r: var.set(f'👤  Account: {username}  |  Sent: {r["used"]}/{r["sending_limit"]}  |  Limit Left: {max(0,r["sending_limit"]-r["used"])}')
if __name__=='__main__': Auth()
