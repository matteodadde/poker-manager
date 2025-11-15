# 1. Imposta la connessione al DB di Render
$env:DATABASE_URL="postgresql://poker_db_d9a2_user:ct31NGw6XadUlrGjVoBsO644UMx6jIhP@dpg-d4bnjqv5r7bs739u0mig-a.frankfurt-postgres.render.com/poker_db_d9a2"

# 2. Imposta la connessione a Redis di Render (usa lo stesso URL per tutti e 3)
$env:REDIS_URL="rediss://red-d4bnl7h5pdvs73d1eugg:5iYVLYCK4IyMU9hpx3RV3UjxFG9QL4OJ@frankfurt-keyvalue.render.com:6379"
$env:LIMITER_REDIS_URL="rediss://red-d4bnl7h5pdvs73d1eugg:5iYVLYCK4IyMU9hpx3RV3UjxFG9QL4OJ@frankfurt-keyvalue.render.com:6379/1"
$env:FLASK_LIMITER_STORAGE="rediss://red-d4bnl7h5pdvs73d1eugg:5iYVLYCK4IyMU9hpx3RV3UjxFG9QL4OJ@frankfurt-keyvalue.render.com:6379/1"

# 3. Imposta le altre variabili
$env:FLASK_ENV="production"
$env:SECRET_KEY="diohjweghfewghfweghjdgewdgewhdeg"

# 4. Carica il tuo JSON in una variabile d'ambiente (dal tuo file locale)
$env:PLAYERS_DATA_JSON = (Get-Content -Path ".\private_data.json" -Raw)