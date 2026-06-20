# CareBase

Django clinic appointment app with email/password authentication and xAI Grok-powered symptom triage.

## Local Development

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r carebase\requirements.txt
.\.venv\Scripts\python carebase\manage.py migrate
.\.venv\Scripts\python carebase\manage.py runserver
```

The app runs at `http://127.0.0.1:8000/`.

## xAI Grok Configuration

Set `XAI_API_KEY` in your local shell or in Vercel Project Settings. The app also accepts `GROK_API_KEY` as a compatibility alias, but `XAI_API_KEY` is preferred.

If no xAI key is configured, CareBase uses a local keyword-based triage fallback instead of crashing.

If xAI returns `403 permission-denied`, the key is valid enough to reach xAI but the xAI team has no credits or licenses enabled. Add credits/licenses in the xAI Console, then restart the Django/Vercel deployment.

At the moment, Grok API responses are not functioning for the supplied key because the xAI team has no available credits/licenses. The local fallback still recommends a doctor specialty from symptom keywords.

Optional model override:

```text
XAI_MODEL=grok-4.3
```

## Vercel Deployment

Use the inner `carebase` folder as the Vercel project root. This folder contains `manage.py`, `requirements.txt`, `vercel.json`, and the `api/index.py` WSGI entrypoint.

Required Vercel environment variables:

```text
DJANGO_SECRET_KEY=<generated secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.vercel.app,your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://your-domain.com
DATABASE_URL=<managed postgres connection string>
XAI_API_KEY=<xai key>
XAI_MODEL=grok-4.3
```

Vercel stores environment variables outside source code. Do not commit real API keys or GitHub tokens.
