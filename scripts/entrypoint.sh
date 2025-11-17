#!/bin/sh

# Questo comando fa in modo che lo script si fermi
# immediatamente se uno dei comandi fallisce.
set -e

echo "==> (ENTRYPOINT) Esecuzione migrazioni database..."
/usr/local/bin/flask db upgrade

echo "==> (ENTRYPOINT) Avvio di Gunicorn..."
# 'exec' è importante, sostituisce questo script con gunicorn
# invece di lasciarli girare entrambi.
exec /usr/local/bin/gunicorn -w 4 -b 0.0.0.0:$PORT wsgi:app