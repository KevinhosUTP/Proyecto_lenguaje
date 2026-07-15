import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional

# Cargar variables de entorno desde tu archivo .env (ruta explícita)
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=str(env_path))
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Debug: indicar si se cargaron
print("DEBUG: SUPABASE_URL loaded:", bool(SUPABASE_URL))

app = FastAPI(
    title="API de Predicción de Salarios Tech - UTP",
    description="Proyecto Final con manejo avanzado de excepciones (400, 402, 404, 500, 501)"
)

# Permitir CORS para la conexión con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def ruta_principal():
    return {
        "mensaje": "¡Bienvenido a la API de Predicción de Salarios Tech!",
        "estado": "En línea"
    }

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

@app.get("/api/v1/salarios")
def obtener_todos_los_salarios(
        anio: Optional[str] = None,
        experiencia: Optional[str] = None,
        tamano_empresa: Optional[str] = None,
        modalidad: Optional[str] = None,
        tipo_empleo: Optional[str] = None
):
    try:
        if anio and anio.isdigit() and int(anio) > 2025:
            raise HTTPException(status_code=501, detail="Las predicciones para años futuros (mayores a 2025) aún no están implementadas en este modelo.")

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # PARADIGMA DECLARATIVO (SQL a nivel de Base de Datos)
        # Pedimos a Supabase que nos devuelva el total REAL de la tabla con count="exact"
        query = supabase.table("data_science_salaries").select("*", count="exact")

        # Aplicamos los filtros directamente en la consulta SQL
        if anio and anio != "TODOS":
            query = query.eq("work_year", int(anio))
        if experiencia and experiencia != "TODOS":
            query = query.eq("experience_level", experiencia)
        if tamano_empresa and tamano_empresa != "TODOS":
            query = query.eq("company_size", tamano_empresa)
        if modalidad and modalidad != "TODOS":
            query = query.eq("remote_ratio", int(modalidad))
        if tipo_empleo and tipo_empleo != "TODOS":
            query = query.eq("employment_type", tipo_empleo)

        # Ejecutamos la consulta. Traemos una muestra de 1000 para el gráfico, pero obtenemos el Total Real
        respuesta = query.limit(1000).execute()

        datos_crudos = respuesta.data
        total_registros = respuesta.count  # ¡Aquí viene el 93,000 real!

        if not datos_crudos:
            raise HTTPException(status_code=404, detail="No se encontraron registros en la base de datos para esta combinación estricta de filtros.")

        # PARADIGMA FUNCIONAL (Transformación en memoria)
        # Usamos map y lambdas para enriquecer la data antes de enviarla
        datos_transformados = list(map(
            lambda item: {
                **item,
                "experience_label": mapear_experiencia_completa(item["experience_level"])
            },
            datos_crudos
        ))

        return {
            "total": total_registros, # Enviamos el total exacto (ej. 93000)
            "salarios": datos_transformados # Enviamos la muestra gráfica
        }

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/v1/predecir")
def predecir_salario(experience_level: str, company_size: str, remote_ratio: int, version_api: Optional[str] = "v1"):
    try:
        # TRAMPA: Simulador de Código 400 (Bad Request)
        if experience_level not in ["EN", "MI", "SE", "EX"]:
            raise HTTPException(status_code=400, detail="Parámetro 'experience_level' inválido. Solo se acepta EN, MI, SE o EX.")

        # TRAMPA: Simulador de Código 402 (Payment Required)
        if version_api == "v2_premium":
            raise HTTPException(status_code=402, detail="Se requiere una suscripción Premium activa para usar el modelo algorítmico V2.")

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        respuesta = supabase.table("data_science_salaries").select("*").limit(10).execute()

        if not respuesta.data:
            raise HTTPException(status_code=404, detail="No hay datos suficientes de entrenamiento.")

        predictor = PredictorSalario(datos_historicos=respuesta.data)
        salario_estimado = predictor.calcular_prediccion(
            exp=experience_level.upper(),
            size=company_size.upper(),
            remote=remote_ratio
        )

        return {
            "inputs": {"experience_level": experience_level, "company_size": company_size, "remote_ratio": remote_ratio},
            "salario_predicho_usd": salario_estimado,
            "moneda": "USD"
        }

    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error en la predicción: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Se corrigió el typo 'hzzost' a 'host'
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)