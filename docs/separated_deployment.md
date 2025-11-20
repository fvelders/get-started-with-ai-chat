# Gescheiden Frontend/Backend Deployment

Deze gids legt uit hoe je de frontend en backend gescheiden kunt deployen, bijvoorbeeld met de backend op je NAS en de frontend lokaal of ergens anders.

## Inhoudsopgave
- [Overzicht](#overzicht)
- [Backend op NAS Deployen](#backend-op-nas-deployen)
- [Frontend Configureren](#frontend-configureren)
- [Troubleshooting](#troubleshooting)

## Overzicht

De applicatie is nu geconfigureerd om frontend en backend gescheiden te kunnen draaien:

```
┌─────────────┐          HTTP/HTTPS          ┌─────────────┐
│             │    ─────────────────────>    │             │
│  Frontend   │         API Calls            │   Backend   │
│  (Lokaal)   │    <─────────────────────    │   (NAS)     │
│             │                               │             │
└─────────────┘                               └─────────────┘
                                                     │
                                                     ▼
                                              ┌──────────────┐
                                              │ Azure AI     │
                                              │ Services     │
                                              └──────────────┘
```

### Wat is er veranderd?

1. **Frontend configuratie** - Backend URL is nu configureerbaar via environment variabele
2. **CORS support** - Backend accepteert nu requests van andere origins
3. **Dedicated Docker configuratie** - Geoptimaliseerd voor backend-only deployment

## Backend op NAS Deployen

### Optie 1: Docker Compose (Aanbevolen)

#### Stap 1: Kopieer bestanden naar je NAS

Kopieer de volgende bestanden naar een directory op je NAS (bijvoorbeeld `/volume1/docker/ai-chat-backend`):

```bash
ai-chat-backend/
├── Dockerfile.nas-backend
├── docker-compose.nas.yml
└── src/
    ├── .env (te maken)
    ├── requirements.txt
    └── api/
        └── ...
```

#### Stap 2: Configureer Environment Variabelen

Maak een `.env` bestand in de `src` directory op basis van het voorbeeld:

```bash
cd /volume1/docker/ai-chat-backend/src
cp .env.nas-backend .env
nano .env  # Of gebruik een andere teksteditor
```

Vul de volgende verplichte velden in:

```bash
# Azure configuratie
AZURE_AIPROJECT_CONNECTION_STRING="je-connection-string"
AZURE_AI_CHAT_DEPLOYMENT_NAME="gpt-4o-mini"
AZURE_EXISTING_AIPROJECT_ENDPOINT="https://je-project.api.azureml.ms"

# CORS - voeg het adres van je frontend toe
CORS_ORIGINS="http://192.168.1.50:5173,http://localhost:5173"
```

**Belangrijk:** Vervang `192.168.1.50` met het IP-adres waar je frontend draait!

#### Stap 3: Start de Backend

```bash
cd /volume1/docker/ai-chat-backend
docker-compose -f docker-compose.nas.yml up -d
```

Controleer of de container draait:

```bash
docker-compose -f docker-compose.nas.yml ps
docker-compose -f docker-compose.nas.yml logs -f
```

#### Stap 4: Test de Backend

Test of de backend bereikbaar is:

```bash
curl http://NAS-IP:8000/
```

Je zou de HTML homepage moeten zien.

### Optie 2: Synology NAS - Docker GUI

Als je een Synology NAS hebt met Docker support:

1. **Open Docker package** in DSM
2. **Import Image**:
   - Build eerst de image lokaal: `docker build -f Dockerfile.nas-backend -t ai-chat-backend .`
   - Export: `docker save ai-chat-backend > ai-chat-backend.tar`
   - Upload naar NAS en import in Docker package

3. **Create Container**:
   - Image: `ai-chat-backend`
   - Port mapping: `8000:8000`
   - Environment variabelen: Voeg alle variabelen toe uit `.env.nas-backend`
   - Volumes (optioneel): Mount je code directory
   - Auto-restart: Aan

### Optie 3: Zonder Docker (Direct op NAS)

Als je NAS Python ondersteunt:

```bash
# Install Python 3.11+ op je NAS
cd /volume1/apps/ai-chat-backend

# Maak virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
cd src
pip install -r requirements.txt

# Configureer environment
cp .env.nas-backend .env
nano .env

# Start de server
python -m uvicorn api.main:create_app --factory --host 0.0.0.0 --port 8000
```

Voor automatisch opstarten kun je een systemd service of init script maken.

## Frontend Configureren

### Optie 1: Lokale Development Server (Aanbevolen voor Development)

#### Stap 1: Configureer Backend URL

Maak een `.env` bestand in `src/frontend/`:

```bash
cd src/frontend
nano .env
```

Voeg het NAS backend adres toe:

```bash
VITE_API_BASE_URL=http://192.168.1.100:8000
```

**Vervang `192.168.1.100` met het IP-adres van je NAS!**

#### Stap 2: Install Dependencies

```bash
# Zorg dat je in src/frontend/ bent
pnpm install
```

#### Stap 3: Start Development Server

```bash
pnpm dev
```

De frontend draait nu op `http://localhost:5173` en maakt verbinding met je NAS backend!

### Optie 2: Gebouwde Frontend (Productie)

Als je de frontend wilt deployen op een webserver:

#### Stap 1: Build de Frontend

```bash
cd src/frontend

# Configureer backend URL
echo "VITE_API_BASE_URL=http://je-nas-ip:8000" > .env

# Build
pnpm build
```

De gebouwde bestanden komen in `../api/static/react/`.

#### Stap 2: Deploy naar Webserver

Kopieer de inhoud van `../api/static/react/` naar je webserver:

```bash
# Voorbeeld: nginx
cp -r ../api/static/react/* /var/www/html/ai-chat/

# Of upload via SFTP naar je hosting
scp -r ../api/static/react/* user@webserver:/var/www/html/
```

#### Stap 3: Configureer Webserver

**Nginx voorbeeld:**

```nginx
server {
    listen 80;
    server_name ai-chat.example.com;

    root /var/www/html/ai-chat;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets
    location /assets {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Apache voorbeeld:**

```apache
<VirtualHost *:80>
    ServerName ai-chat.example.com
    DocumentRoot /var/www/html/ai-chat

    <Directory /var/www/html/ai-chat>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted

        # SPA routing
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
</VirtualHost>
```

### Optie 3: Static File Server

Gebruik een simpele static file server:

```bash
cd src/frontend

# Build met backend configuratie
echo "VITE_API_BASE_URL=http://192.168.1.100:8000" > .env
pnpm build

# Start static server
cd ../api/static/react
python -m http.server 3000
```

Frontend is nu bereikbaar op `http://localhost:3000`.

## Netwerk Configuratie

### Firewall op NAS

Zorg dat poort 8000 open staat op je NAS:

**Synology:**
1. Control Panel → Security → Firewall
2. Maak regel: Allow port 8000 from Local Network

**QNAP:**
1. Control Panel → Security → Firewall
2. Add rule: Allow TCP 8000

### Router Port Forwarding (Optioneel)

Als je de backend van buiten je netwerk wil bereiken:

1. Open je router configuratie
2. Port forward 8000 → NAS IP:8000
3. **BELANGRIJK:** Gebruik HTTPS en authentication!

**Aanbeveling:** Gebruik een reverse proxy met SSL (nginx, Traefik) voor productie.

## Beveiliging

### Basic Authentication

Voeg credentials toe aan je backend `.env`:

```bash
WEB_APP_USERNAME="admin"
WEB_APP_PASSWORD="sterksecretwachtwoord"
```

### CORS Restrictie

Beperk CORS tot specifieke origins in plaats van `*`:

```bash
# Alleen specifieke frontend toestaan
CORS_ORIGINS="http://192.168.1.50:5173"

# Meerdere origins
CORS_ORIGINS="http://192.168.1.50:5173,https://chat.example.com"
```

### HTTPS

Voor productie gebruik altijd HTTPS:

1. Gebruik Let's Encrypt certificaten
2. Setup reverse proxy (nginx/Traefik)
3. Update `VITE_API_BASE_URL` naar HTTPS URL

## Troubleshooting

### Frontend kan geen verbinding maken met backend

**Symptomen:**
- "Failed to fetch" errors
- Geen response van backend

**Oplossingen:**

1. **Controleer backend URL:**
   ```bash
   # In src/frontend/.env
   cat .env
   # Moet correct NAS IP hebben
   ```

2. **Test backend direct:**
   ```bash
   curl http://NAS-IP:8000/
   ```

3. **Check CORS configuratie:**
   ```bash
   # In backend .env
   echo $CORS_ORIGINS
   # Moet frontend origin bevatten
   ```

4. **Check browser console:**
   - Open Developer Tools (F12)
   - Kijk naar Network tab
   - Check voor CORS errors

### CORS Errors

**Symptoom:**
```
Access to fetch at 'http://nas-ip:8000/chat' from origin 'http://localhost:5173'
has been blocked by CORS policy
```

**Oplossing:**

1. **Voeg frontend origin toe aan backend `.env`:**
   ```bash
   CORS_ORIGINS="http://localhost:5173,http://192.168.1.50:5173"
   ```

2. **Herstart backend:**
   ```bash
   docker-compose -f docker-compose.nas.yml restart
   ```

### Backend start niet

**Check logs:**
```bash
docker-compose -f docker-compose.nas.yml logs -f
```

**Veel voorkomende problemen:**

1. **Ontbrekende environment variabelen:**
   - Check `.env` bestand
   - Zorg dat alle verplichte velden zijn ingevuld

2. **Azure credentials:**
   - Test connection string
   - Check Azure permissions

3. **Port al in gebruik:**
   ```bash
   # Verander port in docker-compose.nas.yml
   ports:
     - "8001:8000"
   ```

### Trage Response

**Mogelijke oorzaken:**

1. **NAS heeft weinig resources:**
   - Check CPU/memory usage
   - Overweeg upgrade of dedicated server

2. **Azure AI endpoint is traag:**
   - Test direct met Azure SDK
   - Check Azure region latency

3. **Network latency:**
   - Gebruik lokaal netwerk in plaats van internet
   - Check WiFi vs Ethernet

### Development: Hot Reload werkt niet

Als je wijzigingen maakt maar niet ziet in de frontend:

```bash
# Stop development server
# Clear cache
rm -rf src/frontend/node_modules/.vite
rm -rf src/frontend/dist

# Rebuild
cd src/frontend
pnpm install
pnpm dev
```

## Monitoring

### Backend Logs

```bash
# Docker logs
docker-compose -f docker-compose.nas.yml logs -f

# Specifieke service
docker logs ai-chat-backend -f --tail 100
```

### Health Check

Maak een simpel monitoring script:

```bash
#!/bin/bash
# check-backend.sh

BACKEND_URL="http://192.168.1.100:8000"

if curl -f -s "$BACKEND_URL" > /dev/null; then
    echo "✅ Backend is UP"
else
    echo "❌ Backend is DOWN"
    # Optioneel: stuur notificatie
fi
```

Run periodiek via cron:
```bash
*/5 * * * * /path/to/check-backend.sh
```

## Performance Tips

### Backend

1. **Gebruik productie WSGI server:**
   - Uvicorn met workers: `--workers 4`
   - Gunicorn met uvicorn workers

2. **Enable caching:**
   - Redis voor session caching
   - Azure CDN voor static assets

3. **Resource limits:**
   ```yaml
   # In docker-compose.nas.yml
   services:
     backend:
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
   ```

### Frontend

1. **Enable compression:**
   - Gzip/Brotli op webserver
   - Verkleint transfer size

2. **CDN voor static assets:**
   - Host CSS/JS op CDN
   - Snellere load times

3. **Service Worker:**
   - Offline support
   - Caching strategie

## Gerelateerde Documentatie

- [Local Development Guide](./local_development.md)
- [Testing Guide](./testing.md)
- [Deployment Guide](./deployment.md)

## Veelgestelde Vragen

**Q: Kan ik de backend ook op een andere cloud platform draaien?**
A: Ja! De backend kan overal draaien waar Docker of Python beschikbaar is. Pas alleen de `VITE_API_BASE_URL` aan.

**Q: Moet ik beide services op hetzelfde netwerk hebben?**
A: Nee, maar dat is wel sneller. Je kunt de backend ook publiek beschikbaar maken met port forwarding.

**Q: Kan ik meerdere frontends met dezelfde backend gebruiken?**
A: Ja, voeg alle frontend URLs toe aan `CORS_ORIGINS` gescheiden door komma's.

**Q: Hoe update ik de backend?**
A: Pull de nieuwe code, rebuild de Docker image, en herstart de container:
```bash
docker-compose -f docker-compose.nas.yml down
docker-compose -f docker-compose.nas.yml build
docker-compose -f docker-compose.nas.yml up -d
```
