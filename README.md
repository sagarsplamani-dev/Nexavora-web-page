# Nexavora course website

A Django recreation of the supplied Nexavora Technologies LLP course-site reference. The homepage contains the Data Science and Data Analytics learning paths, responsive section navigation, curriculum accordions, and enquiry forms. Enquiries are stored in the database and managed through Django Admin.

## Run locally

Requires Python 3.11 or newer.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/`. In VS Code, use **Django website (port 8000)** to start the recreated site. If another service is already using port `8000`, stop it before starting Django; only one server can listen on that address at a time.

The local development default uses SQLite and `DJANGO_DEBUG=True`. Before deploying, set a unique `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS`; see `.env.example`. The application does not send email yet, so admins should review submissions in Django Admin.

## WhatsApp Cloud API notifications

The existing callback and contact forms save enquiries first. After a successful save, Django sends an approved WhatsApp template to `WHATSAPP_ADMIN_PHONE`. A Meta/API failure does not remove the enquiry. Notification state, Meta message ID, error code, and attempt time are visible in Django Admin. A unique hidden submission key prevents a repeated POST of the same form from creating a second enquiry or sending a second notification. Enquiries created before this integration are marked `Not sent`; new enquiries start as `Pending`.

The root `.env` is ignored by `.gitignore`; do not commit it or paste credentials into source control, support requests, or chat. The access token previously shared in the setup request must be revoked and replaced before use. Copy the placeholders locally and fill them with credentials from your own Meta app:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env` (and as Render environment variables in production):

- `WHATSAPP_ACCESS_TOKEN`: a current token with the required WhatsApp messaging permission. Never log or expose it.
- `WHATSAPP_PHONE_NUMBER_ID`: the sending business phone-number ID.
- `WHATSAPP_BUSINESS_ACCOUNT_ID`: the owning WhatsApp Business Account ID.
- `WHATSAPP_ADMIN_PHONE`: opted-in recipient in international E.164 digits, without `+`.
- `WHATSAPP_GRAPH_API_VERSION`: Graph API version; `v27.0` is current in this example. Check Meta's [version changelog](https://developers.facebook.com/docs/graph-api/changelog/) before upgrading.
- `WHATSAPP_NOTIFICATION_TEMPLATE`: the name of an approved utility template with seven body parameters.
- `WHATSAPP_TEMPLATE_LANGUAGE`: the approved template language code, such as `en_US`.

Create and get approval for a utility template whose body variables are in this order:

```text
New website enquiry #{{1}}
Category: {{2}}
Name: {{3}}
Email: {{4}}
Phone: {{5}}
Message: {{6}}
Submitted: {{7}}
```

The default template-name value in `.env.example` is only a placeholder. The configured name and language must exactly match the template approved in WhatsApp Manager. The `hello_world` template is used only for the initial API test and does not include enquiry details. A free-form message can only be sent during the 24-hour customer-service window after a WhatsApp user messages the business. Website enquiries do not start that WhatsApp window, so these outbound alerts must use an approved template. Follow WhatsApp's recipient opt-in and template policies. Without a delivery-status webhook, `Accepted by Meta` means the API accepted the request; it does not confirm delivery. A network timeout is recorded as `Outcome unknown` and is not automatically retried, to avoid duplicate messages.

### Local verification (Windows PowerShell / VS Code terminal)

After setting `.env` and approving the custom template:

```powershell
python manage.py check
python manage.py migrate
python manage.py test apps.contact
python manage.py send_whatsapp_test
python manage.py runserver 127.0.0.1:8000
```

`send_whatsapp_test` sends Meta's `hello_world` template to the configured admin recipient; in development mode, that recipient must be added as a test recipient in the Meta app. Then submit a callback and a contact enquiry through the actual website. Confirm the enquiries appear in Django Admin with their notification state and that an `Accepted by Meta` row has a message ID. Tests mock the HTTP client and never send real messages. To test missing credentials, use the automated configuration tests rather than putting an invalid token in logs or source files.

## Deployment outline (Render)

1. Push the project to a private or public GitHub repository.
2. Create a Render **Web Service** from that repository and use Python as the runtime.
3. Set the build command to `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`.
4. Set the start command to `gunicorn config.wsgi:application`.
5. Add environment variables for `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` (the Render hostname), `CSRF_TRUSTED_ORIGINS` (`https://<your-hostname>`), and `DATABASE_URL` from a managed PostgreSQL database. Also set all seven `WHATSAPP_*` values above in Render's environment settings; never upload `.env` or credentials to GitHub.
6. Enable HTTPS for the service and verify `/`, `/admin/`, and form submissions after deployment.

SQLite is suitable for development but should not be used as persistent production storage on an ephemeral web-service filesystem. `DATABASE_URL` accepts a PostgreSQL connection URL; production connections use SSL. WhiteNoise serves collected static assets. Keep the database and web service in the same hosting region when possible, and back up the production database.

The existing Render build command already runs migrations; keep that step so the enquiry notification fields and submission key are added in production. Use a properly managed production access token (for example, a least-privilege system-user token), rotate or revoke it through Meta/Render as needed, and do not rely on temporary setup tokens. Temporary user tokens expire; monitor token validity and update the Render secret before expiry. Production readiness also requires a Meta app and business, a registered sending number, the `whatsapp_business_messaging` permission and production access as applicable to the app, an opted-in recipient, and approval of the enquiry utility template. Meta may require business verification and app review depending on the business and access level; confirm the current requirements in Meta Business Manager before launch.

## Checks

```powershell
python manage.py check
python manage.py test
```
