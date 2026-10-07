FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend ./
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=false
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY --from=frontend /app/backend/static/app ./backend/static/app
RUN python backend/manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "gunicorn --chdir backend --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --timeout 120 roadledger.wsgi:application"]
