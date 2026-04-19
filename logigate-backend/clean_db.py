import sqlite3
import os

db_path = r'C:\Users\USER\Desktop\LOGIGATE\LogiGate\logigate-backend\logigate.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Borrar placas que empiezan con I o terminan con F o T (suelen ser tornillos o bordes)
    cursor.execute('DELETE FROM "Registros_Accesos" WHERE "Vehiculo_Placa" LIKE "I%" OR "Vehiculo_Placa" LIKE "%F" OR "Vehiculo_Placa" LIKE "%T"')
    cursor.execute('DELETE FROM "Vehiculos" WHERE "Vehiculo_Placa" LIKE "I%" OR "Vehiculo_Placa" LIKE "%F" OR "Vehiculo_Placa" LIKE "%T"')
    
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"Base de datos limpia. Se borraron {deleted_count} registros fantasmas.")
else:
    print("No se encontró la base de datos.")
