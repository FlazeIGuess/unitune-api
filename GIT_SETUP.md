# Git Repository Setup - UniTune API

## ✅ Git Repository erstellt!

Das lokale Git Repository wurde erfolgreich initialisiert mit:
- ✅ 23 Dateien committed
- ✅ `.env` wird NICHT committed (in .gitignore)
- ✅ Test-Dateien werden NICHT committed (in .gitignore)
- ✅ README.md erstellt
- ✅ LICENSE erstellt (MIT)

## 🚀 Auf GitHub hochladen

### Schritt 1: GitHub Repository erstellen

1. Gehe zu https://github.com/new
2. **Repository Name**: `unitune-api`
3. **Description**: `Self-hosted music link conversion API - Alternative to Odesli/SongLink`
4. **Visibility**: 
   - ✅ **Public** (empfohlen für Open Source)
   - ⚠️ **Private** (wenn du API Keys schützen willst)
5. **NICHT** "Initialize with README" anklicken (haben wir schon)
6. Klicke **"Create repository"**

### Schritt 2: Remote hinzufügen

Kopiere die Commands von GitHub (werden nach Repository-Erstellung angezeigt):

```bash
cd unitune-api
git remote add origin https://github.com/DEIN_USERNAME/unitune-api.git
git branch -M main
git push -u origin main
```

**Oder mit SSH** (wenn du SSH Keys hast):
```bash
git remote add origin git@github.com:DEIN_USERNAME/unitune-api.git
git branch -M main
git push -u origin main
```

### Schritt 3: Verifizieren

Gehe zu `https://github.com/DEIN_USERNAME/unitune-api` und prüfe:
- ✅ Alle Dateien sind da
- ✅ `.env` ist NICHT da
- ✅ Test-Dateien sind NICHT da
- ✅ README wird angezeigt

## 📋 Was ist im Repository?

### ✅ Committed (im Git)
```
.env.example          # Template für Environment Variables
.gitignore           # Git Ignore Rules
INTEGRATION.md       # Integration Dokumentation
LICENSE              # MIT License
Procfile             # Heroku/Render Deployment
README.md            # Hauptdokumentation
app.py               # Flask API Server
config.py            # Configuration
requirements.txt     # Python Dependencies
runtime.txt          # Python Version
extractors/          # Platform Extractors (Spotify, TIDAL, etc.)
searchers/           # Platform Searchers
utils/               # Helper Functions
```

### ❌ NICHT Committed (lokal only)
```
.env                 # Deine API Keys (GEHEIM!)
.cache               # Cache Dateien
__pycache__/         # Python Cache
test_*.py            # Test Scripts
debug_*.py           # Debug Scripts
```

## 🔐 Sicherheit

### ✅ Sicher
- `.env` ist in `.gitignore` → wird NICHT hochgeladen
- API Keys bleiben lokal
- Nur Code wird geteilt

### ⚠️ Wichtig
**NIEMALS** diese Dateien committen:
- `.env`
- API Keys
- Secrets
- Passwords

## 🚀 Deployment auf Render

Nach dem GitHub Push:

1. Gehe zu https://dashboard.render.com
2. **New** → **Web Service**
3. **Connect Repository**: Wähle `unitune-api`
4. **Settings**:
   - Name: `unitune-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
5. **Environment Variables** hinzufügen:
   ```
   SPOTIFY_CLIENT_ID=...
   SPOTIFY_CLIENT_SECRET=...
   YOUTUBE_API_KEY=...
   TIDAL_CLIENT_ID=...
   TIDAL_CLIENT_SECRET=...
   PORT=10000
   FLASK_ENV=production
   LOG_LEVEL=ERROR
   ```
6. **Create Web Service**

## 📝 Zukünftige Updates

Wenn du Änderungen machst:

```bash
cd unitune-api
git add .
git commit -m "Beschreibung der Änderungen"
git push
```

Render deployed automatisch nach jedem Push!

## 🆘 Troubleshooting

### Problem: `.env` wurde committed

**Lösung**:
```bash
git rm --cached .env
git commit -m "Remove .env from git"
git push
```

Dann ändere SOFORT alle API Keys!

### Problem: Remote already exists

**Lösung**:
```bash
git remote remove origin
git remote add origin https://github.com/DEIN_USERNAME/unitune-api.git
```

### Problem: Authentication failed

**Lösung**: 
- Nutze GitHub Personal Access Token statt Passwort
- Oder nutze SSH Keys

## ✅ Checklist

Vor dem Push:
- [ ] `.env` ist in `.gitignore`
- [ ] Keine API Keys im Code
- [ ] README.md ist aktuell
- [ ] LICENSE ist vorhanden

Nach dem Push:
- [ ] Repository ist auf GitHub sichtbar
- [ ] `.env` ist NICHT auf GitHub
- [ ] README wird korrekt angezeigt
- [ ] Render Deployment funktioniert

---

**Bereit zum Hochladen!** 🚀
