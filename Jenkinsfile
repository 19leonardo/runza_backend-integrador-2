// Jenkinsfile - Pipeline de CI para RunZa Backend
// Pensado para un Jenkins corriendo en Windows (agente local), apuntando
// a una base de datos PostgreSQL local ya existente para pruebas.
//
// Antes de correr esto por primera vez:
//   1. Crear una base de datos vacía llamada "runza_test" en tu Postgres
//      local (con pgAdmin4 alcanza: clic derecho en Databases > Create).
//   2. En Jenkins: Manage Jenkins > Credentials > agregar dos credenciales
//      tipo "Secret text":
//        - ID: runza-test-database-url
//          Secreto: postgresql://postgres:TU_PASSWORD@localhost:5432/runza_test
//        - ID: runza-test-secret-key
//          Secreto: cualquier-cadena-larga-solo-para-pruebas
//   3. Confirmar que el agente de Jenkins encuentra "python" (ver nota
//      en la sección de Troubleshooting que te paso aparte).

pipeline {
    agent any

    environment {
        ENVIRONMENT                  = 'test'
        ALGORITHM                    = 'HS256'
        ACCESS_TOKEN_EXPIRE_MINUTES  = '30'
        REFRESH_TOKEN_EXPIRE_DAYS    = '7'
        ALLOWED_ORIGINS              = 'http://localhost:8081'
        API_V1_PREFIX                = '/api/v1'
        PROJECT_NAME                 = 'RunZa API'
        VERSION                      = '1.0.0'
        DEBUG                        = 'true'
        DATABASE_URL                 = credentials('runza-test-database-url')
        SECRET_KEY                   = credentials('runza-test-secret-key')
    }

    options {
        timestamps()
        // Evita que builds viejos se queden corriendo si mandas varios pushes seguidos
        disableConcurrentBuilds()
    }

    triggers {
        // Revisa el repo cada 5 minutos. Alternativa a un webhook de GitHub,
        // que requeriría exponer este Jenkins local a internet (ngrok, etc.)
        pollSCM('H/5 * * * *')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Instalar dependencias') {
            steps {
                bat 'python -m venv venv'
                bat 'venv\\Scripts\\python.exe -m pip install --upgrade pip'
                bat 'venv\\Scripts\\pip.exe install -r requirements-dev.txt'
            }
        }

        stage('Análisis estático (flake8)') {
            steps {
                bat 'venv\\Scripts\\pip.exe install flake8'
                // Solo bloquea por errores graves (sintaxis, nombres indefinidos)
                bat 'venv\\Scripts\\flake8.exe app --select=E9,F63,F7,F82 --show-source'
            }
        }

        stage('Tests con cobertura (pytest)') {
            steps {
                bat 'venv\\Scripts\\python.exe -m pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=xml --junitxml=pytest-report.xml'            }
        }
    }

    post {
        always {
            junit testResults: 'pytest-report.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'coverage.xml', allowEmptyArchive: true
        }
        success {
            echo 'Pipeline OK: todos los tests pasaron.'
        }
        failure {
            echo 'Pipeline falló: revisa el log de la etapa que rompió arriba.'
        }
    }
}
