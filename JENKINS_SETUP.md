# Configurar el Job de Jenkins para RunZa Backend

Esto asume que tu Jenkins ya está instalado y corriendo (lo confirmaste).
El `Jenkinsfile` ya viene en este paquete — solo hay que configurar Jenkins
para que lo use.

## 0. Verificar que Jenkins responde

Abre `http://localhost:8080` en el navegador. Si no carga, revisa en
"Servicios" de Windows que el servicio "Jenkins" esté en estado
"En ejecución" (o vuelve a abrir la consola donde lo corriste para la
práctica de la materia).

## 1. Crear la base de datos de pruebas

Con pgAdmin4 (que ya usas): clic derecho en *Databases* → *Create* →
*Database*, nómbrala `runza_test`. No hace falta crear tablas: el
`conftest.py` que ya está en tu repo las crea automáticamente al correr
los tests.

## 2. Agregar las credenciales en Jenkins

*Manage Jenkins* → *Credentials* → *(global)* → *Add Credentials*.
Crea dos, ambas de tipo **Secret text**:

| ID | Secreto |
|---|---|
| `runza-test-database-url` | `postgresql://postgres:TU_PASSWORD@localhost:5432/runza_test` |
| `runza-test-secret-key` | cualquier cadena larga, ej. `jenkins-clave-de-pruebas-no-usar-en-prod` |

Reemplaza `TU_PASSWORD` por la contraseña real de tu usuario `postgres`
local.

## 3. Crear el Pipeline Job

*New Item* → nombre `runza-backend-ci` → tipo **Pipeline** → OK.

En la configuración del job, sección **Pipeline**:
- Definition: `Pipeline script from SCM`
- SCM: `Git`
- Repository URL: `https://github.com/19leonardo/runza-backend.git`
- Branch Specifier: `*/main` (cambia `main` si tu rama principal tiene otro nombre)
- Script Path: `Jenkinsfile`

Guarda. Jenkins ya va a leer el `Jenkinsfile` directamente del repo en
cada corrida (eso incluye el disparador `pollSCM` que ya está definido
adentro del propio Jenkinsfile, así que no necesitas configurar el
trigger de nuevo en la UI).

## 4. Primera corrida manual

Click en **Build Now**. Si todo está bien, vas a ver las 4 etapas
(Checkout, Instalar dependencias, Análisis estático, Tests con
cobertura) en verde, y el resumen de pytest + cobertura en el log.

## 5. Problemas comunes (troubleshooting)

**`'python' no se reconoce como un comando interno o externo`**
Jenkins corre como servicio de Windows con un PATH distinto al de tu
usuario, así que no encuentra Python aunque tú sí puedas correrlo en tu
terminal. Tres soluciones, de más simple a más robusta:
1. Reemplaza `python` por la ruta completa en el `Jenkinsfile`, ej.
   `C:\Users\TU_USUARIO\AppData\Local\Programs\Python\Python311\python.exe -m venv venv`.
2. En *Manage Jenkins* → *Tools*, agrega una instalación de Python si tu
   versión de Jenkins lo soporta.
3. Reinicia el servicio de Jenkins configurado para correr con tu cuenta
   de usuario en vez de "Local System" (Servicios de Windows → Jenkins →
   Propiedades → pestaña *Iniciar sesión como*).

**`could not connect to server: Connection refused` (Postgres)**
El servicio de PostgreSQL no está corriendo. Ábrelo desde *Servicios* de
Windows (busca `postgresql-x64-16`) o desde pgAdmin4.

**El build no se dispara solo al hacer push**
El `pollSCM('H/5 * * * *')` revisa el repo cada ~5 minutos, no al
instante — así evitamos tener que exponer tu Jenkins local a internet
con un webhook real. Si en algún momento quieres disparo instantáneo,
se puede armar con un webhook de GitHub + un túnel (ngrok o Cloudflare
Tunnel), pero no es necesario para la entrega de esta semana.

**Quieres confirmar que de verdad corrió**
Revisa el "Test Result" del build (lo publica el step `junit` del
Jenkinsfile) y el artefacto `coverage.xml` archivado, ambos visibles
desde la página del build en la UI de Jenkins.
