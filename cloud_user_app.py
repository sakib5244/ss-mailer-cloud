import tkinter as tk, hashlib, socket, uuid, os
from tkinter import messagebox
from cloud_client import call, server_url, set_server_url, test_server_url
from ss_mailer import App
BG='#030d22'; PANEL='#061a38'; CYAN='#00c8ff'; PURPLE='#a100ff'; WHITE='#eef6ff'; MUTED='#a7c8ef'
def ent(p,show=None):return tk.Entry(p,bg='#03152f',fg=WHITE,insertbackground='white',relief='flat',highlightbackground=CYAN,highlightthickness=1,font=('Segoe UI',11),show=show)
def btn(p,t,cmd):return tk.Button(p,text=t,command=cmd,bg='#0869f7',fg='white',activebackground=PURPLE,relief='flat',font=('Segoe UI',10,'bold'),padx=12,pady=8,cursor='hand2')
class UserLogin:
 def __init__(self):
  self.root=tk.Tk(); self.root.title('SS Mailer • Secure Login'); self.root.geometry('460x560'); self.root.configure(bg=BG); self.root.resizable(False,False)
  try:self.root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ss_mailer.ico'))
  except:pass
  tk.Label(self.root,text='✉ SS Mailer',bg=BG,fg=CYAN,font=('Segoe UI',23,'bold')).pack(pady=(35,5)); tk.Label(self.root,text='SECURE CLOUD LOGIN',bg=BG,fg=WHITE,font=('Segoe UI',12,'bold')).pack(pady=(0,18)); card=tk.Frame(self.root,bg=PANEL,highlightbackground=PURPLE,highlightthickness=2); card.pack(fill='both',expand=True,padx=28,pady=(0,24))
  tk.Label(card,text='Cloud Server URL (same URL from Admin)',bg=PANEL,fg=MUTED).pack(anchor='w',padx=22,pady=(14,4)); self.url=ent(card);
  try: self.url.insert(0,server_url())
  except: pass
  self.url.pack(fill='x',padx=22,ipady=6); tk.Button(card,text='SAVE / TEST SERVER',command=self.test_url,bg='#6816b9',fg='white',relief='flat').pack(fill='x',padx=22,pady=(7,3)); tk.Label(card,text='Username',bg=PANEL,fg=MUTED).pack(anchor='w',padx=22,pady=(10,4)); self.u=ent(card); self.u.pack(fill='x',padx=22,ipady=8); tk.Label(card,text='Password',bg=PANEL,fg=MUTED).pack(anchor='w',padx=22,pady=(14,4)); self.p=ent(card,'●'); self.p.pack(fill='x',padx=22,ipady=8); btn(card,'LOGIN',self.login).pack(fill='x',padx=22,pady=20); tk.Label(card,text='RGB • SECURE • PROFESSIONAL',bg=PANEL,fg=CYAN,font=('Segoe UI',9)).pack(pady=8); self.p.bind('<Return>',lambda e:self.login()); self.root.mainloop()
 def test_url(self):
  try:
   u=set_server_url(self.url.get()); d=test_server_url(u); messagebox.showinfo('Server Connected',f"{d.get('service','SS Mailer API')}\nStatus: {d.get('status')}",parent=self.root)
  except Exception as e: messagebox.showerror('Server Connection',str(e),parent=self.root)
 def login(self):
  try:
   set_server_url(self.url.get())
   dev=hashlib.sha256((socket.gethostname()+str(uuid.getnode())).encode()).hexdigest()[:32]
   result=call('POST','/api/user/login',json={'username':self.u.get().strip(),'password':self.p.get(),'device_id':dev}); token=result['token']; username=result['user']['username']; self.root.destroy(); launch(username,token)
  except Exception as e:messagebox.showerror('Login Failed',str(e),parent=self.root)
def launch(username,token):
 root=tk.Tk(); app=App(root); app.cloud_token=token; app.auth_username=username
 try:
  header=root.winfo_children()[0]; badge=tk.Frame(header,bg='#061a38'); badge.pack(side='right',padx=10)
  status=call('GET','/api/me',token); user=status['user']; txt=tk.StringVar(value=f"👤  Account: {username}  |  Sent: {user.get('used', 0)}/{user.get('sending_limit', user['limit_left'] + user.get('used', 0))}  |  Limit Left: {user['limit_left']}")
  tk.Label(badge,textvariable=txt,bg='#061a38',fg=CYAN,font=('Segoe UI',9,'bold')).pack(side='left',padx=4)
  def logout():
   try:call('POST','/api/logout',token)
   except:pass
   root.destroy()
  tk.Button(badge,text='Logout',command=logout,bg='#b71c50',fg='white',relief='flat').pack(side='left',padx=4)
  app.auth_limit_label=txt
  def refresh():
   try:
    x=call('GET','/api/me',token)['user']; txt.set(f"👤  Account: {username}  |  Sent: {x.get('used', 0)}/{x.get('sending_limit', x['limit_left'] + x.get('used', 0))}  |  Limit Left: {x['limit_left']}")
   except:txt.set(f'{username}  |  Server unavailable')
  app._auth_refresh_limit=refresh
 except Exception as e:messagebox.showerror('Cloud Account',str(e),parent=root)
 root.mainloop()
if __name__=='__main__':UserLogin()
