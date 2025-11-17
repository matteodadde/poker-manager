# Dockerfile per Poker Manager (Revisionato)

# --- STAGE 1: "Builder" ---
# Questo stage installa strumenti pesanti (build-essential)
# e compila le dipendenze Python.
FROM python:3.11-slim as builder

# Imposta variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa solo le dipendenze di build
# Aggiungiamo 'apt-get clean' per pulire anche la cache dei pacchetti
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
# Le librerie compilate verranno salvate qui
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && rm -rf /root/.cache/pip

# --- STAGE 2: "Final" ---
# Questa è l'immagine finale, super-leggera.
# Non conterrà build-essential.
FROM python:3.11-slim

# Imposta le stesse variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installa solo le dipendenze di *runtime*
# 'libpq5' è la libreria di runtime per Postgres (molto più leggera di libpq-dev)
# 'sqlite3' lo rimuoviamo, dato che è per lo sviluppo (vedi sotto)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Crea l'utente non-root
RUN useradd --system --create-home pokeruser

# Ensure instance folder exists and is writable
RUN mkdir -p /app/instance \
    && chown -R pokeruser:pokeruser /app

USER pokeruser

# 1. Copia le librerie (già presente)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 2. AGGIUNGI QUESTA RIGA: Copia gli eseguibili (flask, gunicorn, ecc.)
COPY --from=builder /usr/local/bin /usr/local/bin
# Questo sostituisce il 'RUN chown...'
COPY --chown=pokeruser:pokeruser . .

# Espone la porta
EXPOSE 5000

# Variabili d'ambiente per la produzione
ENV FLASK_ENV=production

# Comando per avviare l'app
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]

