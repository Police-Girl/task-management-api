# Task Management API

A fully-featured REST API built with **Django** and **Django REST Framework**.
Deployed live at: **https://LucianKatana.pythonanywhere.com/api/**

---

## What This Project Does

This API allows users to manage personal tasks. Each user can:
- Create, read, update and delete their own tasks
- Mark tasks as complete or incomplete
- Filter and sort tasks by status, priority and due date
- Register and manage their own account

No user can see or touch another user's tasks — ownership is strictly enforced.

---

## Live URLs

| Page | URL |
|------|-----|
| API Root | https://LucianKatana.pythonanywhere.com/api/ |
| Admin Dashboard | https://LucianKatana.pythonanywhere.com/admin/ |
| Login | https://LucianKatana.pythonanywhere.com/api/auth/login/ |
| Tasks | https://LucianKatana.pythonanywhere.com/api/tasks/ |
| Users | https://LucianKatana.pythonanywhere.com/api/users/ |

---

## Project Structure

```
task-management-api/
├── task_api/                  # Django project configuration
│   ├── settings.py            # All Django settings
│   ├── urls.py                # Root URL routing
│   └── wsgi.py                # WSGI entry point for deployment
│
├── task_manager/              # Main app — all business logic
│   ├── models.py              # Task database model
│   ├── serializers.py         # JSON validation and conversion
│   ├── views.py               # API endpoint handlers
│   ├── urls.py                # App URL routing
│   ├── permissions.py         # Task ownership enforcement
│   ├── filters.py             # Filtering and sorting logic
│   └── admin.py               # Django admin configuration
│
├── manage.py                  # Django CLI tool
├── requirements.txt           # Python dependencies
├── Procfile                   # Deployment config
├── runtime.txt                # Python version
└── .env.example               # Environment variable template
```

---

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.13 | Programming language |
| Django 4.2 | Web framework |
| Django REST Framework | API toolkit |
| JWT (SimpleJWT) | Token authentication |
| django-filter | Filtering and sorting |
| SQLite | Database (development + production) |
| Whitenoise | Static file serving |
| PythonAnywhere | Deployment platform |

---

## API Endpoints

### Authentication
| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/login/ | Login and get JWT tokens |
| POST | /api/auth/refresh/ | Refresh an expired access token |

### Users
| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/users/ | Register a new account |
| GET | /api/users/me/ | View your profile |
| PUT | /api/users/me/ | Update your profile |
| PATCH | /api/users/me/ | Partially update your profile |
| DELETE | /api/users/me/ | Delete your account |
| POST | /api/users/change-password/ | Change your password |

### Tasks
| Method | URL | Description |
|--------|-----|-------------|
| GET | /api/tasks/ | List all your tasks |
| POST | /api/tasks/ | Create a new task |
| GET | /api/tasks/<id>/ | Get a specific task |
| PUT | /api/tasks/<id>/ | Replace a task completely |
| PATCH | /api/tasks/<id>/ | Partially update a task |
| DELETE | /api/tasks/<id>/ | Delete a task |
| POST | /api/tasks/<id>/toggle-status/ | Mark complete or incomplete |
| GET | /api/tasks/summary/ | Get task counts by status |

### Task Filtering (add as query parameters)
```
?status=PENDING              Only pending tasks
?status=COMPLETED            Only completed tasks
?priority=HIGH               Only high priority tasks
?due_date_before=2026-12-31  Tasks due before this date
?due_date_after=2026-01-01   Tasks due after this date
?is_overdue=true             Only overdue tasks
?search=keyword              Search title and description
?ordering=due_date           Sort by due date (ascending)
?ordering=-due_date          Sort by due date (descending)
?ordering=priority           Sort by priority
```

---

## Task Attributes

| Field | Type | Description |
|-------|------|-------------|
| title | String | Short name for the task (required) |
| description | String | Detailed description (optional) |
| due_date | DateTime | Must be in the future (required) |
| priority | Choice | LOW, MEDIUM, or HIGH (default: MEDIUM) |
| status | Choice | PENDING or COMPLETED (default: PENDING) |
| completed_at | DateTime | Auto-set when marked complete |
| created_at | DateTime | Auto-set on creation |
| updated_at | DateTime | Auto-updated on every save |

---

## Business Rules

- Due dates must be in the future
- Completed tasks cannot be edited — revert to PENDING first
- Marking a task complete automatically sets the completed_at timestamp
- Reverting to pending automatically clears the completed_at timestamp
- Users can only see and manage their own tasks

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | Deleted successfully |
| 400 | Bad request / validation error |
| 401 | Not logged in / bad token |
| 403 | Logged in but not allowed |
| 404 | Not found |

---

## Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/Police-Girl/task-management-api.git
cd task-management-api
```

### 2. Create and activate virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
nano .env
```

Fill in your .env:
```
SECRET_KEY=your-generated-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=
```

Generate a secret key:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser
```bash
python manage.py createsuperuser
```

### 7. Start the server
```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/api/

---

## Testing the API (Terminal)

### Register and login
```bash
# Register
curl -X POST https://LucianKatana.pythonanywhere.com/api/users/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@gmail.com", "password": "Securepass1234"}'

# Login and save token automatically
RESPONSE=$(curl -s -X POST https://LucianKatana.pythonanywhere.com/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "password": "Securepass1234"}')
TOKEN=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")
```

### Task operations
```bash
# Create a task
curl -X POST https://LucianKatana.pythonanywhere.com/api/tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My task", "description": "Test", "due_date": "2026-12-31T23:59:00Z", "priority": "HIGH"}'

# List tasks
curl -X GET https://LucianKatana.pythonanywhere.com/api/tasks/ \
  -H "Authorization: Bearer $TOKEN"

# Mark complete
curl -X POST https://LucianKatana.pythonanywhere.com/api/tasks/1/toggle-status/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "COMPLETED"}'

# Filter by priority
curl -X GET "https://LucianKatana.pythonanywhere.com/api/tasks/?priority=HIGH" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Deployment (PythonAnywhere)

### 1. Clone repo on PythonAnywhere Bash console
```bash
git clone https://github.com/your-username/task-management-api.git
cd task-management-api
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install python-dotenv
```

### 3. Set up .env
```bash
cp .env.example .env
nano .env
```
```
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-username.pythonanywhere.com
DATABASE_URL=
```

### 4. Run migrations
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### 5. Configure Web Tab on PythonAnywhere
- **Source code:** /home/your-username/task-management-api
- **Virtualenv:** /home/your-username/task-management-api/venv
- **Python version:** 3.13

### 6. WSGI file content
```python
import os
import sys

path = '/home/your-username/task-management-api'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'task_api.settings'

from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Reload the web app and visit your live URL

---

## Author
Nicole Wangeci as my ALX Back end development capstone Project

