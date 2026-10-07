from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from django.urls import include, path, re_path


def app_view(_request):
    index_path = Path(settings.BASE_DIR) / "static" / "app" / "index.html"
    if not index_path.exists():
        raise Http404("Frontend build not found. Run `npm run build` in frontend.")
    return FileResponse(index_path.open("rb"), content_type="text/html")


urlpatterns = [
    path("api/", include("planner.urls")),
    re_path(r"^(?!api/|static/).*$", app_view),
]

