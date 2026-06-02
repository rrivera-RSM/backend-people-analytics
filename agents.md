# agents.md

Guía para agentes (y colaboradores) que trabajen en este backend FastAPI de People Analytics.

## 1) Objetivo del repositorio
- API FastAPI para exponer datos de people analytics.
- Arquitectura modular por dominio (`app/modules/*`) con separación por capas.
- DB asíncrona con SQLAlchemy (`AsyncSession`) y DI vía `Depends`.

## 2) Estructura del proyecto
- `main.py`: inicialización de FastAPI, routers públicos/protegidos, CORS, arranque uvicorn.
- `app/api/v1/*.py`: endpoints HTTP por dominio.
- `app/api/deps.py`: factorías de repositorios/servicios para inyección de dependencias.
- `app/modules/<dominio>/application/services.py`: lógica de aplicación/casos de uso.
- `app/modules/<dominio>/infrastructure/repo.py`: acceso a datos (queries SQLAlchemy).
- `app/modules/<dominio>/schemas.py`: esquemas request/response.
- `app/infrastructure/db/models/**`: modelos ORM.
- `app/infrastructure/db/session.py`: motor async, session maker y `get_db`.
- `settings.py`: configuración (DB, CORS, auth, etc).
- `app/auth.py`: autenticación Azure AD (`fastapi-azure-auth`).

## 3) Stack técnico
- Python + FastAPI
- SQLAlchemy async
- Pydantic v2 (`pydantic-settings`)
- Uvicorn
- Auth: `fastapi-azure-auth`

Dependencias en `requirements.txt`.

## 4) Flujo recomendado para cambios
1. Localiza el dominio afectado (`employees`, `ona`, `kpis`, `app_managers`, `employee_insights`, `evaluations`).
2. Implementa primero en `infrastructure/repo.py` (si hay cambios de acceso a datos).
3. Orquesta reglas de negocio en `application/services.py`.
4. Expón/ajusta contratos en `schemas.py`.
5. Conecta endpoint en `app/api/v1/<dominio>.py`.
6. Registra dependencias en `app/api/deps.py` si introduces nuevos services/repos.
7. Si es un módulo nuevo, añade su router en `main.py` con `app.include_router(...)`.

## 5) Convenciones de diseño
- Mantener la lógica de negocio fuera de routers.
- Routers: validación de entrada/salida, auth y delegación a servicios.
- Servicios: reglas de negocio, composición de datos, manejo de casos de uso.
- Repos: solo acceso a DB (consultas, filtros, joins, paginación).
- Mantener tipado explícito y retornos consistentes con `schemas.py`.
- Reutilizar la sesión async inyectada por `get_db`; no crear engines/sesiones ad hoc.

## 6) Seguridad y autenticación
- Existen rutas públicas y protegidas.
- Las rutas protegidas usan `Security(azure_scheme, scopes=["user_impersonation"])`.
- Evitar exponer datos sensibles en logs/respuestas de error.

## 7) Comandos útiles
Crear entorno e instalar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ejecutar API:
```bash
python main.py
```

Alternativa uvicorn:
```bash
uvicorn main:app --host localhost --port 8000 --reload
```

## 8) Checklist para PRs/cambios de agente
- El endpoint responde con el schema esperado.
- No se rompió la DI en `app/api/deps.py`.
- El router del módulo está incluido en `main.py`.
- Errores HTTP coherentes (`HTTPException` cuando aplique).
- Consultas async sin bloqueos ni sesiones huérfanas.
- Sin secretos hardcodeados (usar `settings.py` / `.env`).

## 9) Cómo añadir un módulo nuevo
1. Crear estructura:
   - `app/modules/<nuevo>/application/services.py`
   - `app/modules/<nuevo>/infrastructure/repo.py`
   - `app/modules/<nuevo>/schemas.py`
2. Crear router `app/api/v1/<nuevo>.py`.
3. Registrar dependencias en `app/api/deps.py`.
4. Incluir router en `main.py`.
5. Si aplica, crear/usar modelos en `app/infrastructure/db/models/...`.

## 10) Notas para agentes
- Evita cambios globales de estilo no solicitados.
- Mantén cambios acotados al dominio impactado.
- Si tocas queries complejas, documenta brevemente decisiones de filtrado/joins.
- Si introduces comportamiento nuevo, añade ejemplos de request/response en el PR o en doc técnica.

---
Si quieres, en un siguiente paso puedo convertir este `agents.md` en una versión más estricta con plantillas de tareas (bugfix/feature/refactor), Definition of Done y convenciones de testing por módulo.
