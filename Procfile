web: cd backend && gunicorn breathe_esg.wsgi --log-file -
release: cd backend && python manage.py migrate --noinput && python manage.py collectstatic --noinput
