import os
import sys
from pathlib import Path

# Vercel imports this module from the repository root, while the Django project
# lives in backend/. Ensure Django can resolve roadledger and planner there.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "roadledger.settings")
application = get_wsgi_application()
