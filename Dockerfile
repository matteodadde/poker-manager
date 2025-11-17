# Dockerfile per Poker Manager (Revisionato e Corretto)

# --- STAGE 1: "Builder" ---
# Questo stage installa strumenti pesanti (build-essential)
# e compila le dipendenze Python.
FROM python:3.11-slim as builder

# Imposta variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa solo le dipendenze di build
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia i file per l'installazione
COPY requirements.txt setup.cfg ./

# Installa le dipendenze
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

# --- STAGE 2: "Final" ---
# Questa è l'immagine finale, super-leggera.
FROM python:3.11-slim

# Imposta le stesse variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa solo le dipendenze di *runtime*
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Crea l'utente non-root
RUN useradd --system --create-home pokeruser

# Crea le cartelle necessarie come root
RUN mkdir -p /app/instance

# Copia le librerie python (dal builder)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copia gli eseguibili python (gunicorn, flask, ecc. dal builder)
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia l'applicazione (ancora come root)
COPY . .

# --- CORREZIONE PERMESSI (CRITICA) ---
# Assegna i permessi di esecuzione agli script PRIMA di cambiare utente.
# Questo risolve l'errore "permission denied" causato da Windows/Git.
RUN chmod +x /app/scripts/*.sh

# Assegna la proprietà di tutto all'utente non-root
RUN chown -R pokeruser:pokeruser /app

# Ora passa all'utente non-root
USER pokeruser

# Espone la porta
EXPOSE 5000

# Variabili d'ambiente per la produzione
ENV FLASK_ENV=production

# --- CORREZIONE AVVIO (CRITICA) ---
# Esegui l'entrypoint script che si occupa di migrazioni e avvio
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Il CMD viene passato come argomento ($@) all'entrypoint.
# entrypoint.sh eseguirà questo DOPO le migrazioni.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]