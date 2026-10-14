import tkinter as tk
from tkinter import ttk,messagebox
from cloud_client import call, server_url, set_server_url, test_server_url
BG='#030d22'; PANEL='#061a38'; CYAN='#00c8ff'; PURPLE='#a100ff'; WHITE='#eef6ff'; MUTED='#a7c8ef'
def btn(p,t,cmd,color='#0869f7'): return tk.Button(p,text=t,command=cmd,bg=color,fg='white',relief='flat',font=('Segoe UI',10,'bold'),padx=10,pady=7,cursor='hand2')
def ent(p,show=None): return tk.Entry(p,bg='#03152f',fg=WHITE,insertbackground='white',relief='flat',highlightbackground=CYAN,highlightthickness=1,font=('Segoe UI',10),show=show)
class Admin:
 def __init__(self):
  self.root=tk.Tk(); self.root.title('SS Mailer • Cloud Admin'); self.root.geometry('1050x700'); self.root.configure(bg=BG); self.token=None; self.fields={}; self.selected=None; self.url_ui(); self.root.mainloop()
 def url_ui(self):
  for w in self.root.winfo_children(): w.destroy()
  tk.Label(self.root,text='✉ SS Mailer',bg=BG,fg=CYAN,font=('Segoe UI',24,'bold')).pack(pady=(95,10))
  tk.Label(self.root,text='CLOUD SERVER SETTINGS',bg=BG,fg=WHITE,font=('Segoe UI',14,'bold')).pack(pady=8)
  card=tk.Frame(self.root,bg=PANEL,highlightbackground=PURPLE,highlightthickness=2); card.pack(padx=230,fill='x',pady=15)
  tk.Label(card,text='Server URL (HTTPS)',bg=PANEL,fg=MUTED).pack(anchor='w',padx=20,pady=(20,5))
  self.url_entry=ent(card); 
  try: current=server_url()
  except: current=''
  self.url_entry.insert(0,current); self.url_entry.pack(fill='x',padx=20,ipady=7)
  row=tk.Frame(card,bg=PANEL); row.pack(fill='x',padx=20,pady=12)
  btn(row,'SAVE URL',self.save_url).pack(side='left',fill='x',expand=True,padx=(0,5))
  btn(row,'TEST CONNECTION',self.test_url,'#6816b9').pack(side='left',fill='x',expand=True,padx=(5,0))
  btn(card,'CONTINUE TO ADMIN LOGIN',self.login_ui).pack(fill='x',padx=20,pady=(4,20))
 def save_url(self):
  try: set_server_url(self.url_entry.get()); messagebox.showinfo('Saved','Server URL saved for this PC. Other PCs need the same URL configured in their app too.',parent=self.root)
  except Exception as e: messagebox.showerror('Server URL',str(e),parent=self.root)
 def test_url(self):
  try:
   u=set_server_url(self.url_entry.get()); data=test_server_url(u); messagebox.showinfo('Connection OK',f"Connected: {data.get('service','SS Mailer API')}\nStatus: {data.get('status')}",parent=self.root)
  except Exception as e: messagebox.showerror('Connection Failed',str(e),parent=self.root)
 def login_ui(self):
  for w in self.root.winfo_children(): w.destroy()
  tk.Label(self.root,text='✉ SS Mailer',bg=BG,fg=CYAN,font=('Segoe UI',24,'bold')).pack(pady=(100,10)); tk.Label(self.root,text='CLOUD ADMIN LOGIN',bg=BG,fg=WHITE,font=('Segoe UI',14,'bold')).pack(pady=10)
  card=tk.Frame(self.root,bg=PANEL,highlightbackground=PURPLE,highlightthickness=2); card.pack(padx=300,fill='x',pady=15); tk.Label(card,text='Admin Password',bg=PANEL,fg=MUTED).pack(anchor='w',padx=20,pady=(20,5)); self.pw=ent(card,'●'); self.pw.pack(fill='x',padx=20,ipady=7); btn(card,'LOGIN',self.login).pack(fill='x',padx=20,pady=20); btn(card,'SERVER SETTINGS',self.url_ui,'#344861').pack(fill='x',padx=20,pady=(0,20)); self.pw.bind('<Return>',lambda e:self.login())
 def login(self):
  try: self.token=call('POST','/api/admin/login',json={'password':self.pw.get()})['token']; self.root.winfo_children()[0].destroy(); [w.destroy() for w in self.root.winfo_children()]; self.panel()
  except Exception as e: messagebox.showerror('Login Failed',str(e),parent=self.root)
 def panel(self):
  tk.Label(self.root,text='✉ SS Mailer  |  CLOUD ADMIN PANEL',bg=BG,fg=CYAN,font=('Segoe UI',20,'bold')).pack(anchor='w',padx=18,pady=14)
  main=tk.Frame(self.root,bg=BG); main.pack(fill='both',expand=True,padx=15,pady=5); left=tk.Frame(main,bg=PANEL,highlightbackground=CYAN,highlightthickness=1); left.pack(side='left',fill='y',padx=(0,12)); right=tk.Frame(main,bg=PANEL,highlightbackground=PURPLE,highlightthickness=1); right.pack(side='left',fill='both',expand=True)
  for label,key,default in [('Username','username',''),('Password (8+ chars)','password',''),('Validity (days)','days','30'),('Device Limit','devices','1'),('Sending Limit','limit','100')]:
   tk.Label(left,text=label,bg=PANEL,fg=WHITE,font=('Segoe UI',9)).pack(anchor='w',padx=12,pady=(9,3)); e=ent(left,'●' if key=='password' else None); e.insert(0,default); e.pack(fill='x',padx=12,ipady=5); self.fields[key]=e
  btn(left,'MANAGE SUBADMINS',self.manage_subadmins,'#6816b9').pack(fill='x',padx=12,pady=(10,5)); btn(left,'CREATE USER',self.create).pack(fill='x',padx=12,pady=(8,5)); btn(left,'UPDATE SELECTED',self.edit,'#6816b9').pack(fill='x',padx=12,pady=5); btn(left,'DELETE SELECTED',self.delete,'#bf2451').pack(fill='x',padx=12,pady=5); btn(left,'CLEAR FORM',self.clear,'#344861').pack(fill='x',padx=12,pady=5); btn(left,'LOGOUT',self.logout,'#bf2451').pack(fill='x',padx=12,pady=5)
  top=tk.Frame(right,bg=PANEL); top.pack(fill='x',padx=12,pady=12); self.q=ent(top); self.q.pack(side='left',fill='x',expand=True,ipady=6); btn(top,'SEARCH',self.refresh).pack(side='left',padx=8); btn(top,'SHOW ALL',lambda:self.refresh(True),'#344861').pack(side='left')
  cols=('Username','Validity Until','Devices','Limit Left / Total','Status'); self.tree=ttk.Treeview(right,columns=cols,show='headings');
  for col in cols: self.tree.heading(col,text=col); self.tree.column(col,width=135,anchor='center')
  self.tree.pack(fill='both',expand=True,padx=12,pady=(0,12)); self.tree.bind('<<TreeviewSelect>>',self.load); st=ttk.Style(); st.theme_use('clam'); st.configure('Treeview',background='#06152d',foreground=WHITE,fieldbackground='#06152d',rowheight=28); st.configure('Treeview.Heading',background='#103362',foreground=CYAN); self.refresh(True)
 def manage_subadmins(self):
  win=tk.Toplevel(self.root); win.title('SS Mailer • Subadmin Manager'); win.geometry('900x600'); win.configure(bg=BG)
  left=tk.Frame(win,bg=PANEL); left.pack(side='left',fill='y',padx=12,pady=12); right=tk.Frame(win,bg=PANEL); right.pack(side='left',fill='both',expand=True,padx=(0,12),pady=12)
  fields={}
  for label,key,default in [('Name','name',''),('Phone','phone',''),('Username','username',''),('Password (8+ chars; blank keeps current)','password',''),('Device/User Limit','device_limit','10')]:
   tk.Label(left,text=label,bg=PANEL,fg=WHITE).pack(anchor='w',padx=12,pady=(8,3)); e=ent(left,'●' if key=='password' else None); e.insert(0,default); e.pack(fill='x',padx=12,ipady=5); fields[key]=e
  selected={'username':None}
  cols=('Username','Name','Phone','User Count','Active Users','Limit','Status'); tree=ttk.Treeview(right,columns=cols,show='headings')
  for col in cols: tree.heading(col,text=col); tree.column(col,width=105,anchor='center')
  tree.pack(fill='both',expand=True,padx=10,pady=10)
  def load_rows():
   try:
    data=call('GET','/api/admin/subadmins',self.token)['subadmins']
    for i in tree.get_children(): tree.delete(i)
    for a in data: tree.insert('','end',values=(a['username'],a['name'],a['phone'],a['user_count'],a['active_user_count'],a['device_limit'],'Active' if a['active'] else 'Disabled'))
   except Exception as e: messagebox.showerror('Subadmins',str(e),parent=win)
  def on_select(_=None):
   sel=tree.selection()
   if not sel:return
   v=tree.item(sel[0],'values'); selected['username']=v[0]
   for k,val in [('username',v[0]),('name',v[1]),('phone',v[2]),('device_limit',v[5])]: fields[k].delete(0,'end'); fields[k].insert(0,val)
   fields['password'].delete(0,'end')
  def clear():
   selected['username']=None
   for k,e in fields.items(): e.delete(0,'end')
   fields['device_limit'].insert(0,'10')
  def save():
   try:
    d={k:e.get().strip() for k,e in fields.items()}; d['device_limit']=int(d['device_limit'])
    if selected['username']:
     old=selected['username']; d['active']=True
     call('PUT','/api/admin/subadmins/'+requests_quote(old),self.token,json=d)
    else: call('POST','/api/admin/subadmins',self.token,json=d)
    load_rows(); clear(); messagebox.showinfo('Saved','Subadmin details saved.',parent=win)
   except Exception as e: messagebox.showerror('Save Subadmin',str(e),parent=win)
  def delete():
   if not selected['username']: return
   if messagebox.askyesno('Delete Subadmin','Delete '+selected['username']+'? Their users will be moved to Main Admin.',parent=win):
    try: call('DELETE','/api/admin/subadmins/'+requests_quote(selected['username']),self.token); load_rows(); clear()
    except Exception as e: messagebox.showerror('Delete Subadmin',str(e),parent=win)
  btn(left,'CREATE / SAVE',save).pack(fill='x',padx=12,pady=(18,5)); btn(left,'CLEAR',clear,'#344861').pack(fill='x',padx=12,pady=5); btn(left,'DELETE SELECTED',delete,'#bf2451').pack(fill='x',padx=12,pady=5); btn(right,'REFRESH LIST',load_rows,'#344861').pack(anchor='e',padx=10,pady=(0,8)); tree.bind('<<TreeviewSelect>>',on_select); load_rows()

 def values(self):
  try:return {'username':self.fields['username'].get().strip(),'password':self.fields['password'].get(),'validity_days':int(self.fields['days'].get()),'device_limit':int(self.fields['devices'].get()),'sending_limit':int(self.fields['limit'].get())}
  except ValueError: raise RuntimeError('Validity, device limit and sending limit must be whole numbers.')
 def create(self):
  try: d=self.values(); call('POST','/api/admin/users',self.token,json=d); self.refresh(True); messagebox.showinfo('Created','User created successfully.',parent=self.root); self.clear()
  except Exception as e: messagebox.showerror('Create User',str(e),parent=self.root)
 def refresh(self,all_users=False):
  try:
   data=call('GET','/api/admin/users'+('' if all_users else '?q='+requests_quote(self.q.get())),self.token)['users'];
   for i in self.tree.get_children():self.tree.delete(i)
   for u in data:self.tree.insert('','end',values=(u['username'],u['expires_at'][:10],f"{u['devices_used']}/{u['device_limit']}",f"{u['limit_left']}/{u['sending_limit']}",'Active' if u['active'] else 'Disabled'))
  except Exception as e: messagebox.showerror('Cloud API',str(e),parent=self.root)
 def load(self,_=None):
  sel=self.tree.selection()
  if not sel:return
  vals=self.tree.item(sel[0],'values'); self.selected=vals[0]; self.fields['username'].delete(0,'end'); self.fields['username'].insert(0,vals[0]); self.fields['password'].delete(0,'end'); self.fields['days'].delete(0,'end'); self.fields['days'].insert(0,'30'); self.fields['devices'].delete(0,'end'); self.fields['devices'].insert(0,vals[2].split('/')[1]); self.fields['limit'].delete(0,'end'); self.fields['limit'].insert(0,vals[3].split('/')[1])
  messagebox.showinfo('Edit User','Enter the remaining validity days. Leave Password blank to keep the current password.',parent=self.root)
 def edit(self):
  if not self.selected: messagebox.showwarning('Select User','Select a row first.',parent=self.root); return
  try:
   d=self.values(); pw=d.pop('password'); d['active']=True
   if not pw:d.pop('password',None)
   call('PUT','/api/admin/users/'+requests_quote(self.selected),self.token,json=d); self.selected=d['username']; self.refresh(True); messagebox.showinfo('Updated','User updated.',parent=self.root)
  except Exception as e: messagebox.showerror('Update User',str(e),parent=self.root)
 def delete(self):
  if not self.selected:return
  if messagebox.askyesno('Delete User','Delete '+self.selected+'?',parent=self.root):
   try:call('DELETE','/api/admin/users/'+requests_quote(self.selected),self.token); self.selected=None; self.refresh(True); self.clear()
   except Exception as e:messagebox.showerror('Delete User',str(e),parent=self.root)
 def clear(self):
  self.selected=None
  for k,e in self.fields.items():e.delete(0,'end')
  for k,v in [('days','30'),('devices','1'),('limit','100')]:self.fields[k].insert(0,v)
 def logout(self):
  try:call('POST','/api/logout',self.token)
  except:pass
  self.root.destroy()
def requests_quote(s):
 from urllib.parse import quote
 return quote(str(s),safe='')
if __name__=='__main__': Admin()
