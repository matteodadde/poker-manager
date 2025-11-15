# app/routes/api/avatar_routes.py
from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from pathlib import Path # Importa Path
from app.utils.avatar_processor import AvatarProcessor
from app.models import Player # Assicurati che Player sia importato
from app import db # Importa l'istanza db

api_bp = Blueprint('api', __name__)

@api_bp.route('/players/<int:player_id>/avatar', methods=['POST'])
@login_required
def upload_player_avatar(player_id: int):
    """
    Endpoint API per caricare, processare e salvare un nuovo avatar.
    Salva i file su disco; il modello Player leggerà da lì.
    """
    
    # 1. Verifica permessi
    is_admin = getattr(current_user, 'is_admin', False) or (
        hasattr(current_user, 'has_role') and current_user.has_role('admin')
    )
    
    if not is_admin and current_user.id != player_id:
        current_app.logger.warning(
            f"Accesso NEGATO API: Utente {current_user.id} ha tentato di caricare avatar per player {player_id}."
        )
        return jsonify({"success": False, "error": "Permesso negato."}), 403

    # 2. Verifica esistenza giocatore
    player = db.get_or_404(Player, player_id)

    # 3. Verifica presenza file
    if 'avatar' not in request.files:
        return jsonify({"success": False, "error": "Nessun file 'avatar' trovato."}), 400
        
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({"success": False, "error": "Nessun file selezionato."}), 400

    # 4. Passa al processore
    processor = AvatarProcessor(file_storage=file, player_id=player.id)
    result = processor.save()

    # 5. Restituisci il risultato JSON
    if result["success"]:
        
        # --- MODIFICA: Rimossa la logica del database ---
        # Il tuo modello Player (base.py) legge i file
        # direttamente dal disco, non è necessario salvare il nome nel DB.
        
        current_app.logger.info(
            f"Avatar aggiornato con successo (API) per player {player.id} da {current_user.nickname}."
        )
        return jsonify(result), 200
        # --- FINE MODIFICA ---
            
    else:
        current_app.logger.warning(
            f"Fallimento upload avatar (API) per player {player.id}: {result['error']}"
        )
        return jsonify(result), 400


@api_bp.route('/players/<int:player_id>/avatar', methods=['DELETE'])
@login_required
def delete_player_avatar(player_id: int):
    """
    Endpoint API per rimuovere l'avatar di un giocatore.
    Rimuove i file dal disco; il modello Player mostrerà il default.
    """
    # 1. Verifica permessi
    is_admin = getattr(current_user, 'is_admin', False) or (
        hasattr(current_user, 'has_role') and current_user.has_role('admin')
    )
    
    if not is_admin and current_user.id != player_id:
        return jsonify({"success": False, "error": "Permesso negato."}), 403

    player = db.get_or_404(Player, player_id)
    
    try:
        # 2. Rimuovi i file fisici
        save_dir = Path(current_app.config["AVATAR_SAVE_PATH"])
        files_removed = False
        
        # Rimuovi il thumbnail (es. 1.png)
        thumb_file = save_dir / f"{player.id}.png"
        if thumb_file.exists():
            thumb_file.unlink()
            files_removed = True
        
        # Rimuovi il file full (es. 1_full.png)
        full_file = save_dir / f"{player.id}_full.png"
        if full_file.exists():
            full_file.unlink()
            files_removed = True

        # --- MODIFICA: Rimossa la logica del database ---
        # Non c'è nulla da aggiornare nel DB, il modello
        # vedrà che i file mancano e userà il default.
        # --- FINE MODIFICA ---

        if files_removed:
            current_app.logger.info(
                f"Avatar rimosso (API) per player {player.id} da {current_user.nickname}."
            )
            return jsonify({"success": True, "message": "Avatar rimosso."}), 200
        else:
            return jsonify({"success": False, "message": "Nessun avatar da rimuovere."}), 404
            
    except OSError as e:
        current_app.logger.error(
            f"Errore rimozione avatar (API) per {player.id}: {e}"
        )
        return jsonify({"success": False, "error": "Errore del server durante la rimozione."}), 500