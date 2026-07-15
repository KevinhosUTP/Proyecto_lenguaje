import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# Cargar credenciales desde un archivo .env
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://umurbzvavrmrgzdicpdj.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVtdXJienZhdnJtcmd6ZGljcGRqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4NDA2ODE3NCwiZXhwIjoyMDk5NjQ0MTc0fQ.JV6j1OZAKWrpFbFKNu5s5XxMBj2Av1hgfjAj5EtYvWI")

def iniciar_cliente_supabase() -> Client:
    """Inicializa la conexión con la base de datos de Supabase."""
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error de conexión con Supabase: {e}")
        raise

def procesar_e_ingestar_datos():
    """Lee el CSV local completo y carga los registros en Supabase de 1000 en 1000."""
    try:
        supabase = iniciar_cliente_supabase()

        # 1. Quitamos .head(1000) para leer TODO el archivo CSV
        df = pd.read_csv("Salarios2025.csv")

        # Reemplazar valores nulos para evitar errores en base de datos
        df = df.fillna("N/A")

        # Convertir el DataFrame a una lista de diccionarios
        registros = df.to_dict(orient="records")

        print(f"Iniciando inserción de {len(registros)} filas en Supabase...")

        # 2. Cambiamos el tamaño del lote a 10000
        tamano_lote = 10000
        for i in range(0, len(registros), tamano_lote):
            lote = registros[i:i + tamano_lote]
            supabase.table("data_science_salaries").insert(lote).execute()
            print(f"Lote {i // tamano_lote + 1} ({len(lote)} filas) insertado con éxito.")

        print("¡Proceso de ingesta finalizado de manera correcta!")

    except FileNotFoundError:
        print("Error: No se encontró el archivo 'Salarios2025.csv'.")
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la ingesta: {str(e)}")

if __name__ == "__main__":
    procesar_e_ingestar_datos()