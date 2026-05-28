web: cd backend && python manage.py collectstatic --noinput && python manage.py migrate --noinput && python init_db.py && gunicorn breathe_esg.wsgi --bind 0.0.0.0:$PORT --workers 2 --log-file -
