# Treking — Task Tracking Project

Short description

This is a student project: a task management/tracking system built with Django. Users can register, create tasks, add details (status, priority, due date), attach files and comment on tasks.

Features

- User registration and authentication
- Create / edit / delete tasks
- Task details: status, priority, due date
- Comments on tasks
- Attach files to tasks (uploads)
- Search and filter tasks by status/priority
- Basic role checks: only owners or staff can edit/delete tasks

Quick start (Windows PowerShell)

1. Create virtual environment & activate

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Apply migrations and create superuser

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Run the dev server

```powershell
python manage.py runserver
```

Notes

- Media files are saved to `media/` (see `task_treking/settings.py`). In development they are served by Django when `DEBUG=True`.
- For production use a proper DB (PostgreSQL) and a web server to serve media/static files.

Next steps

- Add tests, CI and Docker support.
- Improve permissions (fine-grained) and add activity logs.
