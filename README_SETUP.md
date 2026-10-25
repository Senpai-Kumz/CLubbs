# Clubb - Setup and Deployment Safety Notes

This document covers the first infrastructure-preparation change set. It does not mean a PostgreSQL database or external media storage has already been created.

## Local Development (Windows / VS Code)

1. Make a working copy of the project folder. Keep the original ZIP as a recovery point.
2. Create and activate a virtual environment if you do not already have one:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Copy the example environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Keep `DJANGO_DEBUG=True` for local development. The example key is for local development only. Do not reuse it on Render or in any production environment.
6. Run checks and migrations against local SQLite:

   ```powershell
   python manage.py check
   python manage.py showmigrations
   python manage.py runserver
   ```

   This change set leaves the current SQLite database and existing migrations intact for local testing.

## Database Behavior

- When `DJANGO_DEBUG=True` and `DATABASE_URL` is empty, the project uses the existing local `db.sqlite3` file.
- When `DATABASE_URL` contains a valid `postgres://` or `postgresql://` URL, the project uses PostgreSQL.
- When `DJANGO_DEBUG=False`, both `DJANGO_SECRET_KEY` and `DATABASE_URL` are required. The application deliberately fails to start rather than silently using an insecure secret or ephemeral SQLite in production.
- Do not point a production instance at the SQLite database included in the ZIP. Treat its contents as a development snapshot.

## Before Deploying to Render

**Do not deploy this change set until a managed PostgreSQL database has been created and its connection URL is configured.** The current Render service has no `DATABASE_URL` configured according to the read-only audit. With `DJANGO_DEBUG=False`, the application will intentionally refuse to start without it.

Configure these environment variables in the Render web service:

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY`: a newly generated, private secret. The previous hardcoded key was exposed in source and must not be reused.
- `DJANGO_ALLOWED_HOSTS=clubbs.onrender.com` (add any real custom hostname separately if needed)
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://clubbs.onrender.com`
- `DJANGO_SECURE_SSL_REDIRECT=True`
- `DATABASE_URL`: the PostgreSQL connection URL from the database provider, including required TLS options such as `sslmode=require` where specified.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET`: the private credentials for production media storage.
- `REDIS_URL`: recommended for reliable shared real-time messaging, particularly across multiple processes or instances.

Generate a fresh Django secret locally after installing Django:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Enter that output directly into Render's secret environment variable field. Do not paste it into chat, commit it, or put it in a public file.

## Media Storage

The production settings require Cloudinary credentials. Configure and test media uploads, playback, permissions, and deletion before enabling uploads for real users. Local development can continue using local file storage when Cloudinary is not configured.

## What This Change Set Does Not Do

- It does not create a database with Neon or another provider.
- It does not migrate or copy local SQLite data to PostgreSQL.
- It does not deploy anything to Render or push anything to GitHub.
- It does not implement new Gallery, Messages, Communities, or World features.