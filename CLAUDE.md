# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

gocra2 is a Django web application for managing Go (board game) club tournaments. It implements a MacMahon pairing system and an EGF-style rating system. The app is deployed on Heroku with a PostgreSQL database.

## Required Environment Variables

Before running, set these environment variables:
- `GOCRA_ENV` — set to `DEV` for local development (enables DEBUG mode, disables SSL redirect)
- `DJANGO_SECRET` — Django secret key
- `EMAIL_HOST`, `DEFAULT_FROM_EMAIL`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — SMTP settings

## Common Commands

```bash
# Run development server
GOCRA_ENV=DEV python manage.py runserver

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Django shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

## Architecture

The project has two Django apps:

**`gocra/`** — Legacy standalone Python app (CLI tool). Only `gocra/gocra.py` is used by the web app, specifically the `Rank` class imported in `wgocra/models.py`.

**`wgocra/`** — Main Django app. All web functionality lives here:
- `models.py` — Core data models: `Club`, `Player`, `Series`, `Participant`, `Result`, `Rating`
- `views.py` — All views (function-based and class-based); contains pairing algorithm logic
- `helpers.py` — `ExternalMacMahon` (XML import from Gerlach tournament software), `rank2rating`/`rating2rank` converters
- `ratingsystem.py` — EGF-based rating gain calculation (`RatingSystem.calculate_gain`)

### Data Model

```
Club
 └── Series (one active "open" series per club at a time)
      └── Participant (Player in a Series, with rank/rating at time of entry)
           └── Result (one per round per participant, tracks pairing/color/win)

Player
 └── account (optional link to Django User)
 └── Rating (historical ratings per Series, saved on series_finalize)
```

### Access Control

- `Club.admin` (M2M to User) determines club admins — checked via `is_club_admin()` in views
- Most views require `@login_required`; `SeriesDetailView` and `PublicSeriesListView` are accessible without login
- Anonymous users can only browse closed series (`seriesIsOpen=False`); authenticated users can browse any series by `sid` param

### Key Workflows

1. **Import**: Upload MacMahon XML (`upload_macmahon`) → `ExternalMacMahon.xml_import` creates Series + Participants + Results
2. **Pairing**: `make_pairing` runs `pair_long`/`pair` (recursive algorithm minimizing score difference, penalizing repeat opponents)
3. **Rating calculation**: `SeriesDetailView.calculate_rating` computes gains per result using `RatingSystem.calculate_gain`, updates `Participant.resultrating/gain/score`
4. **Finalize**: `series_finalize` saves result ratings to `Rating` model and closes the series

### Rank/Rating Conversion

Ranks use EGF notation (e.g., `20k`, `1d`). Rating scale: `rank2rating('1d') = 2100`, `rank2rating('20k') = 100`. Each rank step = 100 rating points.

## Deployment

Deployed on Heroku. `Procfile` runs migrations on release and serves with gunicorn. Uses `django-heroku` for automatic configuration (database URL from `DATABASE_URL` env var overrides settings).
