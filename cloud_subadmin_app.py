import tkinter as tk
from tkinter import ttk, messagebox
from urllib.parse import quote
from cloud_client import call, server_url, set_server_url, test_server_url
BG='#030d22'; PANEL='#061a38'; CYAN='#00c8ff'; PURPLE='#a100ff'; WHITE='#eef6ff'; MUTED='#a7c8ef'
def ent(p,show=None): return tk.Entry(p,bg='#03152f',fg=WHITE,insertbackground='white',relief='flat',highlightbackground=CYAN,highlightthickness=1,font=('Segoe UI',10),show=show)
def btn(p,t,cmd,color='#0869f7'): return tk.Button(p,text=t,command=cmd,bg=color,fg='white',relief='flat',font=('Segoe UI',9,'bold'),padx=9,pady=7,cursor='hand2')
class SubadminApp:
 def __init__(self):
  self.root=tk.Tk(); self.root.title('SS Mailer • Subadmin'); self.root.geometry('1050x680'); self.root.configure(bg=BG); self.token=None; self.selected=None; self.login_ui(); self.root.mainloop()
 def login_ui(self):
  for w in self.root.winfo_children(): w.destroy()
  tk.Label(self.root,text='✉ SS Mailer',bg=BG,fg=CYAN,font=('Segoe UI',24,'bold')).pack(pady=(55,8)); tk.Label(self.root,text='SUBADMIN LOGIN',bg=BG,fg=WHITE,font=('Segoe UI',14,'bold')).pack(pady=5)
  card=tk.Frame(self.root,bg=PANEL,highlightbackground=PURPLE,highlightthickness=2); card.pack(padx=260,fill='x',pady=12)
  tk.Label(card,text='Cloud Server URL',bg=PANEL,fg=MUTED).pack(anchor='w',padx=20,pady=(14,4)); self.url=ent(card)
  try:self.url.insert(0,server_url())
  except:pass
  self.url.pack(fill='x',padx=20,ipady=6); btn(card,'SAVE / TEST SERVER',self.test_url,'#6816b9').pack(fill='x',padx=20,pady=6)
  tk.Label(card,text='Username',bg=PANEL,fg=MUTED).pack(anchor='w',padx=20,pady=(8,4)); self.u=ent(card); self.u.pack(fill='x',padx=20,ipady=7)
  tk.Label(card,text='Password',bg=PANEL,fg=MUTED).pack(anchor='w',padx=20,pady=(10,4)); self.p=ent(card,'●'); self.p.pack(fill='x',padx=20,ipady=7)
  btn(card,'LOGIN',self.login).pack(fill='x',padx=20,pady=16); self.p.bind('<Return>',lambda e:self.login())
 def test_url(self):
  try:
   u=set_server_url(self.url.get()); d=test_server_url(u); messagebox.showinfo('Server Connected',f"{d.get('service')}\nStatus: {d.get('status')}",parent=self.root)
  except Exception as e:messagebox.showerror('Server Connection',str(e),parent=self.root)
 def login(self):
  try:
   set_server_url(self.url.get()); r=call('POST','/api/subadmin/login',json={'username':self.u.get().strip(),'password':self.p.get()}); self.token=r['token']; self.profile=r['subadmin']; self.panel()
  except Exception as e:messagebox.showerror('Login Failed',str(e),parent=self.root)
 def panel(self):
  for w in self.root.winfo_children():w.destroy()
  tk.Label(self.root,text='✉ SS Mailer  |  SUBADMIN PANEL',bg=BG,fg=CYAN,font=('Segoe UI',19,'bold')).pack(anchor='w',padx=15,pady=12)
  tk.Label(self.root,text=f"My Profile: {self.profile.get('name')}  |  Phone: {self.profile.get('phone')}  |  Username: {self.profile.get('username')}  |  User Limit: {self.profile.get('device_limit')}",bg=BG,fg=WHITE,font=('Segoe UI',10,'bold')).pack(anchor='w',padx=16,pady=(0,10))
  main=tk.Frame(self.root,bg=BG); main.pack(fill='both',expand=True,padx=12,pady=4); left=tk.Frame(main,bg=PANEL); left.pack(side='left',fill='y',padx=(0,10)); right=tk.Frame(main,bg=PANEL); right.pack(side='left',fill='both',expand=True)
  self.fields={}
  for label,key,default in [('Username','username',''),('Password (8+ chars)','password',''),('Validity days','days','30'),('Device Limit','devices','1'),('Sending Limit','limit','100')]:
   tk.Label(left,text=label,bg=PANEL,fg=WHITE).pack(anchor='w',padx=10,pady=(8,3)); e=ent(left,'●' if key=='password' else None); e.insert(0,default); e.pack(fill='x',padx=10,ipady=5); self.fields[key]=e
  btn(left,'CREATE USER',self.create).pack(fill='x',padx=10,pady=(15,5)); btn(left,'UPDATE SELECTED',self.update,'#6816b9').pack(fill='x',padx=10,pady=5); btn(left,'DELETE SELECTED',self.delete,'#bf2451').pack(fill='x',padx=10,pady=5); btn(left,'CLEAR FORM',self.clear,'#344861').pack(fill='x',padx=10,pady=5); btn(left,'LOGOUT',self.logout,'#bf2451').pack(fill='x',padx=10,pady=5)
  top=tk.Frame(right,bg=PANEL); top.pack(fill='x',padx=10,pady=10); self.q=ent(top); self.q.pack(side='left',fill='x',expand=True,ipady=6); btn(top,'SEARCH',self.refresh).pack(side='left',padx=6); btn(top,'SHOW ALL',lambda:self.refresh(True),'#344861').pack(side='left')
  cols=('Username','Validity Until','Devices','Limit Left / Total','Status'); self.tree=ttk.Treeview(right,columns=cols,show='headings')
  for col in cols:self.tree.heading(col,text=col); self.tree.column(col,width=135,anchor='center')
  self.tree.pack(fill='both',expand=True,padx=10,pady=(0,10)); self.tree.bind('<<TreeviewSelect>>',self.load); st=ttk.Style(); st.theme_use('clam'); st.configure('Treeview',background='#06152d',foreground=WHITE,fieldbackground='#06152d',rowheight=28); st.configure('Treeview.Heading',background='#103362',foreground=CYAN); self.refresh(True)
 def vals(self):
  try:return {'username':self.fields['username'].get().strip(),'password':self.fields['password'].get(),'validity_days':int(self.fields['days'].get()),'device_limit':int(self.fields['devices'].get()),'sending_limit':int(self.fields['limit'].get())}
  except:raise RuntimeError('Validity, device limit and sending limit must be whole numbers.')
 def create(self):
  try:call('POST','/api/subadmin/users',self.token,json=self.vals()); self.refresh(True); self.clear(); messagebox.showinfo('Created','User created.',parent=self.root)
  except Exception as e:messagebox.showerror('Create User',str(e),parent=self.root)
 def refresh(self,all_users=False):
  try:
   q='' if all_users else '?q='+quote(self.q.get()); rows=call('GET','/api/subadmin/users'+q,self.token)['users']
   for i in self.tree.get_children():self.tree.delete(i)
   for u in rows:self.tree.insert('','end',values=(u['username'],u['expires_at'][:10],f"{u['devices_used']}/{u['device_limit']}",f"{u['limit_left']}/{u['sending_limit']}",'Active' if u['active'] else 'Disabled'))
  except Exception as e:messagebox.showerror('Cloud API',str(e),parent=self.root)
 def load(self,_=None):
  sel=self.tree.selection()
  if not sel:return
  v=self.tree.item(sel[0],'values'); self.selected=v[0]
  for k,val in [('username',v[0]),('devices',v[2].split('/')[1]),('limit',v[3].split('/')[1])]:self.fields[k].delete(0,'end');self.fields[k].insert(0,val)
  self.fields['password'].delete(0,'end'); self.fields['days'].delete(0,'end');self.fields['days'].insert(0,'30')
 def update(self):
  if not self.selected:messagebox.showwarning('Select User','Select a user row first.',parent=self.root);return
  try:
   d=self.vals(); old=self.selected
   if not d['password']:d.pop('password')
   call('PUT','/api/subadmin/users/'+quote(old,safe=''),self.token,json=d); self.selected=d['username']; self.refresh(True); messagebox.showinfo('Updated','User updated.',parent=self.root)
  except Exception as e:messagebox.showerror('Update User',str(e),parent=self.root)
 def delete(self):
  if not self.selected:return
  if messagebox.askyesno('Delete User','Delete '+self.selected+'?',parent=self.root):
   try:call('DELETE','/api/subadmin/users/'+quote(self.selected,safe=''),self.token);self.selected=None;self.refresh(True);self.clear()
   except Exception as e:messagebox.showerror('Delete User',str(e),parent=self.root)
 def clear(self):
  self.selected=None
  for k,e in self.fields.items():e.delete(0,'end')
  for k,v in [('days','30'),('devices','1'),('limit','100')]:self.fields[k].insert(0,v)
 def logout(self):
  try:call('POST','/api/logout',self.token)
  except:pass
  self.token=None;self.login_ui()
if __name__=='__main__':SubadminApp()
