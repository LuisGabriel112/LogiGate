import os
import sys

# Añadir el directorio actual al path para importar modelos y utilidades
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models import Registro
from security_utils import encrypt_data, decrypt_data
from cryptography.fernet import InvalidToken

def migrate_existing_data():
    db = SessionLocal()
    try:
        registros = db.query(Registro).all()
        print(f"Encontrados {len(registros)} registros para procesar.")
        
        count = 0
        for r in registros:
            changed = False
            
            # Intentar desencriptar para ver si ya está encriptado
            # Si decrypt_data lanza error o el dato no cambia, es que está en crudo
            
            # Procesar PLACA
            if r.placa:
                try:
                    # Si esto falla, es que no está encriptado con la llave actual
                    decrypt_data(r.placa)
                    # Si llega aquí y el dato es diferente a r.placa, es que ya estaba encriptado
                    # Pero como el helper devuelve el mismo dato si falla, necesitamos una prueba mejor
                except:
                    pass
                
                # Regla simple: Si empieza por 'gAAAAA' (típico de Fernet), asumimos que ya está
                if not str(r.placa).startswith("gAAAAA"):
                    r.placa = encrypt_data(r.placa)
                    changed = True

            # Procesar CONDUCTOR
            if r.conductor and not str(r.conductor).startswith("gAAAAA"):
                r.conductor = encrypt_data(r.conductor)
                changed = True
                
            # Procesar NOTAS
            if r.notas and not str(r.notas).startswith("gAAAAA"):
                r.notas = encrypt_data(r.notas)
                changed = True
            
            if changed:
                count += 1
        
        db.commit()
        print(f"Migración completada. Se encriptaron {count} registros que estaban en crudo.")
        
    except Exception as e:
        print(f"Error durante la migración: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_existing_data()
