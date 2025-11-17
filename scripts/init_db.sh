#!/bin/sh

echo "Inizializzazione del database..."

flask db init
flask db migrate -m "Initial migration"
flask db upgrade

echo "Database pronto."

Aggiungi permessi:

#!/bin/sh
chmod +x scripts/init_db.sh

Esegui con:

#!/bin/sh
docker-compose run --rm pokerapp ./scripts/init_db.sh
