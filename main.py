import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional # Agrega esto al inicio de tu archivo junto a tus otros imports


# Cargar variables de entorno desde tu archivo .env (ruta explícita)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug: indicar si se cargaron (no imprimir claves en texto)
print("DEBUG: SUPABASE_URL loaded:", bool(SUPABASE_URL))

app = FastAPI(
    title="API de Predicción de Salarios Tech - UTP",
    description="Proyecto de Lenguajes de Programación aplicando Multiparadigma"
)

# Permitir CORS para la conexión con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# RUTA RAÍZ (Mensaje de bienvenida)
# ==========================================
@app.get("/")
def ruta_principal():
    """Endpoint raíz para verificar que la API está viva."""
    return {
        "mensaje": "¡Bienvenido a la API de Predicción de Salarios Tech!",
        "estado": "En línea",
        "documentacion": "Visita /docs para ver y probar los endpoints interactivos."
    }

# ==========================================
# 1. PARADIGMA ORIENTADO A OBJETOS (POO)
# ==========================================
class PredictorSalario:
    """
    Clase que encapsula la lógica matemática y los coeficientes de predicción.
    Demuestra la abstracción y encapsulamiento exigidos en la rúbrica.
    """
    def __init__(self, datos_historicos: list):
        self.datos = datos_historicos
        self.salario_base = 65000.0  # Salario base de partida en USD
        self.coeficientes_experiencia = {"EN": 1.0, "MI": 1.5, "SE": 2.2, "EX": 3.1}
        self.coeficientes_empresa = {"S": 0.85, "M": 1.1, "L": 1.3}

    def calcular_prediccion(self, exp: str, size: str, remote: int) -> float:
        """Calcula el salario proyectado."""
        factor_exp = self.coeficientes_experiencia.get(exp, 1.2)
        factor_size = self.coeficientes_empresa.get(size, 1.0)
        factor_remoto = 1.05 if remote == 100 else 1.0

        salario_predicho = self.salario_base * factor_exp * factor_size * factor_remoto
        return round(salario_predicho, 2)


# ==========================================
# 2. PARADIGMA FUNCIONAL (Funciones puras)
# ==========================================
# Función lambda de alto orden para traducir códigos de experiencia a texto legible
mapear_experiencia_completa = lambda codigo: {
    "EN": "Junior / Entry-level",
    "MI": "Mid-level / Intermediate",
    "SE": "Senior / Advanced",
    "EX": "Executive / Director"
}.get(codigo, "Desconocido")


# ==========================================
# 3. ENDPOINTS (Paradigma Estructurado)
# ==========================================
@app.get("/api/v1/salarios")
def obtener_todos_los_salarios(
        anio: Optional[str] = None,
        experiencia: Optional[str] = None,
        tamano_empresa: Optional[str] = None,
        modalidad: Optional[str] = None,
        tipo_empleo: Optional[str] = None
):
    """
    Endpoint con filtros dinámicos múltiples.
    Aplica Programación Funcional (filter, map, lambdas) en cascada.
    """
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Traemos un bloque de datos para procesarlos en memoria
        respuesta = supabase.table("data_science_salaries").select("*").limit(1000).execute()
        datos_crudos = respuesta.data

        # ==========================================
        # PARADIGMA FUNCIONAL (Filtrado Dinámico en Cascada)
        # ==========================================
        if anio and anio != "TODOS":
            datos_crudos = list(filter(lambda x: str(x.get("work_year")) == anio, datos_crudos))

        if experiencia and experiencia != "TODOS":
            datos_crudos = list(filter(lambda x: x.get("experience_level") == experiencia, datos_crudos))

        if tamano_empresa and tamano_empresa != "TODOS":
            datos_crudos = list(filter(lambda x: x.get("company_size") == tamano_empresa, datos_crudos))

        if modalidad and modalidad != "TODOS":
            datos_crudos = list(filter(lambda x: str(x.get("remote_ratio")) == modalidad, datos_crudos))

        if tipo_empleo and tipo_empleo != "TODOS":
            datos_crudos = list(filter(lambda x: x.get("employment_type") == tipo_empleo, datos_crudos))

        # Mapeo final para transformar las etiquetas
        datos_transformados = list(map(
            lambda item: {
                **item,
                "experience_label": mapear_experiencia_completa(item["experience_level"])
            },
            datos_crudos
        ))

        return {"total": len(datos_transformados), "salarios": datos_transformados}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en el servidor: {str(e)}")

@app.get("/api/v1/predecir")
def predecir_salario(experience_level: str, company_size: str, remote_ratio: int):
    """Endpoint predictivo que instancia y utiliza el objeto PredictorSalario (POO)."""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # SOLUCIÓN: Cambiamos .select("salary_in_usd") por .select("*")
        # para que Python mapee todo el registro y evite el KeyError.
        respuesta = supabase.table("data_science_salaries").select("*").limit(10).execute()

        if not respuesta.data:
            raise HTTPException(status_code=404, detail="No hay datos suficientes")

        # Instanciación del objeto (POO)
        predictor = PredictorSalario(datos_historicos=respuesta.data)
        salario_estimado = predictor.calcular_prediccion(
            exp=experience_level.upper(),
            size=company_size.upper(),
            remote=remote_ratio
        )

        return {
            "inputs": {
                "experience_level": experience_level,
                "company_size": company_size,
                "remote_ratio": remote_ratio
            },
            "salario_predicho_usd": salario_estimado,
            "moneda": "USD"
        }
    except Exception as e:
        # Agregamos esto temporalmente para que, si hay otro error,
        # la consola de IntelliJ te muestre la línea exacta del problema.
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Esto le dice a Python que levante el servidor de FastAPI en el puerto 8000
    uvicorn.run("main:app", hzzost="127.0.0.1", port=8000, reload=True)