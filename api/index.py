import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# On Vercel (or local testing with CAREBASE_BOOTSTRAP=1), run
# migrations and seed doctors/slots on cold start.
if os.getenv("VERCEL") or os.getenv("CAREBASE_BOOTSTRAP"):
    try:
        from appointments.bootstrap import bootstrap_deployment

        bootstrap_deployment(os.getenv("VERCEL_URL", "carebase.vercel.app"))
    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning("Bootstrap skipped: %s", exc)

app = application
