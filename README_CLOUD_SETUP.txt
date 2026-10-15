SS MAILER CLOUD — MAIN ADMIN + SUBADMIN + USER APPLICATIONS

IMPORTANT
This ZIP includes the app source and Cloud API server. A public cloud host/domain is not included. For other PCs to log in, deploy cloud_server.py on a reachable host with HTTPS and persistent storage first.

SERVER DEPLOYMENT
1. Upload cloud_server.py and requirements.txt to a Python host that supports a persistent disk/database.
2. Set environment variables on the host:
   SSMAILER_ADMIN_PASSWORD = a strong unique main-admin password (8+ characters)
   SSMAILER_TOKEN_SECRET = a long random secret (32+ random characters)
   SSMAILER_DB = a persistent writable path for ssmailer_cloud.db (recommended)
3. Install requirements.txt. Start with a production WSGI server, for example:
   gunicorn --workers 1 --bind 127.0.0.1:8000 cloud_server:app
   Configure your host's HTTPS/reverse proxy in front of it. Do not expose Flask's development server directly to the public Internet.
4. Open https://YOUR-DOMAIN/health and verify status is ok.
5. On the Main Admin app, open Server Settings, enter the real HTTPS URL, Save URL, and Test Connection.

WINDOWS APPS
1. On a Windows PC with Python 3.10+, run build_exe.bat. It creates SS_Mailer_Admin.exe, SS_Mailer_Subadmin.exe and SS_Mailer_User.exe under dist.
2. Main Admin: set/test server URL, log in using SSMAILER_ADMIN_PASSWORD, create users and manage subadmins.
3. Subadmin and User apps have a Server URL field. On every PC, enter the same deployed HTTPS URL once and Save/Test. The setting is stored locally beside that app; Main Admin cannot automatically write settings onto another PC.
4. Give users only SS_Mailer_User.exe. Give subadmins only SS_Mailer_Subadmin.exe. Keep Main Admin private.

SUBADMIN SYSTEM
Main Admin can create/edit/delete subadmins with name, phone, username, password and a user-creation limit. The list shows total users and active users. Subadmins can sign in separately, see their profile and create/edit/delete only their own users. Deleting a subadmin moves their users into Main Admin's ownership.

USER LIMITS
User login, validity, device limit and sending limit are stored in the shared cloud database. Quota reservation/refund is performed by the server. Device identity is based on the Windows host name and network adapter ID, so hardware/network changes can count as a new device.

SECURITY
- Use HTTPS only for public access and a strong server admin password/token secret.
- The database must be on persistent storage; ephemeral hosting can erase users on restart. Back it up.
- This sample uses SQLite and is designed for a single server instance. For multiple server instances, use PostgreSQL and shared atomic quota operations.
- Never share token.json or OAuth credentials. Only send email to recipients who have consented.
- This package has been syntax-checked, but has not been deployed to your hosting provider or tested against a real public domain. Set your hosting details and run the connection test before distributing apps.
