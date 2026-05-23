import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    # Si por alguna razón no existe, generamos una temporal (esto fallará al reiniciar el servidor)
    # Lo ideal es que siempre exista en el .env
    ENCRYPTION_KEY = Fernet.generate_key().decode()

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encripta un string si no es None."""
    if data is None:
        return None
    try:
        return cipher_suite.encrypt(str(data).encode()).decode()
    except Exception as e:
        print(f"Error encriptando: {e}")
        return data

def decrypt_data(encrypted_data: str) -> str:
    """Desencripta un string si no es None."""
    if encrypted_data is None:
        return None
    try:
        return cipher_suite.decrypt(str(encrypted_data).encode()).decode()
    except Exception as e:
        # Si falla (por ejemplo si el dato no estaba encriptado), lo devolvemos tal cual
        return encrypted_data
