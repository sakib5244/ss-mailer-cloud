SS MAILER — SEPARATE USER + ADMIN APPLICATIONS

BUILD:
1. Extract this ZIP on Windows.
2. Run install_requirements.bat once.
3. Run build_exe.bat.
4. Two separate applications will be created in dist:
   - SS_Mailer_User.exe (user login and mailer)
   - SS_Mailer_Admin.exe (admin password and user management)
5. Keep both EXE files in the SAME folder after building. They share ssmailer_users.db.

RUN FROM PYTHON:
- run.bat opens the user application.
- To open admin app, run: py admin_app.py

ADMIN:
- First-run default admin password: admin123
- Change the admin password in Admin Panel immediately.
- Create users with username, password, validity days, device limit and sending limit.
- Search users, select a row to load details, edit or delete users.

LIMITATIONS:
- User records are stored in local SQLite. This is not a hosted central admin service; user records and device registrations do not sync across different computers. For remote centralized management, a hosted API/server is required.
- Device limit identifies this Windows installation using its machine name/network adapter identifier; major hardware/network changes may count as another device.
- Sending limits depend on the application's send-counter integration and Gmail API quotas/authorization.
