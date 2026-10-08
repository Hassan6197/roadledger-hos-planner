"""Vercel entrypoint for the Django app stored in backend/."""

import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roadledger.settings")

from django.core.wsgi import get_wsgi_application


application = get_wsgi_application()
