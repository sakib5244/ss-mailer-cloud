SS Mailer V0.1 — Gmail API build

SETUP
1. Install Python 3.10+.
2. Run install_requirements.bat.
3. In Google Cloud Console, create/select a project, enable Gmail API, configure OAuth consent screen, and create OAuth Client ID > Desktop app.
4. Download the OAuth client JSON file. Choose it in the app using Choose JSON File.
5. Put only recipients who have explicitly consented to receive your email in the Data box. Use one recipient per line; optional format: email<TAB>name.
6. Click Start. Google OAuth permission opens in your default browser (set Microsoft Edge as default if you want Edge). After permission, the app sends through Gmail API.

NOTES
- Gmail API sending requires the Google OAuth Desktop App credentials JSON, not a service-account JSON.
- First authorization creates token.json next to the app. Keep it private; it grants access to the connected Gmail account. Delete token.json to revoke local saved credentials, and revoke access in your Google Account security settings to fully revoke.
- Successful sends are removed from the active task's Data box. Failed rows remain for review.
- Bounce Check scans recent Gmail messages from mailer-daemon/postmaster and estimates bounce addresses from message content. It is not a guaranteed real-time delivery status or inbox placement detector.
- Each task has separate in-memory status counters and task-specific subject/HTML/body/data. Current task contents are not saved to disk automatically.
- Use only for consented recipients. Follow Gmail sending limits and anti-abuse policies. Avoid unsolicited bulk mail.

Update notes:
- Task-specific name and OAuth JSON selection are stored separately for each task.
- Change Name starts unchecked.
- HTML, Body, and Data editors start empty and remain empty when switching to a new task.
- HTML Preview opens in an in-app window; tkinterweb is used to render the HTML.
- Tag formats: #INVOICE# OHS- plus 11 uppercase letters/digits, #TRXID# 6 digits,
  #RANDOMS# 25 uppercase letters/digits, #DATE# YYYY-MM-DD, #NAME#, #EMAIL#,
  #TIME#, and #TFN#.


UPDATE NOTES - FORMAT / OAUTH / LIMIT
- Upload JSON must be a Google OAuth Desktop App client credentials JSON file.
- If Google says "OAuth Client Disabled", enable or create a valid OAuth client in Google Cloud Console, enable Gmail API, and download a fresh JSON file. Software cannot re-enable a disabled Google OAuth client.
- Format / Headers panel: PDF, JPG Attach, PNG Attach, DOC Attach, Inline Image; Mix includes all valid recipient domains, Gmail filters to @gmail.com.
- PDF is generated from readable HTML text/content; JPG/PNG/Inline Image renders the readable text from HTML into an image, not a pixel-perfect browser screenshot. DOC is an HTML-based .doc file.
- The Name box is used as the sender display name. Gmail may only accept a display name associated with the signed-in account/approved Send mail as configuration.
- Cloud Limit Left is reserved before each send, retained for accepted sends, and refunded on send failure. Keep recipients limited to people who requested or consented to receive your messages.


V6 FIX NOTES
- PDF mode sends the generated PDF attachment only; the HTML template is no longer embedded in the email body. The email body is only the Body field with supported tags replaced.
- Google OAuth browser login now has a 180-second timeout to prevent the worker from staying in a running state indefinitely while waiting for consent. If the Google permission page opens, finish the consent flow.
- If the app says a worker is still active, check the OAuth browser window; if no window is open, Stop, wait a few seconds, and restart the app before retrying.


CLOUD SERVER / SUBADMIN UPDATE
See README_CLOUD_SETUP.txt for the Main Admin, Subadmin and User app setup. Main Admin now has Server Settings (Save URL / Test Connection) and a Manage Subadmins window. The Subadmin app is cloud_subadmin_app.py. The URL is saved locally on each PC, so enter the same public HTTPS server URL once in each app/PC.
