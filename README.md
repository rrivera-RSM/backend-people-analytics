# People Analytics Backend

Backend de People Analytics construido con FastAPI, SQLAlchemy async y
autenticacion con Microsoft Entra ID / Azure AD.

La API expone datos de empleados, KPIs, evaluaciones, ONA
(`Organizational Network Analysis`), insights de empleado y permisos de
managers. Este README esta pensado como una guia de entrada para una persona
junior que necesite entender el proyecto y empezar a anadir endpoints sin
romper la estructura existente.

## Stack principal

- **FastAPI**: framework web, routing, validacion de parametros y documentacion
  Swagger/OpenAPI.
- **Pydantic v2**: modelos de entrada/salida de la API.
- **SQLAlchemy async**: acceso a base de datos con `AsyncSession`.
- **Uvicorn**: servidor ASGI para ejecutar la API.
- **fastapi-azure-auth**: validacion de tokens de Azure AD.
- **MSAL + Microsoft Graph**: flujo On-Behalf-Of para consultar datos de Graph,
  por ejemplo fotos de usuario.

## Como ejecutar el proyecto

1. Crear y activar un entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install -r requirements.txt
```

Aviso: el codigo importa `sqlalchemy` y usa URLs async como
`postgresql+asyncpg://...`, pero en el `requirements.txt` actual no aparecen
`sqlalchemy` ni `asyncpg`. Si partes de un entorno limpio y aparece un error
tipo `ModuleNotFoundError`, revisa ese archivo de dependencias antes de seguir.

3. Crear un archivo `.env` en la raiz del proyecto con las variables necesarias:

```bash
BACKEND_CORS_ORIGINS=["http://localhost:8000"]
OPENAPI_CLIENT_ID="client-id-de-la-app-swagger"
APP_CLIENT_ID="client-id-de-la-api"
APP_CLIENT_SECRET="secret-de-la-api"
TENANT_ID="tenant-id-de-azure"
DATABASE_URL="postgresql+asyncpg://usuario:password@host:puerto/base"
SQL_ECHO=False
```

4. Arrancar la API:

```bash
python main.py
```

Por defecto se levanta en:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

> Nota: el proyecto espera una base de datos PostgreSQL compatible con las
> tablas y vistas usadas por los modelos SQLAlchemy. No se han encontrado
> migraciones en el repositorio, asi que la estructura de base de datos parece
> gestionarse fuera del backend.

## Estructura del repositorio

```text
.
|-- main.py                         # Punto de entrada FastAPI
|-- settings.py                     # Configuracion desde .env
`-- app/
    |-- auth.py                     # Azure AD, MSAL y Microsoft Graph
    |-- api/
    |   |-- deps.py                 # Inyeccion de repositorios y servicios
    |   `-- v1/                     # Routers HTTP
    |-- infrastructure/
    |   `-- db/
    |       |-- base.py             # Base declarativa SQLAlchemy
    |       |-- session.py          # Engine y sesiones async
    |       `-- models/             # Modelos ORM
    `-- modules/                    # Modulos de negocio
        |-- employees/
        |-- employee_insights/
        |-- ona/
        |-- kpis/
        |-- evaluations/
        `-- app_managers/
```

La organizacion sigue una separacion por capas:

```text
HTTP request
   |
   v
Router: app/api/v1/*.py
   |
   v
Service: app/modules/<modulo>/application/services.py
   |
   v
Repository: app/modules/<modulo>/infrastructure/repo.py
   |
   v
SQLAlchemy models: app/infrastructure/db/models/*
   |
   v
Base de datos
```

## Capas de la aplicacion

### 1. `main.py`

Es el punto de entrada. Crea la instancia `FastAPI`, configura Swagger OAuth,
CORS, carga la configuracion OpenID de Azure al arrancar e incluye los routers.

Rutas publicas definidas aqui:

- `GET /`: redirige a `/docs`.

Rutas protegidas definidas aqui:

- `GET /me`: devuelve informacion del usuario autenticado y, opcionalmente, su
  foto desde Microsoft Graph.

Tambien incluye los routers de negocio:

- `/employees`
- `/ona`
- `/kpis`
- `/app-managers`
- `/evaluations`

### 2. `settings.py`

Centraliza la configuracion mediante `pydantic-settings`. Lee variables desde
`.env`.

Variables importantes:

- `BACKEND_CORS_ORIGINS`: origenes permitidos por CORS.
- `OPENAPI_CLIENT_ID`: cliente usado por Swagger UI para login OAuth.
- `APP_CLIENT_ID`: app registration de la API.
- `APP_CLIENT_SECRET`: secreto usado por MSAL para el flujo On-Behalf-Of.
- `TENANT_ID`: tenant de Azure AD.
- `DATABASE_URL`: cadena de conexion de SQLAlchemy async.
- `SQL_ECHO`: si es `True`, SQLAlchemy imprime las queries SQL.

Tambien construye dinamicamente el scope:

```text
api://<APP_CLIENT_ID>/user_impersonation
```

### 3. `app/api/v1`

Contiene los routers HTTP. Un router traduce una llamada REST en una llamada al
servicio de aplicacion correspondiente.

Ejemplo simplificado:

```python
@employee_router.get("/rows", response_model=list[EmployeeRowOut])
async def list_employee_rows(
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.list_rows()
```

Regla practica: el router deberia hacer poco trabajo. Su responsabilidad es:

- Definir path, metodo HTTP y `response_model`.
- Leer parametros de path, query o body.
- Pedir dependencias con `Depends`.
- Devolver el resultado del service.
- Convertir errores esperados en `HTTPException` cuando aplique.

### 4. `app/api/deps.py`

Define las dependencias de FastAPI para construir repositorios y servicios.

Ejemplo:

```python
def get_employee_repo(db: AsyncSession = Depends(get_db)) -> EmployeeRepo:
    return EmployeeRepo(db)


def get_employee_service(
    repo: EmployeeRepo = Depends(get_employee_repo),
) -> EmployeeService:
    return EmployeeService(repo)
```

Esto permite que cada request reciba su propia sesion de base de datos y que el
router no tenga que saber como se construye el servicio.

### 5. `app/modules/<modulo>/application/services.py`

Contiene la logica de aplicacion. Es la capa donde se decide que hacer con los
datos.

Ejemplos:

- Normalizar IDs.
- Comprobar que un manager existe y esta activo.
- Construir insights a partir de evaluaciones y ONA.
- Convertir filas de base de datos en schemas Pydantic.
- Lanzar errores de negocio.

El service no deberia depender directamente de FastAPI salvo en casos
puntuales ya existentes. Idealmente, FastAPI queda en los routers.

### 6. `app/modules/<modulo>/infrastructure/repo.py`

Contiene el acceso a datos. Aqui se escriben queries SQLAlchemy.

Regla practica: si necesitas hablar con la base de datos, hazlo en el repo, no
en el router.

Ejemplo:

```python
stmt = select(Employee).where(Employee.id == employee_id)
res = await self.db.execute(stmt)
return res.scalar_one_or_none()
```

### 7. `app/modules/<modulo>/schemas.py`

Contiene modelos Pydantic de entrada y salida.

- Los modelos `Out` describen respuestas.
- Los modelos `In` describen bodies de entrada.
- Los `Enum` ayudan a limitar valores permitidos.

Usar `response_model` en los routers es importante porque:

- Documenta automaticamente la API.
- Valida la respuesta.
- Evita devolver campos internos por accidente.

### 8. `app/infrastructure/db`

Aqui vive la infraestructura comun de base de datos.

- `base.py`: define `Base`, clase base de los modelos ORM.
- `session.py`: crea el engine async, el `AsyncSessionLocal` y la dependencia
  `get_db`.
- `models/`: modelos SQLAlchemy separados por schemas de base de datos:
  - `core`: empleados, oficinas, sociedades, departamentos, categorias e
    historico de empleado.
  - `people`: salarios, evaluaciones, ONA, KPIs, permisos de managers,
    attrition, etc.

La sesion se crea por request:

```python
async with AsyncSessionLocal() as session:
    yield session
```

Eso significa que cada peticion HTTP trabaja con su propia sesion y esta se
cierra al terminar.

## Modulos de negocio

### Employees

Rutas bajo `/employees`.

Responsabilidades principales:

- Listado de empleados con filtros.
- Listado del equipo de un manager.
- Foto de empleado desde Microsoft Graph.
- Evaluaciones de un empleado.
- Informacion salarial.
- Riesgo de attrition.
- Timeline de cambios organizativos, salariales y evaluaciones.
- Insights de empleado mediante el modulo `employee_insights`.

Archivos clave:

- `app/api/v1/employees.py`
- `app/modules/employees/application/services.py`
- `app/modules/employees/infrastructure/repo.py`
- `app/modules/employees/schemas.py`

### Employee Insights

Modulo usado desde `/employees/{employee_id}/insights`.

Combina informacion de empleado, evaluaciones, registros ONA y relaciones para
generar insights interpretables.

Tiene una clase `EmployeeInsightRules` con umbrales como:

- Score alto o medio de desempeno.
- Delta minimo para detectar cambio de tendencia.
- Percentiles ONA altos.
- Umbrales de influencia transversal, lateral o ascendente.

### ONA

Rutas bajo `/ona`.

ONA significa `Organizational Network Analysis`: analisis de relaciones entre
empleados.

Responsabilidades:

- Devolver un grafo completo de nodos y aristas.
- Devolver relaciones de un empleado concreto.
- Devolver el registro ONA activo de un empleado.

### KPIs

Rutas bajo `/kpis`.

Responsabilidades:

- Consultar KPIs agregados de salario y bonus.
- Filtrar por sociedad, departamento, oficina y categoria.
- Leer de vistas materializadas:
  - `people.mv_salary_increase_avgs`
  - `people.mv_bonus_avgs`

El repo contiene una logica importante: cuando se filtra por una dimension, se
permiten tanto registros especificos como agregados globales (`NULL`) para
construir una tabla de resultados jerarquica.

### Evaluations

Rutas bajo `/evaluations`.

Responsabilidades:

- Devolver un scatter del ultimo ciclo de evaluaciones.
- Cruzar evaluacion de desempeno con percentil ONA.
- Evitar exponer PII: devuelve IDs y dimensiones, no nombres ni emails.

Nota de seguridad: a diferencia de otros routers, `app/api/v1/evaluations.py`
no declara actualmente `Security(azure_scheme, scopes=["user_impersonation"])`
en el router. Si este endpoint debe ser privado, conviene anadir esa dependencia
igual que en `employees`, `ona`, `kpis` y `app_managers`.

### App Managers

Rutas bajo `/app-managers`.

Responsabilidades:

- Anadir empleados gestionados por un manager.
- Revocar empleados gestionados por un manager.
- Validar que el manager existe y esta activo.
- Evitar self-management.
- No borrar relaciones: las desactiva con `bol_active = 0`.

## Autenticacion y autorizacion

La autenticacion se basa en Microsoft Entra ID / Azure AD.

### Componentes principales

En `app/auth.py`:

- `azure_scheme`: instancia de `SingleTenantAzureAuthorizationCodeBearer`.
- `acquire_graph_token_obo`: obtiene un token de Microsoft Graph usando el
  flujo On-Behalf-Of.
- `extract_bearer_token`: extrae el token del header `Authorization`.
- `get_me`: construye la respuesta de `/me`.
- `graph_get_user_photo_by_oid`: obtiene la foto de un usuario por OID.

### Que token espera la API

Los endpoints protegidos esperan un header:

```text
Authorization: Bearer <access_token>
```

El token debe ser emitido para esta API y contener el scope:

```text
api://<APP_CLIENT_ID>/user_impersonation
```

Ese scope se configura en `settings.py` y se pasa a `azure_scheme`.

### Como se protege un router

Patron usado en la mayoria de routers:

```python
router = APIRouter(
    prefix="/employees",
    tags=["employees"],
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])],
)
```

Esto obliga a que todas las rutas del router tengan un token valido con el
scope requerido.

Algunas rutas tambien incluyen:

```python
dependencies=[Depends(azure_scheme)]
```

o reciben:

```python
current_user = Depends(azure_scheme)
```

Esto permite acceder al usuario autenticado dentro del endpoint o reforzar la
dependencia a nivel de ruta.

### Swagger UI y login

`main.py` configura Swagger para usar OAuth con PKCE:

```python
swagger_ui_init_oauth={
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": settings.OPENAPI_CLIENT_ID,
    "scopes": [
        "openid",
        "profile",
        f"api://{settings.APP_CLIENT_ID}/user_impersonation",
    ],
}
```

En `/docs`, el boton `Authorize` permite iniciar sesion y probar endpoints
protegidos desde Swagger.

### Microsoft Graph y flujo On-Behalf-Of

Para obtener fotos de usuario, la API no usa directamente el token recibido
para llamar a Graph. Hace esto:

1. Recibe el token del usuario en `Authorization`.
2. Extrae el bearer token.
3. Usa MSAL con `APP_CLIENT_ID`, `APP_CLIENT_SECRET` y `TENANT_ID`.
4. Ejecuta `acquire_token_on_behalf_of`.
5. Obtiene un token para `https://graph.microsoft.com/.default`.
6. Llama a Graph:
   - `/me/photos/{size}/$value`
   - `/users/{oid}/photos/{size}/$value`

Esto se llama flujo **On-Behalf-Of**: la API actua en nombre del usuario.

## Como anadir un endpoint nuevo

Supongamos que queremos anadir:

```text
GET /employees/{employee_id}/basic-profile
```

### Paso 1: definir el schema de salida

En `app/modules/employees/schemas.py`:

```python
class EmployeeBasicProfileOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
```

### Paso 2: anadir una query al repo

En `app/modules/employees/infrastructure/repo.py`:

```python
async def get_basic_profile(self, employee_id: int):
    stmt = (
        select(
            Employee.id,
            Employee.first_name,
            Employee.last_name,
            Employee.email,
        )
        .where(Employee.id == employee_id)
    )
    res = await self.db.execute(stmt)
    return res.mappings().first()
```

El repo solo recupera datos. No decide codigos HTTP.

### Paso 3: anadir el metodo en el service

En `app/modules/employees/application/services.py`:

```python
async def employee_basic_profile(
    self,
    employee_id: int,
) -> EmployeeBasicProfileOut:
    row = await self.read_repo.get_basic_profile(employee_id)
    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")
    return EmployeeBasicProfileOut(**row)
```

El service coordina la logica: llama al repo, valida casos esperados y devuelve
un modelo de salida.

### Paso 4: crear la ruta en el router

En `app/api/v1/employees.py`:

```python
@employee_router.get(
    "/{employee_id}/basic-profile",
    response_model=EmployeeBasicProfileOut,
    dependencies=[Depends(azure_scheme)],
)
async def get_employee_basic_profile(
    employee_id: int,
    service: EmployeeService = Depends(get_employee_service),
):
    return await service.employee_basic_profile(employee_id)
```

Como `employee_router` ya esta incluido en `main.py`, no hace falta tocar
`main.py` para este caso.

### Paso 5: probarlo

Arranca la API y abre:

```text
http://localhost:8000/docs
```

Desde Swagger:

1. Pulsa `Authorize`.
2. Inicia sesion.
3. Busca el endpoint nuevo.
4. Ejecutalo con un `employee_id` existente.

### Paso 6: si es un modulo nuevo

Si el endpoint pertenece a un modulo nuevo, por ejemplo `departments`, hay que
crear mas piezas:

```text
app/modules/departments/
|-- schemas.py
|-- application/
|   `-- services.py
`-- infrastructure/
    `-- repo.py

app/api/v1/departments.py
```

Luego registrar dependencias en `app/api/deps.py`:

```python
def get_department_repo(db: AsyncSession = Depends(get_db)) -> DepartmentRepo:
    return DepartmentRepo(db)


def get_department_service(
    repo: DepartmentRepo = Depends(get_department_repo),
) -> DepartmentService:
    return DepartmentService(repo)
```

Y finalmente incluir el router en `main.py`:

```python
from app.api.v1.departments import departments_router

app.include_router(departments_router)
```

## Convenciones del proyecto

- Usar `async def` en endpoints, services y repos.
- Usar `await` para llamadas a base de datos.
- Mantener SQLAlchemy dentro de los repositorios.
- Mantener la logica de negocio dentro de los services.
- Mantener FastAPI, `Depends`, `Query`, `Security` y `HTTPException` sobre todo
  en los routers.
- Definir modelos Pydantic para respuestas estables.
- Evitar devolver modelos ORM directamente si la respuesta forma parte de la
  API publica.
- Usar `response_model` siempre que sea posible.
- Aplicar paginacion (`limit`, `offset`) en listados grandes.
- No borrar historicos si el modelo usa vigencia o flags como `bol_active`;
  seguir el patron existente de desactivar o cerrar vigencia.

## Base de datos

El backend usa SQLAlchemy async:

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.SQL_ECHO,
)
```

`pool_pre_ping=True` ayuda a evitar errores por conexiones muertas en pools de
larga duracion.

Los modelos se dividen principalmente en dos schemas:

### Schema `core`

- `employee`
- `employee_hst`
- `society`
- `department`
- `office`
- `category`

### Schema `people`

- `salary`
- `evaluation`
- `positive_impact`
- `employee_attrition`
- `ona_active`
- `ona_employee_node`
- `ona_insights`
- `ona_question`
- `app_manager`
- `app_manager_employee`
- `mv_salary_increase_avgs`
- `mv_bonus_avgs`

## Flujo mental para leer el codigo

Si quieres entender un endpoint, sigue este orden:

1. Busca la ruta en `app/api/v1`.
2. Mira que service usa con `Depends(...)`.
3. Abre ese service en `app/modules/<modulo>/application/services.py`.
4. Mira que metodo del repo llama.
5. Abre el repo en `app/modules/<modulo>/infrastructure/repo.py`.
6. Revisa los modelos SQLAlchemy usados en `app/infrastructure/db/models`.
7. Revisa el schema Pydantic para saber exactamente que devuelve la API.

Ejemplo:

```text
GET /employees/{employee_id}/timeline-evolution
   -> app/api/v1/employees.py
   -> EmployeeService.employee_timeline_evolution
   -> EmployeeRepo.get_employee_history_timeline
   -> EmployeeRepo.get_employee_salary_timeline
   -> EmployeeRepo.get_employee_evaluation_timeline
   -> EmployeeTimelineEvolutionOut
```

## Consejos para juniors

- No empieces modificando SQL complejo. Primero entiende que respuesta necesita
  el frontend o consumidor de la API.
- Si el endpoint devuelve datos, empieza por el schema `Out`.
- Si el endpoint recibe body, crea un schema `In`.
- Si hay una query nueva, escribela en el repo y prueba que devuelve lo minimo
  necesario.
- Si hay reglas de negocio, ponlas en el service.
- Si algo debe estar protegido, anade `Security(azure_scheme, scopes=["user_impersonation"])`
  al router o endpoint.
- Si tocas permisos, salarios, evaluaciones o datos personales, revisa dos veces
  que no estas exponiendo mas informacion de la necesaria.

## Estado actual de calidad

- No se han encontrado tests automatizados en el repositorio.
- No se han encontrado migraciones de base de datos.
- `requirements.txt` no incluye actualmente `sqlalchemy` ni `asyncpg`, aunque
  el codigo los necesita para la capa de base de datos async.
- `requirements.txt` incluye herramientas de formato/lint como `black` y
  `flake8`, pero no hay comandos de proyecto definidos en un `pyproject.toml`.

Antes de cambios grandes, conviene anadir tests al menos para services y repos
criticos, especialmente autenticacion, permisos de managers e insights.
