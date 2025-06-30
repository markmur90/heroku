release: python3 manage.py migrate
release: python3 manage.py collectstatic --noinput

web: gunicorn config.wsgi:application --log-file -
