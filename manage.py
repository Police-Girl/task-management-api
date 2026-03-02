#!/usr/bin/env python
"""
manage.py — Django's Command-Line Utility

This is the entry point for all Django management commands.

Common commands:
  python manage.py runserver          Start the development server
  python manage.py makemigrations     Create new migration files from model changes
  python manage.py migrate            Apply migrations to the database
  python manage.py createsuperuser    Create an admin user
  python manage.py shell              Open an interactive Python shell with Django loaded
  python manage.py collectstatic      Collect static files for production
  python manage.py test               Run tests
"""

import os
import sys


def main():
    """Run administrative tasks."""
    # Tell Django which settings module to use
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'task_api.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    # Parse and execute the command from the command line
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
