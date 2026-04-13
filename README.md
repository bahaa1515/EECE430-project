# AUB Varsity Volleyball Platform

EECE 430 course project built with Django for managing an AUB volleyball team. The project supports separate student and coach flows for login, notifications, attendance, roster management, statistics, dashboard views, and highlights/MVP content.

## Main Features

- Role-based login and signup
  - Students use `@mail.aub.edu`
  - Coaches use `@aub.edu.lb`
- Per-user notifications with read/unread state
- Coach-managed attendance with official statuses
- Match and practice management
- Player roster management with starter/substitute rules
- Statistics page with live computed data and manual team metrics
- Coach-managed match logs that feed player statistics
- Coach-managed highlights and MVP linked to specific sessions

## Tech Stack

- Python 3.11
- Django 4.2
- SQLite
- Django templates, static CSS, and simple JavaScript

## Project Structure

```text
volleyball_project/
|-- accounts/
|-- attendance/
|-- dashboard/
|-- highlights/
|-- notifications/
|-- players/
|-- statistics_app/
|-- static/
|-- templates/
|-- volleyball/
|-- manage.py
|-- requirements.txt
```

## Setup

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Apply migrations

```powershell
python manage.py migrate
```

### 4. Optional: load demo data

```powershell
python manage.py seed_data
```

### 5. Run the server

```powershell
python manage.py runserver
```

Open:

`http://127.0.0.1:8000/`

## Demo Accounts

If you run `seed_data`, use:

- Coach
  - Email: `bh00@aub.edu.lb`
  - Password: `coach123`
- Student
  - Email: `bh01@mail.aub.edu`
  - Password: `student123`

## Notes

- `db.sqlite3`, `media/`, and virtual environments are ignored from version control.
- This repo is configured to ignore local test files as requested for submission/push flow.
- For production use, update `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, storage, and database settings.
