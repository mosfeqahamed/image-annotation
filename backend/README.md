# AnnotateX Backend

Django REST Framework backend for **AnnotateX** — a Kanban task manager and a
canvas-based image annotation tool. This is the single source of truth for the
backend; there is no separate frontend in this repository.

## Tech Stack

| Concern         | Choice                                                        |
| --------------- | ------------------------------------------------------------- |
| Language        | Python 3.12+                                                  |
| Framework       | Django 6 + Django REST Framework                              |
| Auth            | JWT via `djangorestframework-simplejwt` (with blacklisting)   |
| Database        | Managed Postgres — Neon or Supabase (required, no SQLite)      |
| Image storage   | Cloudinary (`django-cloudinary-storage`)                      |
| Static files    | WhiteNoise                                                    |
| WSGI server     | Gunicorn                                                      |
| Hosting         | Render (`render.yaml` blueprint)                              |
| Package manager | [uv](https://docs.astral.sh/uv/) (`pyproject.toml` / `uv.lock`) |

## Project Structure

```
image-annotation/
├── build.sh              # Render build script (runs from repo root)
├── render.yaml           # Render Blueprint (Infrastructure as Code)
├── pyproject.toml        # Dependencies (managed by uv)
├── uv.lock               # Pinned dependency versions
└── backend/
    ├── .env.example      # Environment variable template
    ├── manage.py
    ├── config/           # Project settings, URLs, WSGI
    ├── accounts/         # JWT auth: register / login / logout / refresh / me
    ├── tasks/            # Kanban tasks: CRUD, filtering, drag-and-drop reorder
    └── annotations/      # Image series, uploads (Cloudinary), polygon annotations
```

## Local Development

All commands run from the **repository root** (one level above `backend/`).

1. Install [uv](https://docs.astral.sh/uv/).
2. Install locked dependencies:
   ```bash
   uv sync
   ```
3. Create your environment file and fill in the values:
   ```bash
   cp backend/.env.example backend/.env
   ```
   `DATABASE_URL` is **required** — set it to your Postgres connection string
   (see below). If you don't configure Cloudinary, everything works except
   image uploads.
4. Apply migrations:
   ```bash
   uv run python backend/manage.py migrate
   ```
5. (Optional) Create an admin user:
   ```bash
   uv run python backend/manage.py createsuperuser
   ```
6. Run the dev server:
   ```bash
   uv run python backend/manage.py runserver
   ```
   The API is available at `http://localhost:8000/api/`.

> To change dependencies, edit `pyproject.toml` (or `uv add <pkg>`) and commit
> the updated `uv.lock`. There is no `requirements.txt`.

## Configuration

Configuration is entirely environment-driven (see `backend/.env.example`). Key
variables:

| Variable                                    | Purpose                                            |
| ------------------------------------------- | -------------------------------------------------- |
| `SECRET_KEY`                                | Django secret key                                  |
| `DEBUG`                                      | `True` locally, `False` in production              |
| `ALLOWED_HOSTS`                             | Comma-separated hostnames                          |
| `DATABASE_URL`                              | Postgres connection string (required)              |
| `CLOUDINARY_CLOUD_NAME` / `_API_KEY` / `_API_SECRET` | Cloudinary image storage credentials      |
| `CORS_ALLOWED_ORIGINS`                      | Comma-separated frontend origins                   |
| `JWT_ACCESS_MINUTES` / `JWT_REFRESH_DAYS`   | Token lifetimes (optional)                          |

### Database (Neon or Supabase Postgres)

Use any managed Postgres. Always use the provider's **pooled** connection
string — the direct host is often IPv6-only and unreachable from IPv4 networks
(including Render's free tier). SSL is required and enabled automatically.

- **Neon** ([neon.tech](https://neon.tech)): Dashboard → **Connection Details** →
  copy the pooled string (`...-pooler.<region>.aws.neon.tech`). Set as `DATABASE_URL`.
- **Supabase** ([supabase.com](https://supabase.com)): **Connect → Session Pooler**
  (`aws-0-<region>.pooler.supabase.com:5432`). Set as `DATABASE_URL`.

### Cloudinary (image storage)

1. Create an account at [cloudinary.com](https://cloudinary.com).
2. Copy **Cloud name**, **API Key**, and **API Secret** from the dashboard.
3. Set them as the three `CLOUDINARY_*` variables. Uploaded images are stored in
   Cloudinary and the API returns their absolute URLs.

## Authentication (JWT)

Send the access token as `Authorization: Bearer <access>` on protected requests.

| Method | Endpoint              | Auth | Body / Notes                                        |
| ------ | --------------------- | ---- | --------------------------------------------------- |
| POST   | `/api/auth/register/` | No   | `username, email, password, password_confirm` → returns `access`, `refresh`, `user` |
| POST   | `/api/auth/login/`    | No   | `email, password` → returns `access`, `refresh`, `user` |
| POST   | `/api/auth/refresh/`  | No   | `refresh` → returns a new `access`                  |
| POST   | `/api/auth/logout/`   | Yes  | `refresh` → blacklists the refresh token            |
| GET    | `/api/auth/me/`       | Yes  | Current user                                        |

## API Overview

- **Tasks** — `/api/tasks/` (CRUD; `?date=YYYY-MM-DD` filter; `POST /api/tasks/bulk-reorder/` and `PATCH /api/tasks/{id}/reorder/` for drag-and-drop).
- **Annotations**
  - `/api/annotations/series/` — image series (CRUD); `POST /api/annotations/series/{id}/upload/` (multipart `images`).
  - `/api/annotations/images/` — individual images.
  - `/api/annotations/annotations/` — polygon annotations (`?image={id}` filter; `POST /api/annotations/annotations/bulk-save/` to atomically replace an image's annotations).

All resources are scoped to the authenticated user.

## Deploying to Render

This repo ships a `render.yaml` Blueprint.

1. Push the repository to GitHub.
2. In Render: **New + → Blueprint**, and select this repo.
3. Render reads `render.yaml` and creates the web service. Fill in the values
   marked "sync: false" in the dashboard:
   - `DATABASE_URL` — Postgres pooled connection string (Neon or Supabase)
   - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
   - `CORS_ALLOWED_ORIGINS` — your frontend origin(s)

   `SECRET_KEY` is generated automatically; `DEBUG=False` and
   `ALLOWED_HOSTS=.onrender.com` are preset.
4. Deploy. The build runs `build.sh` (uv sync → collectstatic → migrate) and the
   service starts with:
   ```
   uv run gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:$PORT
   ```

## Notes & Challenges

- **Data modeling.** Annotation images are grouped under an `ImageSeries`
  collection (mirroring medical-imaging viewers) so users can switch between
  related images. Polygon annotations are stored in a `JSONField` as an array of
  `{x, y}` points — fast to serve and easy for a canvas frontend to consume,
  without a relational coordinate table.
- **Storage migration.** Moving from local media to Cloudinary means image URLs
  become absolute; the serializer returns Cloudinary URLs as-is (falling back to
  building an absolute URL from the request only for non-absolute paths).
