import secrets
import string

def genera_password(lunghezza=16):
    # Definisce i caratteri possibili: Lettere (Aa-Zz), Numeri (0-9) e Punteggiatura (!@#$...)
    alfabeto = string.ascii_letters + string.digits
    
    # Genera la password scegliendo caratteri casuali in modo sicuro
    password = ''.join(secrets.choice(alfabeto) for _ in range(lunghezza))
    return password

if __name__ == "__main__":
     print("\nEcco 15 password pronte da copiare:")
     for _ in range(15):
         print(genera_password())