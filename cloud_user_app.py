import tkinter as tk, hashlib, socket, uuid, os
from tkinter import messagebox
from cloud_client import call, server_url
from ss_mailer import App

BG = '#030d22'
PANEL = '#061a38'
CYAN = '#00c8ff'
PURPLE = '#a100ff'
WHITE = '#eef6ff'
MUTED = '#a7c8ef'


def ent(parent, show=None):
    return tk.Entry(parent, bg='#03152f', fg=WHITE, insertbackground='white',
                    relief='flat', highlightbackground=CYAN, highlightthickness=1,
                    font=('Segoe UI', 11), show=show)


def btn(parent, text, command):
    return tk.Button(parent, text=text, command=command, bg='#0869f7', fg='white',
                     activebackground=PURPLE, relief='flat',
                     font=('Segoe UI', 10, 'bold'), padx=12, pady=8, cursor='hand2')


class UserLogin:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('SS Mailer • Email Sending Api')
        self.root.geometry('460x560')
        self.root.configure(bg=BG)
        self.root.resizable(False, False)
        try:
            self.root.iconbitmap(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ss_mailer.ico'))
        except Exception:
            pass
        self.show_loading()
        self.root.mainloop()

    def show_loading(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg=BG)
        tk.Label(self.root, text='✉ SS Mailer', bg=BG, fg=CYAN,
                 font=('Segoe UI', 25, 'bold')).pack(pady=(165, 12))
        tk.Label(self.root, text='Email Sending Api', bg=BG, fg=WHITE,
                 font=('Segoe UI', 15, 'bold')).pack(pady=4)
        tk.Label(self.root, text='Loading, please wait...', bg=BG, fg=MUTED,
                 font=('Segoe UI', 10)).pack(pady=(18, 12))
        progress = ttk_progress(self.root)
        progress.pack(padx=105, fill='x')
        self.root.after(1500, self.login_page)

    def login_page(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text='✉ SS Mailer', bg=BG, fg=CYAN,
                 font=('Segoe UI', 23, 'bold')).pack(pady=(35, 5))
        tk.Label(self.root, text='Email Sending Api', bg=BG, fg=WHITE,
                 font=('Segoe UI', 12, 'bold')).pack(pady=(0, 18))
        card = tk.Frame(self.root, bg=PANEL, highlightbackground=PURPLE,
                        highlightthickness=2)
        card.pack(fill='both', expand=True, padx=28, pady=(0, 24))
        tk.Label(card, text='Username', bg=PANEL, fg=MUTED).pack(
            anchor='w', padx=22, pady=(22, 4))
        self.u = ent(card)
        self.u.pack(fill='x', padx=22, ipady=8)
        tk.Label(card, text='Password', bg=PANEL, fg=MUTED).pack(
            anchor='w', padx=22, pady=(14, 4))
        self.p = ent(card, '●')
        self.p.pack(fill='x', padx=22, ipady=8)
        btn(card, 'LOGIN', self.login).pack(fill='x', padx=22, pady=20)
        tk.Label(card, text='Secure Access • Authorized User Only', bg=PANEL,
                 fg=CYAN, font=('Segoe UI', 9)).pack(pady=8)
        self.p.bind('<Return>', lambda event: self.login())
        self.u.focus_set()

    def login(self):
        try:
            if hasattr(self, 'status_label'):
                self.status_label.configure(text='Loading...')
                self.root.update_idletasks()
            server_url()  # Server URL is preconfigured for user installations.
            device_id = hashlib.sha256(
                (socket.gethostname() + str(uuid.getnode())).encode()
            ).hexdigest()[:32]
            if hasattr(self, 'status_label'):
                self.status_label.configure(text='Licences Checking...')
                self.root.update_idletasks()
            result = call('POST', '/api/user/login', json={
                'username': self.u.get().strip(),
                'password': self.p.get(),
                'device_id': device_id,
            })
            token = result['token']
            username = result['user']['username']
            if hasattr(self, 'status_label'):
                self.status_label.configure(text='Licences Successful')
                self.root.update_idletasks()
            self.root.destroy()
            launch(username, token)
        except Exception as exc:
            messagebox.showerror('Login Failed', str(exc), parent=self.root)


def ttk_progress(parent):
    # A lightweight animated-looking progress bar without an extra dependency.
    frame = tk.Frame(parent, bg='#12345a', height=5)
    frame.pack_propagate(False)
    bar = tk.Frame(frame, bg=CYAN, width=65)
    bar.place(x=0, y=0, relheight=1)
    def animate(x=0, direction=1):
        if not frame.winfo_exists():
            return
        width = max(frame.winfo_width(), 250)
        next_x = x + direction * 18
        if next_x >= width - 65:
            next_x, direction = width - 65, -1
        elif next_x <= 0:
            next_x, direction = 0, 1
        bar.place(x=next_x, y=0, relheight=1, width=65)
        frame.after(45, lambda: animate(next_x, direction))
    frame.after(45, animate)
    return frame


def launch(username, token):
    root = tk.Tk()
    app = App(root)
    app.cloud_token = token
    app.auth_username = username
    try:
        header = root.winfo_children()[0]
        badge = tk.Frame(header, bg='#061a38')
        badge.pack(side='right', padx=10)
        status = call('GET', '/api/me', token)
        user = status['user']
        sent = user.get('used', 0)
        limit = user.get('sending_limit', user['limit_left'] + sent)
        txt = tk.StringVar(value=f"👤  Account: {username}  |  Limit Left: {user['limit_left']}")
        tk.Label(badge, textvariable=txt, bg='#061a38', fg=CYAN,
                 font=('Segoe UI', 9, 'bold')).pack(side='left', padx=4)

        def logout():
            if not messagebox.askyesno('Confirm Logout', 'Are you sure you want to log out?', parent=root):
                return
            try:
                call('POST', '/api/logout', token)
            except Exception:
                pass
            root.destroy()
            UserLogin()

        tk.Button(badge, text='Logout', command=logout, bg='#b71c50', fg='white',
                  activebackground='#8f153d', relief='flat').pack(side='left', padx=4)
        app.auth_limit_label = txt

        def refresh():
            try:
                current = call('GET', '/api/me', token)['user']
                txt.set(f"👤  Account: {username}  |  Limit Left: {current['limit_left']}")
                root.after(15000, refresh)
            except Exception as exc:
                # Only force logout when server explicitly rejects an expired/disabled session.
                if '403' in str(exc) or 'expired' in str(exc).lower() or 'disabled' in str(exc).lower():
                    try: root.destroy()
                    except Exception: pass
                    messagebox.showwarning('Licence Expired', 'Your licence has expired or been disabled. Please log in again.')
                    UserLogin()
                    return
                txt.set(f'{username}  |  Server unavailable')
                root.after(15000, refresh)

        app._auth_refresh_limit = refresh
        root.after(15000, refresh)
    except Exception as exc:
        messagebox.showerror('Cloud Account', str(exc), parent=root)
    root.mainloop()


if __name__ == '__main__':
    UserLogin()
