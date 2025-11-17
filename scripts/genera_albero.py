# genera_albero.py
"""
Genera una rappresentazione testuale dell'albero delle directory del progetto,
escludendo i file e le cartelle non necessari (cache, venv, segreti).
"""
import os
from pathlib import Path

# --- Configurazione ---

# Directory da cui iniziare
ROOT_DIR = Path('.')
# Nome del file di output
OUTPUT_FILE = 'albero_progetto.txt'

# Cartelle da escludere completamente
EXCLUDE_DIRS = {
    '__pycache__',
    'venv',          # Ambiente virtuale
    '.venv',         # Ambiente virtuale (alternativo)
    'env',           # Ambiente virtuale (alternativo)
    'node_modules',  # Dipendenze NPM
    '.git',          # Repository Git
    '.vscode',       # Configurazione VS Code
    '.idea',         # Configurazione PyCharm
    'instance',      # Database e log
    'migrations',    # Script di migrazione DB
    'htmlcov',       # Report di coverage HTML
    '.pytest_cache',
    '.mypy_cache',
    '.benchmarks',    # Cartella di benchmark
}

# Nomi di file esatti da escludere
EXCLUDE_FILENAMES = {
    '.DS_Store',     # File di sistema MacOS
    '.env',          # Contiene segreti!
    '.flaskenv',
    OUTPUT_FILE,     # Il file di output stesso
    '.coverage',     # File dati di coverage
    'poker.db',      # Per sicurezza, anche se dovrebbe essere in 'instance'
}

# Estensioni di file da escludere
EXCLUDE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd',  # Python cache
    '.swp',                 # Swap file (Vim)
    '.log',                 # File di log
    '.db', '.sqlite', '.sqlite3' # File di database generici
}
# --- Fine Configurazione ---


def should_exclude(entry: os.DirEntry) -> bool:
    """
    Controlla se un file o una cartella deve essere esclusa.
    Usa os.DirEntry per efficienza.
    """
    name = entry.name
    
    # Escludi cartelle
    if entry.is_dir() and name in EXCLUDE_DIRS:
        return True
    
    # Escludi nomi di file esatti
    if entry.is_file() and name in EXCLUDE_FILENAMES:
        return True
    
    # Escludi per estensione
    if entry.is_file():
        # Ottieni l'estensione usando pathlib
        ext = Path(name).suffix
        if ext in EXCLUDE_EXTENSIONS:
            return True
                
    return False


def build_tree(dir_path: Path, prefix: str = '') -> list[str]:
    """
    Costruisce ricorsivamente l'albero delle directory.
    """
    lines = []
    
    # Usa os.scandir() per efficienza (ottiene is_dir/is_file)
    try:
        # Filtra le voci escluse
        entries = [e for e in os.scandir(dir_path) if not should_exclude(e)]
        
        # Ordina per tipo (cartelle prima) e poi per nome
        entries.sort(key=lambda e: (e.is_file(), e.name.lower()))
        
    except FileNotFoundError:
        return [] # Ignora se la cartella non esiste
    except NotADirectoryError:
        return [] # Ignora se non è una cartella

    for index, entry in enumerate(entries):
        # Determina il connettore (ultimo elemento vs altri)
        connector = '└── ' if index == len(entries) - 1 else '├── '
        lines.append(f"{prefix}{connector}{entry.name}")
        
        if entry.is_dir():
            # Prepara il prefisso per il livello successivo
            extension = '    ' if index == len(entries) - 1 else '│   '
            lines.extend(build_tree(Path(entry.path), prefix + extension))
            
    return lines


def main():
    """
    Funzione principale: genera l'albero e lo scrive su file.
    """
    print(f"Generazione dell'albero del progetto in corso (radice: '{ROOT_DIR.name}')...")
    
    try:
        root_name = os.path.basename(os.path.abspath(ROOT_DIR))
        lines = [root_name] # Aggiunge il nome della cartella radice all'inizio
        lines.extend(build_tree(ROOT_DIR))
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for line in lines:
                f.write(line + '\n')
                
        print(f"Albero del progetto salvato con successo in '{OUTPUT_FILE}'.")
        print(f"Totale righe: {len(lines)}")
        
    except Exception as e:
        print(f"ERRORE durante la generazione dell'albero: {e}")


if __name__ == "__main__":
    main()
    