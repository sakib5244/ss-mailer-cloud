import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import os
import tempfile
import threading, queue, re, json, base64, csv, time, random, string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
from email.mime.base import MIMEBase
from email import encoders
from html.parser import HTMLParser
from html import escape as html_escape
from io import BytesIO

BG = '#03132b'; PANEL = '#041a37'; PANEL2 = '#061f40'; BORDER = '#078cff'; TEXT = '#eaf4ff'; MUTED = '#a9c8ef'; BLUE = '#0869f7'; GREEN = '#00bd78'; RED = '#f51650'; CYAN = '#00baff'

def st_all_done(stats):
    return stats.get('remaining', 0) == 0

class App:
    def __init__(self, root):
        self.root = root
        root.title('SS Mailer V0.1')
        root.geometry('1000x650')
        root.minsize(1000, 650)
        root.maxsize(1000, 650)
        root.configure(bg=BG)
        self.task = 1
        self.json_path = tk.StringVar(value='No JSON file selected')
        self.name_count = tk.IntVar(value=10)
        self.change_name = tk.BooleanVar(value=False)
        self.task_names = {}
        self.task_json_paths = {}
        self.used_names = set()
        self.name = tk.StringVar()
        self.tfn = tk.StringVar()
        self.send_format = tk.StringVar(value='PDF')
        self.header_mode = tk.StringVar(value='Mix')
        self.subjects = ['Your invoice #INVOICE# has been created successfully.', 'Forward:Invoice document #INVOICE#', 'The invoice #INVOICE# is enclosed for your records.']
        self.subject_index = 0
        self.task_configs = {}
        self.task_stats = {i: {'total': 0, 'sent': 0, 'failed': 0, 'remaining': 0, 'bounce': 0, 'checked': 0} for i in range(1,6)}
        self.worker = None
        self.stop_event = threading.Event()
        self.events = queue.Queue()
        self.token_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token.json')
        self._style()
        self._build()
        self._status_clock()

    def _style(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TCombobox', fieldbackground=PANEL2, background=PANEL2, foreground=TEXT, arrowcolor=TEXT)
        style.map('Dark.TCombobox', fieldbackground=[('readonly', PANEL2)], foreground=[('readonly', TEXT)])
        style.configure('Dark.Vertical.TScrollbar', background='#164a7c', troughcolor=PANEL2, arrowcolor=TEXT)

    def panel(self, parent, title=None, color=BORDER, padx=1, pady=1):
        f = tk.Frame(parent, bg=PANEL, highlightbackground=color, highlightthickness=1, bd=0)
        if title:
            h = tk.Frame(f, bg=PANEL2, height=29)
            h.pack(fill='x')
            h.pack_propagate(False)
            tk.Label(h, text=title, bg=PANEL2, fg=TEXT, font=('Segoe UI', 10, 'bold'), anchor='w', padx=9).pack(fill='both', expand=True)
        return f

    def button(self, parent, text, command=None, bg=BLUE, fg='white', height=1):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg, activebackground=bg, activeforeground='white', relief='flat', bd=0, font=('Segoe UI', 9, 'bold'), cursor='hand2', padx=7, pady=5, height=height)

    def entry(self, parent, var=None, text=None):
        e = tk.Entry(parent, textvariable=var, bg='#03152f', fg=TEXT, insertbackground='white', relief='flat', highlightbackground=BORDER, highlightcolor=CYAN, highlightthickness=1, font=('Segoe UI', 9))
        if text:
            e.insert(0, text)
        return e

    def editor(self, parent, hint):
        box = tk.Frame(parent, bg='#03152f', highlightbackground=BORDER, highlightthickness=1)
        t = tk.Text(box, bg='#03152f', fg=TEXT, insertbackground='white', relief='flat', wrap='word', font=('Consolas', 9), padx=7, pady=7, undo=True)
        sb = ttk.Scrollbar(box, command=t.yview, style='Dark.Vertical.TScrollbar')
        t.configure(yscrollcommand=sb.set)
        t.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')
        return box, t

    def _build(self):
        # Header
        header = tk.Frame(self.root, bg='#061a38', height=54)
        header.pack(fill='x')
        header.pack_propagate(False)
        tk.Label(header, text='✉  SS Mailer V0.1', bg='#061a38', fg=TEXT, font=('Segoe UI', 19, 'bold')).pack(side='left', padx=15)
        tk.Label(header, text='Bangladesh Mailer', bg='#061a38', fg=CYAN, font=('Segoe UI', 10, 'bold')).pack(side='left', padx=8, pady=(8,0))
        mode = tk.Frame(header, bg='#061a38'); mode.pack(side='right', padx=12)
        tk.Label(mode, text='Mode:', bg='#061a38', fg=TEXT, font=('Segoe UI', 9)).pack(side='left', padx=5)
        self.mode = ttk.Combobox(mode, values=['Mode 1', 'Mode 2'], state='readonly', width=9, style='Dark.TCombobox'); self.mode.current(0); self.mode.pack(side='left')

        # task cards
        tasks = tk.Frame(self.root, bg=BG); tasks.pack(fill='x', padx=12, pady=(7,6))
        self.task_cards=[]
        self.task_state_labels=[]
        colors=['#00baff','#00d59a','#a33dff','#ffb51b','#ff2680']
        for i,c in enumerate(colors,1):
            card=tk.Frame(tasks,bg=PANEL2,highlightbackground=c,highlightthickness=1,cursor='hand2')
            card.pack(side='left',fill='x',expand=True,padx=3)
            tk.Label(card,text=str(i),bg=c,fg='white',font=('Segoe UI',15,'bold'),width=2).pack(side='left',padx=7,pady=7)
            inner=tk.Frame(card,bg=PANEL2); inner.pack(side='left',fill='both',expand=True)
            tk.Label(inner,text=f'Task {i}',bg=PANEL2,fg=TEXT,font=('Segoe UI',9,'bold')).pack(anchor='w',pady=(5,0))
            state_label=tk.Label(inner,text='● Ready',bg=PANEL2,fg=GREEN,font=('Segoe UI',8)); state_label.pack(anchor='w')
            self.task_state_labels.append(state_label)
            card.bind('<Button-1>',lambda e,n=i:self.select_task(n))
            for child in card.winfo_children(): child.bind('<Button-1>',lambda e,n=i:self.select_task(n))
            self.task_cards.append((card,c))

        # main grid
        main=tk.Frame(self.root,bg=BG); main.pack(fill='both',expand=True,padx=12)
        main.grid_columnconfigure(0,weight=6,uniform='col'); main.grid_columnconfigure(1,weight=3,uniform='col'); main.grid_columnconfigure(2,weight=3,uniform='col')
        main.grid_rowconfigure(0,weight=5); main.grid_rowconfigure(1,weight=4)
        # left top configuration
        config=self.panel(main,'⚙  Task 1 - Configuration'); self._config_title=config.winfo_children()[0].winfo_children()[0] if config.winfo_children() else None; config.grid(row=0,column=0,sticky='nsew',padx=(0,5),pady=(0,5))
        tk.Label(config,text='Subject',bg=PANEL,fg=TEXT,font=('Segoe UI',9,'bold')).pack(anchor='w',padx=10,pady=(5,2))
        sr=tk.Frame(config,bg=PANEL); sr.pack(fill='x',padx=9)
        self.subject=self.entry(sr); self.subject.pack(side='left',fill='x',expand=True,ipady=5)
        self.button(sr,'⟳ Get Subject',self.get_subject).pack(side='left',padx=(6,0),ipady=2)
        editors=tk.Frame(config,bg=PANEL); editors.pack(fill='both',expand=True,padx=7,pady=7)
        for col in range(3): editors.grid_columnconfigure(col,weight=1,uniform='edit'); editors.grid_rowconfigure(1,weight=1)
        self.html_box,self.html=self.editor(editors,'Paste your HTML code here...')
        self.body_box,self.body=self.editor(editors,'Enter email body here...')
        self.data_box,self.data=self.editor(editors,'Enter recipient data here...')
        for col,(title,box) in enumerate([('‹/›  HTML',self.html_box),('▤  Body',self.body_box),('▤  Data',self.data_box)]):
            head=tk.Frame(editors,bg=PANEL)
            head.grid(row=0,column=col,sticky='ew',padx=4,pady=(0,3))
            tk.Label(head,text=title,bg=PANEL,fg=CYAN,font=('Segoe UI',9,'bold')).pack(side='left')
            if col == 0:
                self.button(head,'HTML Preview',self.preview_html,bg='#064a9d').pack(side='right',padx=(3,0))
            box.grid(row=1,column=col,sticky='nsew',padx=3)

        # left bottom task controls
        controls=self.panel(main,'ϟ  Task Controls'); controls.grid(row=1,column=0,sticky='nsew',padx=(0,5),pady=(0,0))
        row=tk.Frame(controls,bg=PANEL); row.pack(fill='x',padx=10,pady=8)
        self.button(row,'▶  Start',self.start,bg='#00b86b').pack(side='left',fill='x',expand=True,ipady=5,padx=(0,5))
        self.button(row,'■  Stop',self.stop,bg=RED).pack(side='left',fill='x',expand=True,ipady=5)
        tk.Label(controls,text='Current Task:',bg=PANEL,fg=TEXT,font=('Segoe UI',9)).pack(anchor='w',padx=10)
        self.current=ttk.Combobox(controls,values=[f'Task {i}' for i in range(1,6)],state='readonly',style='Dark.TCombobox'); self.current.current(0); self.current.pack(fill='x',padx=10,pady=(3,8))
        tk.Label(controls,text='Preview prototype only — sending is not connected.',bg=PANEL,fg=MUTED,font=('Segoe UI',8)).pack(anchor='w',padx=10,pady=(0,5))

        # middle top name + TFN + JSON
        mid=tk.Frame(main,bg=BG); mid.grid(row=0,column=1,rowspan=2,sticky='nsew',padx=1,pady=0)
        mid.grid_rowconfigure(2,weight=0); mid.grid_rowconfigure(3,weight=0); mid.grid_rowconfigure(4,weight=0); mid.grid_columnconfigure(0,weight=1)
        namep=self.panel(mid,'♟  Name'); namep.grid(row=0,column=0,sticky='ew',pady=(0,5))
        self.entry(namep,self.name,'').pack(fill='x',padx=8,pady=(7,5),ipady=4)
        r=tk.Frame(namep,bg=PANEL); r.pack(fill='x',padx=8,pady=(0,5))
        self.button(r,'♟ Get Name',self.get_name).pack(side='left')
        tk.Checkbutton(r,text='Change Name',variable=self.change_name,bg=PANEL,fg=TEXT,selectcolor=PANEL2,activebackground=PANEL,activeforeground=TEXT,font=('Segoe UI',8)).pack(side='left',padx=5)
        nr=tk.Frame(namep,bg=PANEL); nr.pack(fill='x',padx=8,pady=(0,7))
        tk.Label(nr,text='Name Count',bg=PANEL,fg=TEXT,font=('Segoe UI',8)).pack(side='left')
        tk.Spinbox(nr,from_=1,to=9999,textvariable=self.name_count,width=5,bg='#03152f',fg=TEXT,buttonbackground=PANEL2,insertbackground='white',relief='flat',highlightbackground=BORDER,highlightthickness=1,font=('Segoe UI',9)).pack(side='right')
        tfnp=self.panel(mid,'‹/›  TFN'); tfnp.grid(row=1,column=0,sticky='ew',pady=(0,5))
        self.entry(tfnp,self.tfn).pack(fill='x',padx=8,pady=7,ipady=4)
        jsonp=self.panel(mid,'▣  Upload JSON'); jsonp.grid(row=2,column=0,sticky='ew',pady=(0,5))
        self.button(jsonp,'☁ Choose JSON File',self.choose_json,bg='#064a9d').pack(fill='x',padx=8,pady=(8,4))
        self.json_label=tk.Label(jsonp,textvariable=self.json_path,bg=PANEL,fg=MUTED,font=('Segoe UI',8),wraplength=260,justify='left'); self.json_label.pack(fill='x',padx=8,pady=(0,8))
        fmtp=self.panel(mid,'▣  Format / Headers'); fmtp.grid(row=3,column=0,sticky='ew',pady=(0,5))
        tk.Label(fmtp,text='Format',bg=PANEL,fg=TEXT,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=8,pady=(5,1))
        self.format_combo=ttk.Combobox(fmtp,textvariable=self.send_format,values=['PDF','JPG Attach','PNG Attach','DOC Attach','Inline Image'],state='readonly',style='Dark.TCombobox')
        self.format_combo.pack(fill='x',padx=8,pady=(0,4))
        tk.Label(fmtp,text='Headers',bg=PANEL,fg=TEXT,font=('Segoe UI',8,'bold')).pack(anchor='w',padx=8,pady=(1,1))
        self.header_combo=ttk.Combobox(fmtp,textvariable=self.header_mode,values=['Mix','Gmail'],state='readonly',style='Dark.TCombobox')
        self.header_combo.pack(fill='x',padx=8,pady=(0,6))
        csvp=self.panel(mid,'▤  Recipient CSV'); csvp.grid(row=4,column=0,sticky='ew',pady=(0,5))
        self.csv_path=tk.StringVar(value='No CSV selected')
        self.button(csvp,'Choose CSV File',self.choose_csv,bg='#064a9d').pack(fill='x',padx=8,pady=5)
        tk.Label(csvp,textvariable=self.csv_path,bg=PANEL,fg=MUTED,font=('Segoe UI',8),wraplength=260).pack(fill='x',padx=8,pady=(0,5))

        # right panels
        right=tk.Frame(main,bg=BG); right.grid(row=0,column=2,rowspan=2,sticky='nsew',padx=(5,0))
        right.grid_columnconfigure(0,weight=1); right.grid_rowconfigure(0,weight=5); right.grid_rowconfigure(1,weight=3)
        tags=self.panel(right,'◆  Tags (Click to Copy)'); tags.grid(row=0,column=0,sticky='nsew',pady=(0,5))
        taglist=[('#INVOICE#','Invoice number (random)'),('#TRXID#','Transaction ID (random)'),('#RANDOMS#','Random string'),('#DATE#','Current date'),('#NAME#',"Recipient's Name"),('#EMAIL#',"Recipient's Email"),('#TIME#','Current time'),('#TFN#','TFN box value')]
        for tag,desc in taglist:
            rr=tk.Frame(tags,bg=PANEL); rr.pack(fill='x',padx=7,pady=2)
            self.button(rr,tag,lambda t=tag:self.copy_tag(t),bg='#0757d9').pack(side='left',ipady=0)
            tk.Label(rr,text='→  '+desc,bg=PANEL,fg=TEXT,font=('Segoe UI',8),anchor='w').pack(side='left',padx=5,fill='x',expand=True)
        self.button(tags,'Copy All Tags',self.copy_all,bg='#064a9d').pack(fill='x',padx=7,pady=5)
        bounce=self.panel(right,'⬟  Email Check (Bounce)'); bounce.grid(row=1,column=0,sticky='nsew',pady=(0,5))
        self.bounce_values={}
        for key,label,color in [('bounce','Bounced / Not Delivered',RED),('checked','Total Checked',GREEN)]:
            rr=tk.Frame(bounce,bg=PANEL); rr.pack(fill='x',padx=8,pady=3)
            tk.Label(rr,text='●',fg=color,bg=PANEL).pack(side='left')
            tk.Label(rr,text=label,fg=TEXT,bg=PANEL,font=('Segoe UI',8)).pack(side='left',padx=6)
            val=tk.Label(rr,text='0',fg=TEXT,bg=PANEL,font=('Segoe UI',9,'bold')); val.pack(side='right'); self.bounce_values[key]=val
        self.button(bounce,'↻ Check Bounce',self.check_bounce,bg='#064a9d').pack(fill='x',padx=7,pady=4)
        status=self.panel(right,'●  Layout / Status'); status.grid(row=2,column=0,sticky='nsew')
        self.status_values={}
        for key,label in [('total','Total Recipients'),('sent','Sent'),('failed','Failed'),('remaining','Remaining')]:
            rr=tk.Frame(status,bg=PANEL); rr.pack(fill='x',padx=8,pady=2)
            tk.Label(rr,text=label,bg=PANEL,fg=TEXT,font=('Segoe UI',8)).pack(side='left')
            val=tk.Label(rr,text='0',bg=PANEL,fg=TEXT,font=('Segoe UI',8,'bold')); val.pack(side='right'); self.status_values[key]=val
        self.progress=tk.Canvas(status,height=12,bg='#03152f',highlightthickness=1,highlightbackground=BORDER); self.progress.pack(fill='x',padx=8,pady=6); self.progress.create_rectangle(0,0,0,12,fill=GREEN,outline='')

        # Footer
        footer=tk.Frame(self.root,bg='#061a38',height=26,highlightbackground=BORDER,highlightthickness=1); footer.pack(fill='x',side='bottom',padx=12,pady=6); footer.pack_propagate(False)
        self.status_text=tk.Label(footer,text='●  Ready',bg='#061a38',fg=GREEN,font=('Segoe UI',8,'bold')); self.status_text.pack(side='left',padx=10)
        tk.Label(footer,text='SS Mailer V0.1 • UI Prototype',bg='#061a38',fg=TEXT,font=('Segoe UI',8)).pack(side='left',padx=20)
        self.clock=tk.Label(footer,text='',bg='#061a38',fg=MUTED,font=('Segoe UI',8)); self.clock.pack(side='right',padx=8)
        self.select_task(1)

    def select_task(self,n):
        # Save the current task's editable fields before switching.
        if hasattr(self, 'subject') and hasattr(self, 'task'):
            self.task_configs[self.task] = {
                'subject': self.subject.get(),
                'html': self.html.get('1.0', 'end-1c'),
                'body': self.body.get('1.0', 'end-1c'),
                'data': self.data.get('1.0', 'end-1c'),
                'name': self.name.get(),
                'json_path': self.json_path.get(),
                'send_format': self.send_format.get(),
                'header_mode': self.header_mode.get(),
            }
        self.task=n
        self.current.set(f'Task {n}')
        # Update configuration title and restore this task's independent fields.
        for child in self.root.winfo_children():
            pass
        try:
            config_title = self._config_title
            config_title.configure(text=f'⚙  Task {n} - Configuration')
        except AttributeError:
            pass
        cfg = self.task_configs.get(n, {})
        self.subject.delete(0, 'end'); self.subject.insert(0, cfg.get('subject', ''))
        self.name.set(cfg.get('name', self.task_names.get(n, '')))
        self.json_path.set(cfg.get('json_path', self.task_json_paths.get(n, 'No JSON file selected')))
        self.send_format.set(cfg.get('send_format','PDF'))
        self.header_mode.set(cfg.get('header_mode','Mix'))
        for widget, key, hint in [(self.html, 'html', 'Paste your HTML code here...'), (self.body, 'body', 'Enter email body here...'), (self.data, 'data', 'Enter recipient data here...')]:
            widget.delete('1.0', 'end')
            widget.insert('1.0', cfg.get(key, ''))
        for i,(card,c) in enumerate(self.task_cards,1):
            card.configure(highlightthickness=2 if i==n else 1)
        self.status_text.configure(text=f'●  Task {n} selected')
        self._refresh_stats()

    def preview_html(self):
        html = self.html.get('1.0', 'end-1c').strip()
        if not html:
            messagebox.showinfo('HTML Preview', 'Paste HTML code into the HTML box first.')
            return
        preview_values = self._make_tag_values('preview@example.com', self.name.get() or 'Preview User', self.tfn.get(), self.task_names.get(self.task, ''))
        html = self._replace_tags(html, preview_values)
        win = tk.Toplevel(self.root)
        win.title(f'SS Mailer - Task {self.task} HTML Preview')
        win.geometry('760x520')
        win.configure(bg=BG)
        try:
            from tkinterweb import HtmlFrame
            frame = HtmlFrame(win, messages_enabled=False)
            frame.pack(fill='both', expand=True)
            frame.load_html(html)
        except Exception:
            tk.Label(win, text='Install tkinterweb for rendered in-app HTML preview.', bg=BG, fg=TEXT, font=('Segoe UI', 11, 'bold')).pack(anchor='w', padx=12, pady=10)
            view = tk.Text(win, bg='#03152f', fg=TEXT, wrap='word')
            view.pack(fill='both', expand=True, padx=10, pady=(0,10))
            view.insert('1.0', html)
            view.configure(state='disabled')
        self.status_text.configure(text='●  HTML preview opened inside SS Mailer')

    def get_subject(self):
        self.subject.delete(0,'end'); self.subject.insert(0,self.subjects[self.subject_index % len(self.subjects)]); self.subject_index += 1

    def get_name(self):
        names = ['Olivia Bennett', 'Liam Carter', 'Emma Mitchell', 'Noah Parker', 'Amelia Brooks', 'Elijah Morgan', 'Sophia Reed', 'James Cooper', 'Isabella Hayes', 'Benjamin Foster', 'Mia Collins', 'Lucas Edwards', 'Charlotte Rivera', 'Henry Stewart', 'Evelyn Morris', 'Alexander Rogers', 'Harper Cook', 'Daniel Bailey', 'Abigail Bell', 'Matthew Murphy', 'Emily Kelly', 'Jackson Price', 'Elizabeth Ward', 'Sebastian Gray', 'Avery James', 'Jack Watson', 'Sofia Sanders', 'Aiden Ross', 'Ella Peterson', 'Owen Perry', 'Scarlett Powell', 'Samuel Long', 'Grace Patterson', 'David Hughes', 'Chloe Flores', 'Joseph Washington', 'Victoria Butler', 'John Simmons', 'Riley Bryant', 'Wyatt Alexander', 'Aria Russell', 'Luke Griffin', 'Lily Diaz', 'Gabriel Hayes', 'Zoey Myers', 'Anthony Ford', 'Nora Hamilton', 'Dylan Graham', 'Hannah Sullivan', 'Isaac Wallace', 'Addison Woods', 'Julian Cole', 'Ellie West', 'Levi Jordan', 'Stella Owens', 'Christopher Reynolds', 'Natalie Fisher', 'Joshua Ellis', 'Zoe Harrison', 'Andrew Gibson', 'Leah McDonald', 'Lincoln Cruz', 'Audrey Marshall', 'Nathan Ortiz', 'Claire Gomez', 'Aaron Murray', 'Skylar Freeman', 'Thomas Wells', 'Lucy Webb', 'Charles Simpson', 'Paisley Stevens', 'Caleb Tucker', 'Anna Porter', 'Ryan Hunter', 'Caroline Hicks', 'Adrian Crawford', 'Violet Henry', 'Jonathan Boyd', 'Naomi Mason', 'Christian Kennedy', 'Maya Warren', 'Eli Dixon', 'Sarah Ramos', 'Jeremiah Reyes', 'Alice Burns', 'Connor Gordon', 'Eva Shaw', 'Cameron Holmes', 'Madeline Rice', 'Ezekiel Robertson', 'Ruby Hunt', 'Angel Cooper', 'Kennedy Black', 'Miles Daniels', 'Samantha Palmer', 'Jason Mills', 'Piper Nichols', 'Adam Grant', 'Kinsley Knight', 'Ethan Ferguson', 'Autumn Rose']
        available = [n for n in names if n not in self.used_names]
        if not available:
            self.used_names.clear()
            available = names[:]
        chosen = random.choice(available)
        self.used_names.add(chosen)
        self.task_names[self.task] = chosen
        self.name.set(chosen)
        self.task_configs.setdefault(self.task, {})['name'] = chosen

    def choose_json(self):
        p=filedialog.askopenfilename(title='Choose JSON file',filetypes=[('JSON files','*.json'),('All files','*.*')])
        if p:
            self.json_path.set(p); self.task_json_paths[self.task] = p
            self.task_configs.setdefault(self.task, {})['json_path'] = p
            self.status_text.configure(text=f'●  JSON selected for Task {self.task}')

    def choose_csv(self):
        p=filedialog.askopenfilename(title='Choose recipient CSV',filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if p: self.csv_path.set(os.path.basename(p)); self.status_text.configure(text='●  CSV selected')

    def copy_tag(self,tag):
        self.root.clipboard_clear(); self.root.clipboard_append(tag); self.status_text.configure(text=f'●  Copied {tag}')

    def copy_all(self):
        tags='#INVOICE#\n#TRXID#\n#RANDOMS#\n#DATE#\n#NAME#\n#EMAIL#\n#TIME#\n#TFN#'
        self.root.clipboard_clear(); self.root.clipboard_append(tags); self.status_text.configure(text='●  All tags copied')

    def _refresh_stats(self):
        st=self.task_stats[self.task]
        for k,w in self.status_values.items(): w.configure(text=str(st.get(k,0)))
        for k,w in self.bounce_values.items(): w.configure(text=str(st.get(k,0)))
        self.progress.delete('all')
        total=max(1,st.get('total',0)); pct=min(1.0,st.get('sent',0)/total)
        self.progress.create_rectangle(0,0,int(self.progress.winfo_width()*pct),12,fill=GREEN,outline='')

    def _parse_rows(self, text):
        rows=[]
        for raw in text.splitlines():
            line=raw.strip()
            if not line or line.startswith('#'): continue
            # Supports one recipient per line: email, or email followed by tab/comma/semicolon and optional name.
            parts = next(csv.reader([line], delimiter='	')) if '\t' in line else next(csv.reader([line]))
            email=next((x.strip() for x in parts if re.fullmatch(r'[^\s@,;]+@[^\s@,;]+\.[^\s@,;]+',x.strip())), '')
            if email: rows.append((line,email,parts[1].strip() if len(parts)>1 else ''))
        return rows

    def _make_tag_values(self, email, name, tfn_value='', fallback_name=''):
        """Create one replacement set per recipient, shared by Subject, HTML and Body."""
        now = datetime.now()
        recipient_name = name or fallback_name or 'Customer'
        return {
            '#INVOICE#': 'OHS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=11)),
            '#TRXID#': ''.join(random.choices(string.digits, k=6)),
            '#RANDOMS#': ''.join(random.choices(string.ascii_uppercase + string.digits, k=25)),
            '#DATE#': now.strftime('%Y-%m-%d'),
            '#NAME#': recipient_name,
            '#EMAIL#': email or '',
            '#TIME#': now.strftime('%H:%M:%S'),
            '#TFN#': tfn_value or '',
        }

    def _replace_tags(self, text, values):
        """Replace supported tags case-insensitively in any text or HTML content."""
        if not text:
            return text
        pattern = re.compile('|'.join(re.escape(tag) for tag in sorted(values, key=len, reverse=True)), re.IGNORECASE)
        lookup = {tag.upper(): str(value) for tag, value in values.items()}
        return pattern.sub(lambda match: lookup.get(match.group(0).upper(), match.group(0)), text)

    def _set_task_state(self, task_id, state):
        """Keep each task card's status aligned with its actual send progress."""
        if 1 <= task_id <= len(getattr(self, 'task_state_labels', [])):
            label = self.task_state_labels[task_id - 1]
            color = GREEN if state in ('Ready', 'Done') else (RED if state == 'End' else CYAN)
            label.configure(text=f'● {state}', fg=color)

    def start(self):
        if getattr(self, 'cloud_token', None):
            try:
                from cloud_client import call
                acct=call('GET','/api/me',self.cloud_token)['user']
                if acct['limit_left'] < 1:
                    messagebox.showerror('Limit / Validity','Sending limit exhausted. Contact administrator.'); return
            except Exception as e:
                messagebox.showerror('Cloud Account Check',str(e)); return
        if self.worker and self.worker.is_alive():
            messagebox.showinfo('SS Mailer','A worker is still active (often waiting for Google OAuth permission). Check the browser for the Google permission page. If no page is open, click Stop, wait a few seconds, then restart the app and try again. OAuth login now times out after 3 minutes.'); return
        cred=self.json_path.get()
        if not os.path.isfile(cred) or not cred.lower().endswith('.json'):
            messagebox.showerror('Google OAuth','Choose your Google OAuth Desktop App credentials JSON file first.'); return
        cfg=self.task_configs.get(self.task,{})
        data=self.data.get('1.0','end-1c')
        rows=self._parse_rows(data)
        if self.header_mode.get() == 'Gmail':
            rows=[row for row in rows if row[1].lower().endswith('@gmail.com')]
        if not rows:

            messagebox.showwarning('Recipient Data','Add recipient rows to the Data box. Use one email address per line, optionally followed by a tab and name.'); return
        html=self.html.get('1.0','end-1c').strip(); body=self.body.get('1.0','end-1c').strip(); subject=self.subject.get().strip()
        if not subject or (not html and not body):
            messagebox.showwarning('Message Required','Enter a subject and HTML or Body content first.'); return
        st=self.task_stats[self.task]; st.update(total=len(rows),sent=0,failed=0,remaining=len(rows),bounce=st.get('bounce',0),checked=st.get('checked',0)); self._refresh_stats()
        task_id=self.task
        self._tfn_value = self.tfn.get()
        self._active_task_name = self.task_names.get(task_id, '')
        self._active_name = self.name.get().strip()
        self._active_format = self.send_format.get()
        self._active_change_name = bool(self.change_name.get())
        try: self._active_name_count = max(1, int(self.name_count.get()))
        except (ValueError, tk.TclError): self._active_name_count = 1
        self.stop_event.clear(); self._set_task_state(task_id, 'Running')
        self.status_text.configure(text=f'●  Task {task_id}: waiting for Google permission')
        self.worker=threading.Thread(target=self._send_worker,args=(task_id,cred,rows,subject,html,body),daemon=True); self.worker.start(); self.root.after(200,self._poll_events)

    def _send_worker(self, task_id, cred, rows, subject, html, body):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            scopes=['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly']
            creds=None
            if os.path.exists(self.token_path):
                try: creds=Credentials.from_authorized_user_file(self.token_path,scopes)
                except Exception: creds=None
            if not creds or not creds.valid:
                refreshed=False
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request()); refreshed=True
                    except Exception:
                        # A stale token can belong to an old/disabled OAuth client. Discard it and retry consent.
                        try: os.remove(self.token_path)
                        except OSError: pass
                        creds=None
                if not refreshed:
                    creds=InstalledAppFlow.from_client_secrets_file(cred,scopes).run_local_server(port=0, open_browser=True, timeout_seconds=30)
                with open(self.token_path,'w',encoding='utf-8') as f: f.write(creds.to_json())
            service=build('gmail','v1',credentials=creds,cache_discovery=False)
            self.events.put(('status',task_id,'Google permission granted; sending started'))
            sender_name_pool = ['Olivia Bennett','Liam Carter','Emma Mitchell','Noah Parker','Amelia Brooks','Elijah Morgan','Sophia Reed','James Cooper','Isabella Hayes','Benjamin Foster','Mia Collins','Lucas Edwards','Charlotte Rivera','Henry Stewart','Evelyn Morris','Alexander Rogers','Harper Cook','Daniel Bailey','Abigail Bell','Matthew Murphy','Emily Kelly','Jackson Price','Elizabeth Ward','Sebastian Gray','Avery James','Jack Watson','Sofia Sanders','Aiden Ross','Ella Peterson','Owen Perry','Scarlett Powell','Samuel Long','Grace Patterson','David Hughes','Chloe Flores','Joseph Washington','Victoria Butler','John Simmons','Riley Bryant','Wyatt Alexander','Aria Russell','Luke Griffin','Lily Diaz','Gabriel Hayes','Zoey Myers','Anthony Ford','Nora Hamilton','Dylan Graham','Hannah Sullivan','Isaac Wallace','Addison Woods','Julian Cole','Ellie West','Levi Jordan','Stella Owens']
            current_display_name = self._active_name or 'SS Mailer'
            sent_since_name_change = 0
            for original,email,name in rows:
                if self.stop_event.is_set(): break
                reservation_id=None
                # Build the message before reserving quota so a local PDF/image conversion error cannot consume a send.
                # Use exactly the same generated value for a tag in Subject, HTML and Body.
                values = self._make_tag_values(email, name or current_display_name or self._active_task_name, self._tfn_value, current_display_name)
                sub = self._replace_tags(subject, values)
                h = self._replace_tags(html, values)
                b = self._replace_tags(body, values)
                try:
                    sender_email=service.users().getProfile(userId='me').execute().get('emailAddress','')
                except Exception:
                    sender_email=''
                display_name=(current_display_name or 'SS Mailer').strip()
                msg=MIMEMultipart('mixed')
                msg['to']=email; msg['subject']=sub
                if sender_email:
                    msg['From']=formataddr((display_name, sender_email))
                mode=getattr(self,'_active_format','PDF')
                # Each mode adds only its selected payload. No image/CID part is added in PDF mode.
                if mode == 'PDF':
                    # PDF mode: HTML is rendered into the PDF attachment only.
                    # Never include the HTML template as an inline HTML email body.
                    pdf_bytes=self._html_to_pdf_bytes(h or b or '')
                    part=MIMEBase('application','pdf'); part.set_payload(pdf_bytes); encoders.encode_base64(part)
                    part.add_header('Content-Disposition','attachment',filename=self._attachment_name()+'.pdf'); msg.attach(part)
                    # Only the user's Body field is sent as the email body; tags have already been replaced.
                    msg.attach(MIMEText(b or '', 'plain', 'utf-8'))
                elif mode == 'DOC Attach':
                    doc=(h or '<html><body><pre>'+html_escape(b or '')+'</pre></body></html>').encode('utf-8')
                    part=MIMEBase('application','msword'); part.set_payload(doc); encoders.encode_base64(part)
                    part.add_header('Content-Disposition','attachment',filename=self._attachment_name()+'.doc'); msg.attach(part)
                    alt=MIMEMultipart('alternative')
                    if b: alt.attach(MIMEText(b,'plain','utf-8'))
                    if h: alt.attach(MIMEText(h,'html','utf-8'))
                    if not b and not h: alt.attach(MIMEText('', 'plain','utf-8'))
                    msg.attach(alt)
                elif mode in ('JPG Attach','PNG Attach'):
                    image_bytes, image_type=self._html_to_image_bytes(h or b or '', 'PNG' if mode == 'PNG Attach' else 'JPEG')
                    subtype='jpeg' if image_type=='JPEG' else 'png'
                    part=MIMEBase('image',subtype); part.set_payload(image_bytes); encoders.encode_base64(part)
                    ext='jpg' if image_type=='JPEG' else 'png'; part.add_header('Content-Disposition','attachment',filename=self._attachment_name()+'.'+ext); msg.attach(part)
                    # Attachment modes must not embed the HTML page inline. Only send the user's Body text.
                    msg.attach(MIMEText(b or '', 'plain', 'utf-8'))
                elif mode == 'Inline Image':
                    image_bytes, image_type=self._html_to_image_bytes(h or b or '', 'PNG')
                    related=MIMEMultipart('related')
                    alt=MIMEMultipart('alternative')
                    if b: alt.attach(MIMEText(b,'plain','utf-8'))
                    alt.attach(MIMEText('<html><body><img src="cid:ssmailer_inline" alt="Message image"></body></html>','html','utf-8'))
                    related.attach(alt)
                    part=MIMEBase('image','png'); part.set_payload(image_bytes); encoders.encode_base64(part)
                    part.add_header('Content-ID','<ssmailer_inline>'); part.add_header('Content-Disposition','inline',filename=values['#RANDOMS#']+'.png'); related.attach(part); msg.attach(related)
                else:
                    alt=MIMEMultipart('alternative')
                    alt.attach(MIMEText(b or '', 'plain','utf-8'))
                    if h: alt.attach(MIMEText(h,'html','utf-8'))
                    msg.attach(alt)
                raw=base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
                if getattr(self, 'cloud_token', None):
                    try:
                        from cloud_client import call
                        reservation=call('POST','/api/send/reserve',self.cloud_token,json={})
                        reservation_id=reservation['reservation_id']
                        if 'limit_left' in reservation: self.events.put(('limit',task_id,reservation['limit_left']))
                        elif hasattr(self,'_auth_refresh_limit'): self.root.after(0,self._auth_refresh_limit)
                    except Exception as e:
                        self.events.put(('status',task_id,'Sending stopped: '+str(e)[:100])); break
                try:
                    service.users().messages().send(userId='me',body={'raw':raw}).execute()
                    if reservation_id:
                        from cloud_client import call
                        finished=call('POST','/api/send/finish',self.cloud_token,json={'reservation_id':reservation_id,'success':True})
                        if 'limit_left' in finished: self.events.put(('limit',task_id,finished['limit_left']))
                    self.events.put(('sent',task_id,original,email))
                    if getattr(self, '_active_change_name', False):
                        sent_since_name_change += 1
                        if sent_since_name_change >= max(1, getattr(self, '_active_name_count', 1)):
                            choices=[n for n in sender_name_pool if n != current_display_name]
                            current_display_name=random.choice(choices or sender_name_pool)
                            sent_since_name_change=0
                            self.events.put(('name_change',task_id,current_display_name))
                except Exception as e:
                    if reservation_id:
                        try:
                            from cloud_client import call
                            finished=call('POST','/api/send/finish',self.cloud_token,json={'reservation_id':reservation_id,'success':False})
                            if 'limit_left' in finished: self.events.put(('limit',task_id,finished['limit_left']))
                        except Exception: pass
                    self.events.put(('failed',task_id,original,email,str(e)))
                time.sleep(0.5)
            self.events.put(('finished', task_id, self.stop_event.is_set()))
            self.events.put(('status',task_id,'Stopped' if self.stop_event.is_set() else 'Sending finished'))
        except Exception as e:
            err=str(e)
            if 'oauth client was disabled' in err.lower() or 'client is disabled' in err.lower():
                err=('Google has disabled this OAuth Client. This cannot be fixed by changing the mailer code. '
                     'Enable/create a Google OAuth Client (Desktop app) in Google Cloud Console, enable Gmail API, '
                     'then download a fresh credentials JSON and upload it here. Original error: '+err)
            self.events.put(('error',task_id,err))

    def _html_to_plain_text(self, source):
        class PlainExtractor(HTMLParser):
            def __init__(self): super().__init__(); self.parts=[]
            def handle_data(self, data):
                value=data.strip()
                if value: self.parts.append(value)
        parser=PlainExtractor()
        try: parser.feed(source or '')
        except Exception: return source or ''
        return '\n'.join(parser.parts)

    def _html_to_pdf_bytes(self, source):
        """Render HTML into PDF pages, preserving common HTML/CSS layout when possible."""
        output=BytesIO()
        try:
            from xhtml2pdf import pisa
            result=pisa.CreatePDF(src=(source or '<html><body></body></html>'), dest=output, encoding='utf-8')
            if not result.err and output.getvalue().startswith(b'%PDF-'):
                return output.getvalue()
        except Exception:
            pass
        # Fallback: create readable text with paragraph breaks instead of literal HTML markup.
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        class TextExtractor(HTMLParser):
            def __init__(self): super().__init__(); self.parts=[]
            def handle_data(self,data):
                value=data.strip()
                if value: self.parts.append(value)
            def handle_starttag(self,tag,attrs):
                if tag.lower() in ('p','div','br','tr','li','h1','h2','h3','section','header','footer'): self.parts.append('\n')
        parser=TextExtractor(); parser.feed(source or '')
        text=' '.join(parser.parts).replace('\n','  ').strip() or ' '
        doc=SimpleDocTemplate(output,pagesize=A4,rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42)
        styles=getSampleStyleSheet(); story=[]
        for chunk in [text[i:i+900] for i in range(0,len(text),900)]:
            story.append(Paragraph(html_escape(chunk),styles['BodyText'])); story.append(Spacer(1,8))
        doc.build(story)
        return output.getvalue()

    def _attachment_name(self):
        """Short random filename independent from Body/HTML tag values."""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    def _html_to_image_bytes(self, source, image_format='PNG'):
        """Render the HTML page to an image via a PDF page, preserving layout and text."""
        pdf_bytes = self._html_to_pdf_bytes(source or '<html><body></body></html>')
        try:
            import fitz  # PyMuPDF
            from PIL import Image
            doc = fitz.open(stream=pdf_bytes, filetype='pdf')
            if len(doc) == 0:
                raise RuntimeError('HTML renderer produced an empty page')
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8), alpha=False)
            image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
            out = BytesIO()
            image.save(out, format=image_format, quality=92)
            doc.close()
            return out.getvalue(), image_format
        except Exception as exc:
            raise RuntimeError('Could not render HTML as a page image. Install requirements again. ' + str(exc))

    def _poll_events(self):
        try:
            while True:
                ev=self.events.get_nowait(); kind,tid,*args=ev
                if kind=='sent':
                    original,email=args; st=self.task_stats[tid]; st['sent']+=1; st['remaining']=max(0,st['remaining']-1)
                    if getattr(self, 'cloud_token', None) and hasattr(self, '_auth_refresh_limit'):
                        try: self.root.after(0,self._auth_refresh_limit)
                        except Exception: pass
                    # Remove only the successfully accepted row from that task's data editor and stored config.
                    text=self.data.get('1.0','end-1c') if self.task==tid else self.task_configs.get(tid,{}).get('data','')
                    lines=text.splitlines(); removed=False; kept=[]
                    for line in lines:
                        if not removed and line.strip()==original.strip(): removed=True
                        else: kept.append(line)
                    updated='\n'.join(kept)
                    self.task_configs.setdefault(tid,{})['data']=updated
                    if self.task==tid:
                        self.data.delete('1.0','end'); self.data.insert('1.0',updated); self._refresh_stats()
                elif kind=='failed':
                    original,email,err=args; st=self.task_stats[tid]; st['failed']+=1; st['remaining']=max(0,st['remaining']-1)
                    self.status_text.configure(text=f'●  Failed {email}: {err[:80]}')
                    if getattr(self,'cloud_token',None) and hasattr(self,'_auth_refresh_limit'):
                        try: self.root.after(0,self._auth_refresh_limit)
                        except Exception: pass
                    if self.task==tid: self._refresh_stats()
                elif kind=='finished':
                    was_stopped=args[0]
                    state = 'Done' if st_all_done(self.task_stats[tid]) else 'End'
                    self._set_task_state(tid, state)
                elif kind=='name_change':
                    new_name=args[0]
                    self.task_names[tid]=new_name
                    self.task_configs.setdefault(tid,{})['name']=new_name
                    if self.task==tid:
                        self.name.set(new_name)
                elif kind=='limit':
                    left=args[0]
                    if hasattr(self,'auth_limit_label') and hasattr(self,'auth_username'):
                        self.auth_limit_label.set(f'{self.auth_username}  |  Limit Left: {left}')
                elif kind=='status':
                    msg=args[0]
                    if any(word in msg.lower() for word in ('sending started','sending')) and not any(word in msg.lower() for word in ('finished','stopped')):
                        self._set_task_state(tid, 'Running')
                    self.status_text.configure(text=f'●  Task {tid}: {msg}')
                elif kind=='error':
                    messagebox.showerror('Google OAuth / Gmail API',args[0]); self.status_text.configure(text='●  Gmail connection failed')
        except queue.Empty: pass
        if (self.worker and self.worker.is_alive()) or not self.events.empty(): self.root.after(200,self._poll_events)

    def check_bounce(self):
        if self.worker and self.worker.is_alive():
            messagebox.showinfo('Bounce Check','Wait until the current sending task finishes, then check bounces.'); return
        cred=self.json_path.get()
        if not os.path.isfile(cred):
            messagebox.showerror('Bounce Check','Select the Google OAuth credentials JSON file first.'); return
        self.status_text.configure(text=f'●  Task {self.task}: checking Gmail bounce notices')
        threading.Thread(target=self._bounce_worker,args=(self.task,cred),daemon=True).start()
        self.root.after(200,self._poll_events)

    def _bounce_worker(self, tid, cred):
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            scopes=['https://www.googleapis.com/auth/gmail.send','https://www.googleapis.com/auth/gmail.readonly']
            creds=Credentials.from_authorized_user_file(self.token_path,scopes) if os.path.exists(self.token_path) else None
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
                else: creds=InstalledAppFlow.from_client_secrets_file(cred,scopes).run_local_server(port=0,open_browser=True,timeout_seconds=30)
                with open(self.token_path,'w',encoding='utf-8') as f:f.write(creds.to_json())
            service=build('gmail','v1',credentials=creds,cache_discovery=False)
            res=service.users().messages().list(userId='me',q='from:(mailer-daemon OR postmaster) newer_than:7d',maxResults=100).execute()
            ids=res.get('messages',[]); bounced=set()
            for item in ids:
                m=service.users().messages().get(userId='me',id=item['id'],format='full').execute()
                payload=m.get('payload',{}); headers={h['name'].lower():h['value'] for h in payload.get('headers',[])}
                text=headers.get('subject','')
                def walk(part):
                    nonlocal text
                    data=part.get('body',{}).get('data')
                    if data:
                        try:text+=' '+base64.urlsafe_b64decode(data+'===').decode('utf-8','ignore')
                        except Exception:pass
                    for sub in part.get('parts',[]):walk(sub)
                walk(payload)
                for em in re.findall(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',text,re.I): bounced.add(em.lower())
            st=self.task_stats[tid]; st['bounce']=len(bounced); st['checked']=len(ids)
            self.events.put(('status',tid,f'Bounce scan finished: {len(bounced)} addresses found in recent bounce notices'))
            self.root.after(0,lambda:self._refresh_stats() if self.task==tid else None)
        except Exception as e:self.events.put(('error',tid,'Bounce check failed: '+str(e)))

    def stop(self):
        self.stop_event.set(); self.status_text.configure(text='●  Stop requested')

    def _status_clock(self):
        self.clock.configure(text=datetime.now().strftime('%Y-%m-%d   %H:%M:%S'))
        self.root.after(1000,self._status_clock)

if __name__ == '__main__':
    root=tk.Tk(); App(root); root.mainloop()
