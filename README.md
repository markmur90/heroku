# Swift App

## Descripción
swiftapi4 es un proyecto diseñado para proporcionar una API rápida y eficiente para [descripción breve del propósito del proyecto].

## Instalación

1. Crea y activa un entorno virtual, instala las dependencias y realiza las migraciones:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   python manage.py makemigrations
   python manage.py migrate
   # Ejecuta nuevamente este comando tras actualizar el repositorio
   # para aplicar migraciones nuevas (por ejemplo, la columna `oauth_state`).
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
2. Recopila los archivos estáticos:
   ```bash
   python manage.py makemigrations && python manage.py migrate
3. Recopila los archivos estáticos:
   ```bash
   python manage.py makemigrations && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000
4. Inicia el servidor de desarrollo:
   ```bash
   source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:8000
5. Comando combinado para configurar y ejecutar el servidor:
   ```bash
   source .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt && python manage.py makemigrations && python manage.py migrate && python manage.py createsuperuser && gunicorn config.wsgi:application --bind 0.0.0.0:8000


## Gunicorn

Solución para producción:
Para implementar tu aplicación en un entorno de producción, necesitas usar un servidor WSGI o ASGI como Gunicorn, uWSGI, o Daphne junto con un servidor web como Nginx o Apache. Aquí tienes los pasos básicos:

1. Instala Gunicorn:
   ```bash
   pip install gunicorn
2. Ejecuta Gunicorn:
   ```bash
   gunicorn config.wsgi:application --bind 0.0.0.0:8000
3. Configura un servidor web (como Nginx) para manejar solicitudes y servir archivos estáticos.
Asegúrate de que DEBUG esté en False en tu archivo settings.py (ya lo tienes configurado correctamente).

4. Configura ALLOWED_HOSTS con los dominios o direcciones IP permitidas para tu aplicación:
   ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com']
5. Usa HTTPS y configura correctamente los certificados SSL.


## Nginx

1. Instalar Nginx
   ```bash
   sudo apt-get update && sudo apt-get install -y nginx
2. Crea archivo:
   ```bash
   sudo nano /etc/nginx/site-available/api_bank
3. Crea un archivo de configuración para tu aplicación en /etc/nginx/sites-available/tu_app:
   ```bash
   server {
   listen 80;
   server_name tu-dominio.com www.tu-dominio.com;

   location = /favicon.ico { access_log off; log_not_found off; }
   location /static/ {
      root /ruta/a/tu/proyecto; # Cambia esto por la ruta a tus archivos estáticos
   }

   location / {
      proxy_pass http://127.0.0.1:8000; # Gunicorn escucha en este puerto
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
   }
}


4. Habilita la configuración 
Crea un enlace simbólico para habilitar la configuración:
   ```bash
   sudo ln -s /etc/nginx/sites-available/api_bank /etc/nginx/sites-enabled/
5. Verifica y reinicia Nginx
Verifica que la configuración sea válida:
   ```bash
   sudo nginx -t
6. Si no hay errores, reinicia Nginx:
   ```bash
   sudo systemctl restart nginx
7. Configura archivos estáticos en Django. Asegúrate de haber recopilado los archivos estáticos en tu proyecto:
   ```bash
   python manage.py collectstatic
8. Prueba tu configuración
Accede a tu dominio o dirección IP en el navegador para verificar que todo funcione correctamente.

Con esto, Nginx manejará las solicitudes y servirá los archivos estáticos, mientras que Gunicorn ejecutará tu aplicación Django.


## Choices
     RJCT = "RJCT", "Rechazada"
     RCVD = "RCVD", "Recibida"
     ACCP = "ACCP", "Aceptada"
     ACTC = "ACTC", "Validación técnica aceptada"
     ACSP = "ACSP", "Acuerdo aceptado en proceso"
     ACSC = "ACSC", "Acuerdo aceptado completado"
     ACWC = "ACWC", "Aceptado con cambio"
     ACWP = "ACWP", "Aceptado con pendiente"
     ACCC = "ACCC", "Verificación de crédito aceptada"
     CANC = "CANC", "Cancelada"
     PDNG = "PDNG", "Pendiente"

# 🧠 Automatización de Despliegue — `api_bank_h2`

### Cambios importantes en esta versión

- Todos los scripts usan ahora **bloques elegibles** `DO_*` en lugar de `OMIT_*`, permitiendo un control más preciso con `--do-*`.
- Se ha añadido el comando `d_local_ssl`, que ejecuta entorno local en HTTPS (Gunicorn + Nginx en puerto 8443 con certificado autofirmado).
- Los encabezados de los logs están centrados visualmente para mejorar la auditoría.
- Nuevos alias disponibles:
  - `d_local_ssl` → lanza entorno local con SSL
  - `d_reset` → reinicia entorno seguro
  - `d_reload_aliases` → recarga todos los alias



Este archivo documenta el uso de funciones Bash para automatizar el despliegue, configuración y ejecución del sistema `api_bank_h2` en distintos entornos. Incluye alias funcionales para `local`, `heroku`, `production`, y pruebas SSL.

---

## 🧩 VARIABLES DE CONTROL

| Parámetro(s)           | Variable interna      | Descripción                                       |
| ----------------------- | --------------------- | -------------------------------------------------- |
| `-a` \| `--all`     | `PROMPT_MODE=false` | Ejecutar todos los pasos sin confirmaciones        |
| `-s` \| `--step`    | `PROMPT_MODE=true`  | Modo paso a paso                                   |
| `-W` \| `--dry-run` | `DRY_RUN=true`      | Modo simulación: no realiza acciones destructivas |
| `-d` \| `--debug`   | `DEBUG_MODE=true`   | Activa modo diagnóstico extendido                 |

---

## 🧰 TAREAS DE DESARROLLO LOCAL

| Parámetro(s)                 | Variable interna       | Descripción                                           |
| ----------------------------- | ---------------------- | ------------------------------------------------------ |
| `-L` \| `--do-local`      | `DO_JSON_LOCAL=true` | Cargar archivos locales `.json` y `.env`           |
| `-l` \| `--do-load-local` | `DO_RUN_LOCAL=true`  | Ejecutar entorno local estándar                       |
| `-r` \| `--do-local-ssl`  | `DO_LOCAL_SSL=true`  | Ejecutar entorno local con SSL (Gunicorn + Nginx 8443) |

---

## 💾 BACKUPS Y DEPLOY

| Parámetro(s)             | Variable interna           | Descripción                 |
| ------------------------- | -------------------------- | ---------------------------- |
| `-C` \| `--do-clean`  | `DO_CLEAN=true`          | Limpiar respaldos antiguos   |
| `-Z` \| `--do-zip`    | `DO_ZIP_SQL=true`        | Generar backups ZIP + SQL    |
| `-B` \| `--do-bdd`    | `DO_SYNC_REMOTE_DB=true` | Sincronizar BDD remota       |
| `-H` \| `--do-heroku` | `DO_HEROKU=true`         | Desplegar a Heroku           |
| `-v` \| `--do-vps`    | `DO_DEPLOY_VPS=true`     | Desplegar a VPS (Njalla)     |
| `-S` \| `--do-sync`   | `DO_SYNC_LOCAL=true`     | Sincronizar archivos locales |

---

## 🛠 ENTORNO Y CONFIGURACIÓN

| Parámetro(s)                  | Variable interna   | Descripción                         |
| ------------------------------ | ------------------ | ------------------------------------ |
| `-Y` \| `--do-sys`         | `DO_SYS=true`    | Actualizar sistema y dependencias    |
| `-P` \| `--do-ports`       | `DO_PORTS=true`  | Cerrar puertos abiertos conflictivos |
| `-D` \| `--do-docker`      | `DO_DOCKER=true` | Diagnóstico y soporte Docker        |
| `-M` \| `--do-mac`         | `DO_MAC=true`    | Cambiar dirección MAC aleatoria     |
| `-x` \| `--do-ufw`         | `DO_UFW=true`    | Configurar firewall UFW              |
| `-p` \| `--do-pem`         | `DO_PEM=true`    | Generar claves PEM locales           |
| `-U` \| `--do-create-user` | `DO_USER=true`   | Crear usuario del sistema            |
| `-u` \| `--do-varher`      | `DO_VARHER=true` | Configurar variables Heroku          |

---

## 🗃️ POSTGRES Y MIGRACIONES

| Parámetro(s)            | Variable interna  | Descripción                    |
| ------------------------ | ----------------- | ------------------------------- |
| `-Q` \| `--do-pgsql` | `DO_PGSQL=true` | Configurar conexión PostgreSQL |
| `-I` \| `--do-migra` | `DO_MIG=true`   | Aplicar migraciones Django      |

---

## 🌐 EJECUCIÓN Y TESTING

| Parámetro(s)                  | Variable interna         | Descripción                      |
| ------------------------------ | ------------------------ | --------------------------------- |
| `-G` \| `--do-gunicorn`    | `DO_GUNICORN=true`     | Ejecutar Gunicorn como servidor   |
| `-w` \| `--do-web`         | `DO_RUN_WEB=true`      | Abrir navegador tras despliegue   |
| `-V` \| `--do-verif-trans` | `DO_VERIF_TRANSF=true` | Verificar transferencias SEPA     |
| `-E` \| `--do-cert`        | `DO_CERT=true`         | Generar certificados autofirmados |

---

## 🧠 Alias disponibles y funciones

| Alias | Acción | Descripción |
| ----- | ------ | ----------- |
| `api` | `cd + venv + code api_bank_h2` | Abrir proyecto Django principal |
| `BKapi` | `cd + venv + code api_bank_h2_BK` | Abrir backup del proyecto |
| `api_heroku` | `cd + venv + code api_bank_heroku` | Abrir proyecto en Heroku |
| `update` | `apt-get update/upgrade/full-upgrade` | Actualizar sistema completo |
| `monero` | `bash monero-wallet-gui` | Abrir interfaz gráfica de Monero |
| `d_help` | `./01_full.sh --help` | Muestra ayuda del script maestro |
| `d_step` | `./01_full.sh -s` | Ejecución paso a paso del despliegue |
| `d_all` | `./01_full.sh -a` | Ejecuta todos los bloques disponibles |
| `d_debug` | `./01_full.sh -d` | Modo debug del despliegue |
| `d_menu` | `./01_full.sh --menu` | Menú interactivo FZF |
| `d_status` | `diagnóstico_entorno.sh` | Diagnóstico completo del entorno |
| `ad_local` | `cd + venv + d_local` | Activar entorno y lanzar despliegue local |
| `d_env` | `cd + venv` | Solo entorno activado sin ejecutar nada |
| `d_mig` | `makemigrations + migrate + collectstatic + runserver` | Migraciones y servidor local |
| `d_local` | `./01_full.sh local completo` | Despliegue completo local |
| `d_heroku` | `./01_full.sh producción Heroku` | Despliegue completo en Heroku |
| `d_njalla` | `./01_full.sh VPS Njalla` | Despliegue completo en VPS |
| `d_pgm` | `./01_full.sh + producción + extras` | Backup + migraciones + certificados |
| `d_hek` | `./01_full.sh BDD + variables Heroku` | Sincronizar BDD + Heroku + usuario |
| `d_back` | `./01_full.sh -C -Z` | Limpieza y backup |
| `d_sys` | `./01_full.sh -Y -P -D -M -x` | Actualizar sistema, cerrar puertos, firewall |
| `d_cep` | `./01_full.sh -p -E` | Generar claves PEM y certificados |
| `d_vps` | `./01_full.sh -v` | Desplegar solo en VPS |


## 📂 Recomendación

Agrega este archivo a tu `.bashrc`, `.bash_aliases` o `.zshrc` y luego ejecuta:

```bash
source ~/.bash_aliases
```

Así tendrás acceso inmediato a todas las funciones.

---

## 🌐 Dominio y Servidor

- **Dominio:** `coretransapi.com` (administrado en Njalla)
- **VPS:** Debian 12 (VPS 15) - `504e1ebc.host.njalla.net`
- **IP pública:** `80.78.30.242`
- **IPv6:** `2a0a:3840:8078:30::504e:1ebc:1337`
- **Hostname:** `coretransapi`

---

## 🔐 Seguridad

- **SSH Key (ed25519)**: Acceso únicamente con clave pública
- **Puerto SSH personalizado:** 49222
- **Firewall:** UFW activado + reglas específicas
- **Protección adicional:** fail2ban + acceso recomendado vía VPN + Tor

---

## 📦 Scripts de instalación

Ubicados en el directorio `scripts/`, estos scripts automatizan el setup del VPS:

| Script                           | Función                                 |
| -------------------------------- | ---------------------------------------- |
| `setup_coretransact.sh`        | Script maestro de configuración inicial |
| `vps_instalar_dependencias.sh` | Instala dependencias necesarias          |
| `vps_configurar_ssh.sh`        | Configura claves y puerto SSH            |
| `vps_configurar_sistema.sh`    | Timezone, hostname y usuario             |
| `vps_deploy_django.sh`         | Clonación y despliegue de Django        |
| `vps_configurar_gunicorn.sh`   | Configura Gunicorn para Django           |
| `vps_configurar_nginx.sh`      | Configura Nginx con SSL                  |

---

## 📡 Configuración DNS Njalla

- Crear un registro A para `api.coretransapi.com` apuntando a `80.78.30.242`.
- TTL: `3600`
- Activar DNSSEC y configurar glue records si aplica.

---

## 🔒 Certificados SSL

Certbot se encargará de emitir los certificados:

```bash
certbot --nginx -d api.coretransapi.com
```

Los certificados estarán en:

```nginx
ssl_certificate /etc/letsencrypt/live/api.coretransapi.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/api.coretransapi.com/privkey.pem;
```

---

## ⚙️ Bloque nginx.conf para producción

```nginx
server {
    listen 80;
    server_name api.coretransapi.com;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name api.coretransapi.com;

    ssl_certificate /etc/letsencrypt/live/api.coretransapi.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.coretransapi.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🧑‍💼 USERS — Datos Técnicos de Prueba (Formato Transpuesto)

| Atributo                    | Usuario 1: Claudia Klar                      | Usuario 2: Tom Winter                        | Usuario 3: Baroness Anna Meyer               |
|----------------------------|---------------------------------------------|---------------------------------------------|---------------------------------------------|
| Nombre                     | Claudia Klar                                | Tom Winter                                  | Baroness Anna Meyer                         |
| País                       | DE                                          | DE                                          | DE                                          |
| Dirección                  | Große Bockenheimer Straße 19                | Augsburger Strasse 14a                      | Frankfurter Allee 11                        |
| Ciudad                     | Frankfurt                                   | 80337 München                               | 10247 Berlin                                |
| IBAN                       | `DE00 5007 0010 0200 0402 24`               | `DE00 5007 0010 0200 0448 74`               | `DE00 5007 0010 0200 0448 24`               |
| BIC                        | DEUTDEFFXXX                                 | DEUTDEFFXXX                                 | DEUTDEFFXXX                                 |
| Código Moneda              | EUR                                         | EUR                                         | EUR                                         |
| Teléfono                   | —                                           | `+49 170 123456`, `069 1234567`             | `+49 170 123456`, `069 1234567`             |
| Email                      | —                                           | `TomWinter@example.com`                     | `AnnaMeyer@example.com`                     |
| Identificadores Adicionales | `SecurityAccountID: 100 2040040 00`           | `FKN+PIN: 10020446900014432`<br>`SecurityAccountID: 100 2044690 00` | `SecurityAccountID: 100 2044640 00 20681`<br>`100 2044640 00 20681` |
| OTP                        | [`gluesim`](otpauth://totp/gluesim:100204004000001?secret=7G3DC4GV4J2YFPDS) | [`gluesim`](otpauth://totp/gluesim:100204469000001?secret=ZHEZZYWZJ4R5K2RE) | [`gluesim`](otpauth://totp/gluesim:100204464000001?secret=6XANMMKKWU32XN3G) |
| Counterparty IBAN          | `DE10 0100 0000 0000 0221 37`               | `DE10 0100 0000 0000 0221 37`               | `DE10 0100 0000 0000 0221 37`               |
| Transaction Code           | 123                                         | 123                                         | 123                                         |
| Domain Code                | BFWA                                        | BFWA                                        | BFWA                                        |
| Family Code                | CCRD                                        | CCRD                                        | CCRD                                        |
| Sub Family Code            | CWDL                                        | CWDL                                        | CWDL                                        |
| Saldo                      | —                                           | `1400.95`                                   | `100.95`                                    |
| Ingreso Mensual            | —                                           | `7000 x mes`                                | `700 x mes`                                 |

> 🛡️ Estos datos son utilizados únicamente con fines de simulación y pruebas automatizadas. No se recomienda emplearlos en producción sin cifrado, validación y control de acceso.



---

## 📌 Recomendaciones

- Utilizar claves cifradas y backup en USB offline.
- Registrar toda conexión saliente con logs individuales (ping, OTP, SEPA).
- Usar fail2ban, honeypot y rotación de logs.

---

## 🛡️ Configuración OAuth2 — Django + Heroku + Sandbox Deutsche Bank

Este documento resume cómo configurar correctamente el sistema OAuth2 de una aplicación Django que se comunica con el entorno bancario de Deutsche Bank, siendo compatible tanto con **sandbox/local** como con **producción en Heroku con dominio personalizado**.

---

## 📦 VARIABLES DE ENTORNO REQUERIDAS

## ✅ En desarrollo/sandbox (`.env.local`)

```dotenv
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=0.0.0.0,127.0.0.1
USE_OAUTH2_UI=False

CLIENT_ID=dummy-client-id
CLIENT_SECRET=dummy-client-secret
AUTHORIZE_URL=https://simulator-api.db.com/gw/oidc/authorize
TOKEN_URL=https://simulator-api.db.com/gw/oidc/token
REDIRECT_URI=http://0.0.0.0:8000/oauth2/callback/
SCOPE=openid sepa:transfer
TIMEOUT_REQUEST=10

API_URL=https://simulator-api.db.com/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer
AUTH_URL=https://simulator-api.db.com/gw/dbapi/authorization/v1/authorizations
```

### ✅ En producción Heroku

Configura con:

```bash
heroku config:set DJANGO_SECRET_KEY="clave_supersecreta"
heroku config:set DJANGO_DEBUG=False
heroku config:set DJANGO_ALLOWED_HOSTS="api.coretransapi.com,.herokuapp.com"

heroku config:set USE_OAUTH2_UI=True
heroku config:set CLIENT_ID="tu_client_id_real"
heroku config:set CLIENT_SECRET="tu_client_secret_real"
heroku config:set AUTHORIZE_URL="https://simulator-api.db.com/gw/oidc/authorize"
heroku config:set TOKEN_URL="https://simulator-api.db.com/gw/oidc/token"
heroku config:set REDIRECT_URI="https://api.coretransapi.com/oauth2/callback/"
heroku config:set SCOPE="openid sepa:transfer"
heroku config:set TIMEOUT_REQUEST=10

heroku config:set API_URL="https://simulator-api.db.com/gw/dbapi/paymentInitiation/payments/v1/sepaCreditTransfer"
heroku config:set AUTH_URL="https://simulator-api.db.com/gw/dbapi/authorization/v1/authorizations"
```

---

## 🌍 REDIRECT_URI EN BANCO

En el panel de apps de [developer.db.com](https://developer.db.com/dashboard/developerapps), registra como **redirect URI**:

```
https://api.coretransapi.com/oauth2/callback/
```

---

## 🌐 CONFIGURAR DOMINIO PERSONALIZADO EN HEROKU

### A. Agregar dominio

```bash
heroku domains:add api.coretransapi.com
```

### B. Configurar DNS

En el proveedor DNS, apunta:

```
api.coretransapi.com → <tu-app>.herokudns.com
```

### C. HTTPS automático

```bash
heroku certs:auto:enable
```

---

## 🚦 CONTROL DEL FLUJO UI (PKCE)

Usa `USE_OAUTH2_UI=True` solo cuando:

- Tu app esté aprobada por Deutsche Bank.
- El `REDIRECT_URI` coincida con el registrado.
- El entorno sea producción con HTTPS.

---

## 🛠️ DEBUG & LOGS

Todos los pasos del flujo OAuth están registrados en:

- Archivos por `payment_id`: `schemas/transferencias/transferencia_<id>.log`
- Base de datos: modelo `LogTransferencia`

Esto incluye:

- Headers enviados
- Cuerpo de la petición
- Headers de respuesta
- Cuerpo de la respuesta
- Errores y estado del flujo

---

# **Deploy de Django a VPS Njalla**

---

Guía detallada paso a paso
Requisitos previos

    Proyecto Django funcional en tu computadora local
    Acceso SSH a tu VPS de Njalla (ya lo tienes)
    Git instalado en tu computadora local
    Conocimientos básicos de línea de comandos

## **Proceso principal**

---

### **1 Preparar tu proyecto Django**

Antes de hacer deploy, asegúrate de que tu proyecto esté listo:
Actualiza settings.py

DEBUG = False
ALLOWED_HOSTS = ['tu-dominio.com', 'www.tu-dominio.com', 'tu-ip-vps']

###### Configuración para archivos estáticos

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

###### Configuración para archivos de medios

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

###### Crea un archivo requirements.txt

pip freeze > requirements.txt

Consejo: Considera usar variables de entorno para configuraciones sensibles como claves secretas y credenciales de base de datos.

### **2 Conectarse al VPS**

###### Conéctate a tu VPS de Njalla usando SSH:

ssh usuario@tu-ip-vps

###### Si usas una clave SSH personalizada:

ssh -i ~/.ssh/vps_njalla_nueva root@80.78.30.242

### **3 Instalar dependencias en el servidor**

###### Una vez conectado al VPS, instala las dependencias necesarias:

sudo apt update
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib

### **4 Configurar la base de datos**

###### Configura PostgreSQL para tu proyecto:

sudo -u postgres psql

CREATE DATABASE nombre_db;
CREATE USER nombre_usuario WITH PASSWORD 'contraseña';
ALTER ROLE nombre_usuario SET client_encoding TO 'utf8';
ALTER ROLE nombre_usuario SET default_transaction_isolation TO 'read committed';
ALTER ROLE nombre_usuario SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE nombre_db TO nombre_usuario;
\q

### **5 Transferir tu proyecto**

Hay varias formas de transferir tu proyecto al servidor:

###### Opción 1: Usando Git (recomendado)

En tu servidor:

mkdir -p /var/www/
cd /var/www/
git clone https://tu-repositorio.git proyecto_django

###### Opción 2: Usando SCP

En tu computadora local:

scp -r /ruta/a/tu/proyecto_django usuario@tu-ip-vps:/var/www/

### **6 Configurar el entorno virtual**

###### Crea y configura un entorno virtual para tu proyecto:

cd /var/www/proyecto_django
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

### **7 Configurar Django**

###### Aplica las migraciones y recolecta los archivos estáticos:

cd /var/www/proyecto_django
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser

### **8 Configurar Gunicorn**

###### Crea un archivo de servicio para Gunicorn:

sudo nano /etc/systemd/system/gunicorn.service

###### Añade el siguiente contenido:

[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/proyecto_django
ExecStart=/var/www/proyecto_django/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/proyecto_django/proyecto.sock nombre_proyecto.wsgi:application

[Install]
WantedBy=multi-user.target

###### Inicia el servicio:

sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn

### **9 Configurar Nginx**

###### Crea un archivo de configuración para Nginx:

sudo nano /etc/nginx/sites-available/proyecto_django

###### Añade el siguiente contenido:

server {
    listen 80;
    server_name tu-dominio.com www.tu-dominio.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        root /var/www/proyecto_django;
    }

    location /media/ {
        root /var/www/proyecto_django;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/proyecto_django/proyecto.sock;
    }
}

###### Habilita el sitio y reinicia Nginx:

sudo ln -s /etc/nginx/sites-available/proyecto_django /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

### **10 Configurar HTTPS con Certbot**

###### Instala Certbot y obtén un certificado SSL:

sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com -d www.tu-dominio.com

###### Certbot actualizará automáticamente tu configuración de Nginx para usar HTTPS.

### **11 Configurar el firewall**

###### Configura el firewall para permitir el tráfico web:

sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
sudo ufw status

###### ¡Felicidades! Tu aplicación Django debería estar ahora desplegada y accesible en tu dominio con HTTPS.

---

## **Mantenimiento y actualizaciones**

### **Actualizar tu aplicación**

###### Para actualizar tu aplicación cuando hagas cambios:

cd /var/www/proyecto_django
git pull  # Si usas Git
source venv/bin/activate
pip install -r requirements.txt  # Si hay nuevas dependencias
python manage.py migrate  # Si hay nuevas migraciones
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

### **Copias de seguridad**

Es importante realizar copias de seguridad regularmente:

###### Backup de la base de datos

sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

###### Backup del código

tar -czvf /path/to/backup/proyecto_django_$(date +%Y%m%d).tar.gz /var/www/proyecto_django

###### Automatizar con cron

sudo crontab -e

0 2 * * * sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

---

## **CONFIGURACIONES**

## **Configuración de producción para Django**

### **Configuración de variables de entorno**

###### Es recomendable usar variables de entorno para configuraciones sensibles:

sudo nano /etc/environment

###### Añade tus variables:

DJANGO_SECRET_KEY='tu_clave_secreta'
DJANGO_DEBUG=False
DJANGO_DB_NAME='nombre_db'
DJANGO_DB_USER='nombre_usuario'
DJANGO_DB_PASSWORD='contraseña'
DJANGO_DB_HOST='0.0.0.0'

###### Luego modifica tu settings.py para usar estas variables:

import os

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DJANGO_DB_NAME'),
        'USER': os.environ.get('DJANGO_DB_USER'),
        'PASSWORD': os.environ.get('DJANGO_DB_PASSWORD'),
        'HOST': os.environ.get('DJANGO_DB_HOST'),
        'PORT': '5432',
    }
}

### **Configuración de caché**

###### Para mejorar el rendimiento, configura el caché:

sudo apt install redis-server
pip install django-redis

###### Añade la configuración a settings.py:

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

---

## **Configuración avanzada de Nginx**

###### Optimización de rendimiento

Mejora el rendimiento de Nginx con estas configuraciones:

server {
    # Configuración básica...

    # Compresión gzip
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml;
    gzip_disable "MSIE [1-6]\.";

    # Caché de navegador para archivos estáticos
    location /static/ {
        root /var/www/proyecto_django;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Configuración para archivos de medios
    location /media/ {
        root /var/www/proyecto_django;
        expires 7d;
        add_header Cache-Control "public, max-age=604800";
    }

    # Límites de tamaño de carga
    client_max_body_size 10M;
}

###### Configuración de seguridad

Mejora la seguridad de tu servidor:

server {
    # Configuración básica...

    # Cabeceras de seguridad
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Frame-Options SAMEORIGIN;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Deshabilitar listado de directorios
    autoindex off;

    # Ocultar información de versión
    server_tokens off;
}

---

## **Mantenimiento y actualizaciones**

### **Actualizar tu aplicación**

#### Para actualizar tu aplicación cuando hagas cambios:

cd /var/www/proyecto_django
git pull  # Si usas Git
source venv/bin/activate
pip install -r requirements.txt  # Si hay nuevas dependencias
python manage.py migrate  # Si hay nuevas migraciones
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

### Copias de seguridad

Es importante realizar copias de seguridad regularmente:

###### Backup de la base de datos

sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

###### Backup del código

tar -czvf /path/to/backup/proyecto_django_$(date +%Y%m%d).tar.gz /var/www/proyecto_django

###### Automatizar con cron

sudo crontab -e

0 2 * * * sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

---

## **Solución de problemas comunes**

### **Error 502 Bad Gateway**

Si recibes un error 502, verifica los siguientes aspectos:

###### Comprueba que Gunicorn esté funcionando:

    sudo systemctl status gunicorn

###### Verifica los logs de Gunicorn:

    sudo journalctl -u gunicorn

###### Comprueba los permisos del socket:

    ls -la /var/www/proyecto_django/proyecto.sock

###### Reinicia Gunicorn:

    sudo systemctl restart gunicorn

### Archivos estáticos no se cargan

Si los archivos estáticos no se cargan correctamente:

###### Verifica que hayas ejecutado collectstatic:

    cd /var/www/proyecto_django
    source venv/bin/activate
    python manage.py collectstatic --noinput

###### Comprueba los permisos de la carpeta static:

    sudo chown -R www-data:www-data /var/www/proyecto_django/staticfiles

###### Verifica la configuración de Nginx para los archivos estáticos:

    sudo nano /etc/nginx/sites-available/proyecto_django

### Problemas de base de datos

Si tienes problemas con la base de datos:

###### Verifica que PostgreSQL esté funcionando:

    sudo systemctl status postgresql

###### Comprueba la conexión a la base de datos:

    sudo -u postgres psql -c "SELECT 1;"

###### Verifica las credenciales de la base de datos en settings.py o en las variables de entorno.

### Verificar logs

Los logs son fundamentales para diagnosticar problemas:

###### Logs de Nginx:

    sudo tail -f /var/log/nginx/error.log
    sudo tail -f /var/log/nginx/access.log

###### Logs de Gunicorn:

    sudo journalctl -u gunicorn

###### Logs de Django (si has configurado logging en settings.py):

    tail -f /var/www/proyecto_django/logs/django.log

---

## **Mantenimiento y actualizaciones**

### Actualizar tu aplicación

###### Para actualizar tu aplicación cuando hagas cambios:

cd /var/www/proyecto_django
git pull  # Si usas Git
source venv/bin/activate
pip install -r requirements.txt  # Si hay nuevas dependencias
python manage.py migrate  # Si hay nuevas migraciones
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn

### Copias de seguridad

Es importante realizar copias de seguridad regularmente:

###### Backup de la base de datos

sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

###### Backup del código

tar -czvf /path/to/backup/proyecto_django_$(date +%Y%m%d).tar.gz /var/www/proyecto_django

###### Automatizar con cron

sudo crontab -e

0 2 * * * sudo -u postgres pg_dump nombre_db > /path/to/backup/nombre_db_$(date +%Y%m%d).sql

© `markmur88` – CoreTransAPI Deployment Guide
