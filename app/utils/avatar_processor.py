# app/utils/avatar_processor.py
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from flask import current_app
from werkzeug.datastructures import FileStorage
from typing import Tuple, Dict, Any, Union

class AvatarProcessor:
    """
    Gestisce l'elaborazione e il salvataggio sicuri degli avatar.
    Implementa ritaglio circolare, mascheratura e ridimensionamento
    in DUE formati (thumbnail e full-size).
    """

    def __init__(self, file_storage: FileStorage, player_id: int):
        self.file_storage = file_storage
        self.player_id = player_id
        
        # Carica la configurazione
        self.save_dir = Path(current_app.config["AVATAR_SAVE_PATH"])
        self.public_url_base = current_app.config["AVATAR_PUBLIC_URL"]
        
        # --- MODIFICA: Carica entrambe le dimensioni ---
        self.thumb_size = current_app.config["AVATAR_FINAL_SIZE"]
        self.full_size = current_app.config["AVATAR_FULL_SIZE"]
        # --- FINE MODIFICA ---
        
        self.max_dim = current_app.config["AVATAR_MAX_ORIGINAL_DIMENSION"]
        self.max_size_bytes = current_app.config["AVATAR_MAX_FILE_SIZE_BYTES"]
        
        # Nomi file finali
        self.final_filename = f"{self.player_id}.png"
        self.full_filename = f"{self.player_id}_full.png"
        
        self.final_filepath = self.save_dir / self.final_filename
        self.full_filepath = self.save_dir / self.full_filename

    def _validate_file(self) -> Tuple[bool, str]:
        # ... (Questa funzione rimane INVARIATA) ...
        """Controlla dimensione e tipo preliminare."""
        self.file_storage.seek(0, os.SEEK_END)
        file_length = self.file_storage.tell()
        self.file_storage.seek(0)
        
        if file_length > self.max_size_bytes:
            mb_limit = self.max_size_bytes / 1024 / 1024
            return False, f"File troppo grande. Limite: {mb_limit:.0f} MB."
            
        if file_length == 0:
            return False, "File vuoto o corrotto."

        mime = self.file_storage.mimetype.lower()
        if mime not in ["image/jpeg", "image/png", "image/webp"]:
             return False, "Formato file non supportato (accettati: JPG, PNG, WebP)."
             
        return True, "Validazione preliminare superata."

    def _process_image(self, img: Image.Image) -> Tuple[Image.Image, Image.Image]:
        """
        Applica il ritaglio circolare e il ridimensionamento.
        Restituisce DUE immagini: (thumbnail, full_image)
        """
        
        # 1. Converte in RGBA
        img = img.convert("RGBA")

        # 2. Ritaglio centrato (crop quadrato)
        # Nota: L'immagine che riceviamo è GIA' ritagliata da Cropper.js,
        # ma questa logica la rende perfettamente quadrata se non lo fosse.
        size = min(img.size)
        left = (img.width - size) / 2
        top = (img.height - size) / 2
        right = (img.width + size) / 2
        bottom = (img.height + size) / 2
        img_cropped = img.crop((left, top, right, bottom))

        # 3. Creazione maschera circolare trasparente
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        # 4. Applicazione maschera
        img_circular = ImageOps.fit(
            img_cropped, 
            mask.size, 
            centering=(0.5, 0.5)
        )
        img_circular.putalpha(mask)

        # 5. Ridimensionamento finale in DUE versioni
        img_thumb = img_circular.resize(
            (self.thumb_size, self.thumb_size), 
            Image.Resampling.LANCZOS
        )
        
        img_full = img_circular.resize(
            (self.full_size, self.full_size), 
            Image.Resampling.LANCZOS
        )
        
        return img_thumb, img_full

    def _delete_existing_files(self):
        """Rimuove vecchi file avatar (sia thumb che full)."""
        try:
            # Rimuove il file .png (e potenziali .jpg, ecc.)
            for f in self.save_dir.glob(f"{self.player_id}.*"):
                if not f.name.endswith('_full.png'): # Non rimuovere il full qui
                    f.unlink()
            
            # Rimuove esplicitamente il file _full.png
            full_file = self.save_dir / self.full_filename
            if full_file.exists():
                full_file.unlink()
                
        except OSError as e:
            current_app.logger.error(
                f"Errore rimozione vecchio avatar per {self.player_id}: {e}"
            )
            pass

    def save(self) -> Dict[str, Any]:
        """
        Metodo principale: valida, processa e salva entrambe le immagini.
        Restituisce un dizionario con l'esito.
        """
        is_valid, error_msg = self._validate_file()
        if not is_valid:
            return {"success": False, "error": error_msg}

        try:
            # 1. Apertura sicura
            with Image.open(self.file_storage.stream) as img:
                
                # 2. Validazione formato
                if img.format not in ["JPEG", "PNG", "WEBP"]:
                    return {"success": False, "error": "Formato immagine non valido."}

                # 3. Validazione dimensioni (sull'immagine ricevuta)
                if img.width > self.max_dim or img.height > self.max_dim:
                    return {
                        "success": False,
                        "error": f"Immagine troppo grande. Dimensioni massime: {self.max_dim}x{self.max_dim}px."
                    }
                
                # 4. Elaborazione (produce thumb e full)
                processed_thumb, processed_full = self._process_image(img)

            # 5. Assicura che la directory esista
            self.save_dir.mkdir(parents=True, exist_ok=True)
            
            # 6. Rimuovi vecchi file
            self._delete_existing_files()

            # 7. Salvataggio finale (PNG ottimizzato)
            processed_thumb.save(
                self.final_filepath, 
                "PNG", 
                optimize=True
            )
            processed_full.save(
                self.full_filepath, 
                "PNG", 
                optimize=True
            )
            
            # 8. Costruisci l'URL pubblico (del thumbnail)
            public_url = f"{self.public_url_base}{self.final_filename}?v={int(os.path.getmtime(self.final_filepath))}"

            # L'API restituisce l'URL del THUMBNAIL per l'anteprima
            return {"success": True, "url": public_url}

        except (IOError, OSError, Image.UnidentifiedImageError) as e:
            current_app.logger.error(
                f"Errore elaborazione avatar per {self.player_id}: {e}"
            )
            return {"success": False, "error": f"Errore durante l'elaborazione dell'immagine: {e}"}