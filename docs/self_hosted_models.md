# Zelf-Gehoste Modellen Gebruiken

Deze gids legt uit hoe je je eigen LLM modellen kunt gebruiken in plaats van Azure OpenAI. Perfect voor als je modellen op je NAS wilt draaien!

## Inhoudsopgave
- [Ondersteunde Model Servers](#ondersteunde-model-servers)
- [Ollama (Aanbevolen)](#ollama-aanbevolen)
- [LocalAI](#localai)
- [LM Studio](#lm-studio)
- [vLLM](#vllm)
- [text-generation-webui](#text-generation-webui)
- [Backend Configureren](#backend-configureren)
- [Frontend Configureren](#frontend-configureren)
- [Troubleshooting](#troubleshooting)

## Ondersteunde Model Servers

De applicatie ondersteunt elke OpenAI-compatible API, inclusief:

| Server | Licentie | Beste voor | Link |
|--------|----------|------------|------|
| **Ollama** | MIT | Makkelijkste setup, beste UX | [ollama.com](https://ollama.com/) |
| **LocalAI** | MIT | Features, flexibiliteit | [localai.io](https://localai.io/) |
| **LM Studio** | Proprietary | Desktop GUI | [lmstudio.ai](https://lmstudio.ai/) |
| **vLLM** | Apache 2.0 | Performance, productie | [github.com/vllm-project](https://github.com/vllm-project/vllm) |
| **text-generation-webui** | AGPL | Web UI, tweaking | [github.com/oobabooga](https://github.com/oobabooga/text-generation-webui) |

## Ollama (Aanbevolen)

Ollama is de makkelijkste manier om modellen lokaal te draaien.

### Installatie

**MacOS/Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:**
Download van [ollama.com/download](https://ollama.com/download)

**Docker (voor NAS):**
```bash
docker run -d \
  --name ollama \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --restart unless-stopped \
  ollama/ollama
```

**Synology NAS:**
1. Open Docker package
2. Registry → Zoek "ollama"
3. Download "ollama/ollama"
4. Image → Launch
5. Port settings: 11434:11434
6. Volume: Mount folder voor models
7. Auto-restart: Aan

### Models Downloaden

```bash
# Download een model (bijv. Llama 3.2)
ollama pull llama3.2

# Of een kleiner model
ollama pull phi3

# Lijst van beschikbare modellen
ollama list
```

**Populaire modellen:**
- `llama3.2` - Meta's nieuwste (3B/1B parameters)
- `mistral` - Geweldig allround model (7B)
- `phi3` - Microsoft's kleine maar krachtige model (3.8B)
- `codellama` - Gespecialiseerd in code (7B/13B/34B)
- `neural-chat` - Finetuned voor conversaties (7B)

Meer modellen: [ollama.com/library](https://ollama.com/library)

### Test Ollama

```bash
# Test of Ollama werkt
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Backend Configureren voor Ollama

Maak `.env` in `src/` directory:

```bash
# Model provider
MODEL_PROVIDER="local"

# Ollama configuratie
MODEL_BASE_URL="http://localhost:11434"
MODEL_NAME="llama3.2"
MODEL_API_KEY="not-needed"

# CORS (pas aan voor je frontend)
CORS_ORIGINS="http://localhost:5173"
```

**Voor Ollama op NAS (van een andere machine):**
```bash
MODEL_BASE_URL="http://192.168.1.100:11434"  # Vervang met NAS IP
```

## LocalAI

LocalAI is een self-hosted OpenAI-compatible API server.

### Installatie met Docker

```bash
docker run -d \
  --name localai \
  -p 8080:8080 \
  -v $PWD/models:/models \
  -v $PWD/images:/tmp/generated/images \
  --restart unless-stopped \
  quay.io/go-skynet/local-ai:latest
```

### Models Installeren

LocalAI gebruikt GGUF models. Download van Hugging Face:

```bash
# Maak models directory
mkdir -p models

# Download een model (bijv. Llama 2)
cd models
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf

# Maak config file
cat > llama-2-7b-chat.yaml <<EOF
name: llama-2-7b-chat
parameters:
  model: llama-2-7b-chat.Q4_K_M.gguf
  temperature: 0.7
  top_p: 0.9
EOF
```

### Backend Configureren

```bash
MODEL_PROVIDER="local"
MODEL_BASE_URL="http://localhost:8080"
MODEL_NAME="llama-2-7b-chat"
MODEL_API_KEY="not-needed"
CORS_ORIGINS="http://localhost:5173"
```

## LM Studio

LM Studio heeft een mooie desktop GUI voor model management.

### Setup

1. Download LM Studio van [lmstudio.ai](https://lmstudio.ai/)
2. Install en open de app
3. **Search** tab: Zoek en download een model
4. **Chat** tab: Test je model
5. **Local Server** tab:
   - Selecteer je model
   - Click "Start Server"
   - Noteer de port (meestal 1234)

### Backend Configureren

```bash
MODEL_PROVIDER="local"
MODEL_BASE_URL="http://localhost:1234"
MODEL_NAME="llama-3.2-3b-instruct"  # Gebruik de model naam uit LM Studio
MODEL_API_KEY="not-needed"
CORS_ORIGINS="http://localhost:5173"
```

## vLLM

vLLM is de snelste inference engine, ideaal voor productie.

### Installatie

```bash
pip install vllm
```

### Start vLLM Server

```bash
# Download een model (gebruikt Hugging Face)
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.2-3B-Instruct \
  --port 8000
```

**Docker:**
```bash
docker run -d \
  --name vllm \
  --gpus all \
  -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3.2-3B-Instruct
```

### Backend Configureren

```bash
MODEL_PROVIDER="local"
MODEL_BASE_URL="http://localhost:8000"
MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
MODEL_API_KEY="not-needed"
CORS_ORIGINS="http://localhost:5173"
```

## text-generation-webui

Ook bekend als "oobabooga", heeft een web UI voor advanced tweaking.

### Installatie

```bash
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui
./start_linux.sh  # of start_windows.bat, start_macos.sh
```

### Models Downloaden

Via de web UI (http://localhost:7860):
1. Ga naar "Model" tab
2. Download een model van Hugging Face
3. Load het model

### OpenAI API Extension Enable

1. Ga naar "Session" tab → "Extensions"
2. Enable "openai"
3. Restart de server met `--extensions openai` flag:

```bash
python server.py --extensions openai --listen --api
```

### Backend Configureren

```bash
MODEL_PROVIDER="local"
MODEL_BASE_URL="http://localhost:5000"
MODEL_NAME="your-model-name"
MODEL_API_KEY="not-needed"
CORS_ORIGINS="http://localhost:5173"
```

## Backend Configureren

### Stap 1: Kies je Environment File

Kopieer het juiste template:

```bash
cd src/
cp .env.local-model .env
```

### Stap 2: Edit Configuration

Edit `.env`:

```bash
# Model provider
MODEL_PROVIDER="local"

# Je model server (pas aan voor jouw setup)
MODEL_BASE_URL="http://localhost:11434"  # Ollama
# MODEL_BASE_URL="http://localhost:8080"   # LocalAI
# MODEL_BASE_URL="http://localhost:1234"   # LM Studio
# MODEL_BASE_URL="http://localhost:8000"   # vLLM

# Model naam
MODEL_NAME="llama3.2"

# CORS (vervang met je frontend URL)
CORS_ORIGINS="http://localhost:5173"
```

### Stap 3: Start Backend

**Zonder Docker:**
```bash
cd src/
python -m uvicorn api.main:create_app --factory --host 0.0.0.0 --port 8000
```

**Met Docker:**
```bash
# Build image
docker build -f Dockerfile.nas-backend -t ai-chat-backend .

# Run container
docker run -d \
  --name ai-chat-backend \
  -p 8000:8000 \
  --env-file src/.env \
  --network host \
  ai-chat-backend
```

**Met Docker Compose:**
```bash
docker-compose -f docker-compose.nas.yml up -d
```

### Stap 4: Test Backend

```bash
curl http://localhost:8000/
```

Je zou de homepage moeten zien!

## Frontend Configureren

### Optie 1: Development Server

```bash
cd src/frontend

# Maak .env
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start server
pnpm install
pnpm dev
```

Frontend draait nu op `http://localhost:5173`!

### Optie 2: Production Build

```bash
cd src/frontend

# Configureer backend URL
echo "VITE_API_BASE_URL=http://NAS-IP:8000" > .env

# Build
pnpm build

# Deploy (optioneel)
# Build output is in ../api/static/react/
```

## Model op NAS, Frontend Lokaal

Perfect setup voor development:

### 1. Start Model Server op NAS

**Ollama via Docker (op NAS):**
```bash
docker run -d \
  --name ollama \
  -v /volume1/docker/ollama:/root/.ollama \
  -p 11434:11434 \
  --restart unless-stopped \
  ollama/ollama

# Download model
docker exec ollama ollama pull llama3.2
```

### 2. Start Backend op NAS

```bash
# Op je NAS
cd /volume1/docker/ai-chat-backend
docker-compose up -d
```

Edit `src/.env` op NAS:
```bash
MODEL_PROVIDER="local"
MODEL_BASE_URL="http://localhost:11434"  # Ollama op dezelfde NAS
MODEL_NAME="llama3.2"
CORS_ORIGINS="http://192.168.1.50:5173"  # Je lokale machine IP
```

### 3. Start Frontend Lokaal

```bash
# Op je lokale machine
cd src/frontend

echo "VITE_API_BASE_URL=http://192.168.1.100:8000" > .env  # NAS IP

pnpm dev
```

Open `http://localhost:5173` en je praat met je eigen model op de NAS! 🎉

## Troubleshooting

### Model Server Errors

**"Connection refused":**
```bash
# Check of server draait
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8080/v1/models  # LocalAI/vLLM

# Check Docker logs
docker logs ollama
docker logs localai
```

**"Model not found":**
```bash
# Ollama - lijst modellen
ollama list

# Download model
ollama pull llama3.2

# LocalAI - check models directory
ls models/
```

### Backend Connection Errors

**"Model provider not initialized":**
- Check `.env` file heeft correcte `MODEL_PROVIDER`
- Check `MODEL_BASE_URL` is correct
- Restart backend

**CORS errors:**
```bash
# Voeg frontend origin toe aan .env
CORS_ORIGINS="http://localhost:5173,http://192.168.1.50:5173"

# Restart backend
docker-compose restart
```

### Performance Issues

**Slow responses:**
1. **Use smaller model:**
   ```bash
   # Instead of 70B parameter model
   ollama pull llama3.2:1b  # Veel sneller!
   ```

2. **Check CPU/RAM:**
   ```bash
   # Models hebben memory nodig:
   # 1B parameters  ~1-2GB RAM
   # 3B parameters  ~3-4GB RAM
   # 7B parameters  ~7-8GB RAM
   # 13B parameters ~13-16GB RAM
   ```

3. **GPU acceleration (if available):**
   ```bash
   # Ollama gebruikt automatisch GPU als beschikbaar
   # Check met:
   ollama ps
   ```

**Model loading slow:**
- Models worden in memory geladen bij eerste request
- Duurt 10-30 seconden afhankelijk van model size
- Daarna zijn responses snel

### Network Issues

**Can't connect to NAS from another machine:**

1. **Firewall check:**
   ```bash
   # Test connectivity
   telnet NAS-IP 8000
   telnet NAS-IP 11434
   ```

2. **Docker network mode:**
   ```yaml
   # In docker-compose.nas.yml gebruik host network
   services:
     backend:
       network_mode: host
   ```

3. **Model server binding:**
   ```bash
   # Ollama moet luisteren op 0.0.0.0
   docker run -d \
     -e OLLAMA_HOST=0.0.0.0:11434 \
     ...
   ```

## Model Aanbevelingen

### Voor Chat (Algemeen)

| Model | Size | RAM | Kwaliteit | Speed |
|-------|------|-----|-----------|-------|
| phi3 | 3.8B | ~4GB | ⭐⭐⭐⭐ | ⚡⚡⚡⚡ |
| llama3.2 | 3B | ~3GB | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ |
| mistral | 7B | ~8GB | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| llama3.1 | 8B | ~9GB | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |

### Voor Code

| Model | Size | RAM | Kwaliteit | Speed |
|-------|------|-----|-----------|-------|
| codellama:7b | 7B | ~8GB | ⭐⭐⭐⭐ | ⚡⚡⚡ |
| deepseek-coder | 6.7B | ~7GB | ⭐⭐⭐⭐⭐ | ⚡⚡⚡ |
| starcoder2 | 3B | ~4GB | ⭐⭐⭐ | ⚡⚡⚡⚡ |

### Voor NAS (Limited Resources)

Als je NAS beperkte resources heeft:

```bash
# Kleinste goede modellen
ollama pull llama3.2:1b    # 1B - ~1GB RAM
ollama pull phi3:mini      # 3.8B - ~4GB RAM
ollama pull tinyllama      # 1.1B - ~1GB RAM
```

## Gerelateerde Documentatie

- [Separated Deployment Guide](./separated_deployment.md)
- [Local Development Guide](./local_development.md)
- [Testing Guide](./testing.md)

## Tips & Best Practices

1. **Start klein** - Begin met een klein model (1-3B) om te testen
2. **Monitor resources** - Hou RAM/CPU gebruik in de gaten
3. **Quantized models** - Gebruik Q4 of Q5 quantization voor betere performance
4. **Cache warming** - Eerste request is traag (model loading), daarna snel
5. **Update models** - Models worden constant verbeterd, check regelmatig voor updates

## Vragen?

**Q: Kan ik meerdere modellen tegelijk gebruiken?**
A: Ja! Start meerdere Ollama instances op verschillende ports, of gebruik LM Studio's model switching.

**Q: Kan ik switchen tussen Azure en local?**
A: Ja! Verander gewoon `MODEL_PROVIDER` in `.env` en restart de backend.

**Q: Zijn mijn chats privé met lokale modellen?**
A: Ja! Alles draait lokaal, geen data gaat naar cloud.

**Q: Kan ik GPU gebruiken?**
A: Ja! Ollama, vLLM en andere servers ondersteunen NVIDIA GPU's automatisch.
