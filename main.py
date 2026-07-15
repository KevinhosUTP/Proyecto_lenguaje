import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

app = FastAPI(
    title="Sistema inteligente de predicción salarial para Ingenieros en Ciencia de Datos",
    description="API con seguridad Bearer Token y manejo de excepciones"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. CONFIGURACIÓN DE SEGURIDAD BEARER TOKEN ---
security = HTTPBearer()

def verificar_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_recibido = credentials.credentials
    if token_recibido != "admin123":
        raise HTTPException(
            status_code=401,
            detail="Acceso denegado. Token de autorización inválido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_recibido

# --- CLASES Y FUNCIONES ---
class PredictorSalario:
    def __init__(self, datos_historicos: list):
        self.datos = datos_historicos
        self.salario_base = 65000.0
        self.coeficientes_experiencia = {"EN": 1.0, "MI": 1.5, "SE": 2.2, "EX": 3.1}
        self.coeficientes_empresa = {"S": 0.85, "M": 1.1, "L": 1.3}

    def calcular_prediccion(self, exp: str, size: str, remote: int) -> float:
        factor_exp = self.coeficientes_experiencia.get(exp, 1.2)
        factor_size = self.coeficientes_empresa.get(size, 1.0)
        factor_remoto = 1.05 if remote == 100 else 1.0
        return round(self.salario_base * factor_exp * factor_size * factor_remoto, 2)

mapear_experiencia_completa = lambda codigo: {
    "EN": "Junior / Entry-level",
    "MI": "Mid-level / Intermediate",
    "SE": "Senior / Advanced",
    "EX": "Executive / Director"
}.get(codigo, "Desconocido")

# --- ENDPOINTS ---
@app.get("/")
def ruta_principal():
    return {"mensaje": "API en línea. Usa endpoints protegidos."}

@app.get("/api/v1/salarios")
def obtener_todos_los_salarios(
        anio: Optional[str] = None,
        experiencia: Optional[str] = None,
        tamano_empresa: Optional[str] = None,
        modalidad: Optional[str] = None,
        tipo_empleo: Optional[str] = None,
        token: str = Depends(verificar_token) # <-- CANDADO DE SEGURIDAD
):
    try:
        if anio and anio.isdigit() and int(anio) > 2025:
            raise HTTPException(status_code=501, detail="Las predicciones para años futuros (mayores a 2025) aún no están implementadas.")

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        query = supabase.table("data_science_salaries").select("*", count="exact")

        if anio and anio != "TODOS": query = query.eq("work_year", int(anio))
        if experiencia and experiencia != "TODOS": query = query.eq("experience_level", experiencia)
        if tamano_empresa and tamano_empresa != "TODOS": query = query.eq("company_size", tamano_empresa)
        if modalidad and modalidad != "TODOS": query = query.eq("remote_ratio", int(modalidad))
        if tipo_empleo and tipo_empleo != "TODOS": query = query.eq("employment_type", tipo_empleo)

        respuesta = query.limit(1000).execute()
        datos_crudos = respuesta.data
        total_registros = respuesta.count

        if not datos_crudos:
            raise HTTPException(status_code=404, detail="No se encontraron registros para esta combinación.")

        datos_transformados = list(map(
            lambda item: {**item, "experience_label": mapear_experiencia_completa(item["experience_level"])},
            datos_crudos
        ))

        return {"total": total_registros, "salarios": datos_transformados}

    except HTTPException as http_e: raise http_e
    except Exception as e: raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/api/v1/predecir")
def predecir_salario(
        experience_level: str,
        company_size: str,
        remote_ratio: int,
        token: str = Depends(verificar_token) # <-- CANDADO DE SEGURIDAD
):
    try:
        if experience_level not in ["EN", "MI", "SE", "EX"]:
            raise HTTPException(status_code=400, detail="Parámetro 'experience_level' inválido. Solo EN, MI, SE o EX.")

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        respuesta = supabase.table("data_science_salaries").select("*").limit(10).execute()

        if not respuesta.data:
            raise HTTPException(status_code=404, detail="No hay datos suficientes de entrenamiento.")

        predictor = PredictorSalario(datos_historicos=respuesta.data)
        salario_estimado = predictor.calcular_prediccion(exp=experience_level.upper(), size=company_size.upper(), remote=remote_ratio)

        return {"inputs": {"experience_level": experience_level, "company_size": company_size, "remote_ratio": remote_ratio}, "salario_predicho_usd": salario_estimado, "moneda": "USD"}

    except HTTPException as http_e: raise http_e
    except Exception as e: raise HTTPException(status_code=500, detail=f"Error en la predicción: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)