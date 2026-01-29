# UniTune API Integration Guide

## Übersicht

Die UniTune API wurde erweitert, um UniTune-Share-Links zu verarbeiten und eine Landing-Page anzuzeigen.

## Neue Features

### 1. Share-Link-Endpoint: `/s/{encodedUrl}`

Dieser Endpoint verarbeitet UniTune-Share-Links, die von der App generiert werden.

**Format:** `https://your-api.com/s/{URL-encoded-music-link}`

**Beispiel:**
```
https://your-api.com/s/https%3A%2F%2Fopen.spotify.com%2Ftrack%2F3n3Ppam7vgaVa1iaRUc9Lp
```

#### Verhalten:

- **Browser-Anfrage** (HTML): Zeigt eine schöne Landing-Page mit:
  - Album-Cover
  - Song-Titel und Artist
  - Buttons für alle verfügbaren Plattformen (Spotify, Apple Music, YouTube Music, etc.)
  
- **API-Anfrage** (JSON): Gibt die gleichen Daten wie `/v1-alpha.1/links` zurück

#### Content-Type Detection:

Die API erkennt automatisch, ob es sich um eine Browser- oder API-Anfrage handelt:
- `Accept: text/html` → HTML Landing-Page
- `Accept: application/json` → JSON Response

### 2. Bestehender Endpoint: `/v1-alpha.1/links?url={musicUrl}`

Bleibt unverändert und kompatibel mit Odesli API.

## Workflow

### App → API Flow:

1. **User teilt Song in Spotify**
   ```
   spotify://track/3n3Ppam7vgaVa1iaRUc9Lp
   ```

2. **App empfängt Share Intent**
   - App ruft Odesli API auf (oder könnte UniTune API nutzen)
   - Erhält alle Plattform-Links

3. **App generiert UniTune-Link**
   ```dart
   String _generateShareLink(String originalMusicUrl) {
     final encodedUrl = Uri.encodeComponent(originalMusicUrl);
     return 'https://unitune.art/s/$encodedUrl';
   }
   ```
   
   Ergebnis: `https://unitune.art/s/https%3A%2F%2Fopen.spotify.com%2Ftrack%2F3n3Ppam7vgaVa1iaRUc9Lp`

4. **User teilt Link via WhatsApp/Telegram**

5. **Empfänger öffnet Link im Browser**
   - API dekodiert URL
   - Extrahiert Metadata von Original-Plattform
   - Sucht Song auf allen anderen Plattformen
   - Zeigt Landing-Page mit allen Links

### API → Plattformen Flow:

```
UniTune Link
    ↓
Dekodiere URL
    ↓
Parse Plattform & Track-ID
    ↓
Extrahiere Metadata (Spotify API / Deezer API / etc.)
    ↓
Suche auf anderen Plattformen
    ↓
Generiere Response (HTML oder JSON)
```

## Unterstützte Plattformen

### Als Input (Extrahieren):
- ✅ Spotify
- ✅ Deezer
- ✅ TIDAL
- ✅ YouTube / YouTube Music
- ❌ Apple Music (keine öffentliche API)
- ❌ Amazon Music (keine öffentliche API)

### Als Output (Suchen):
- ✅ Spotify
- ✅ Apple Music (via iTunes Search API)
- ✅ YouTube Music
- ✅ Deezer
- ✅ TIDAL
- ✅ Amazon Music (via Suche)

## Konfiguration

### Erforderliche API-Keys:

```env
# .env Datei
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
YOUTUBE_API_KEY=your_youtube_key  # Optional, aber empfohlen
```

### Ohne YouTube API Key:
- YouTube-Links als Input funktionieren nicht
- YouTube-Suche funktioniert weiterhin (generiert Suche-URLs)

## Deployment

### Option 1: Heroku
```bash
git push heroku main
```

### Option 2: Docker
```bash
docker build -t unitune-api .
docker run -p 5000:5000 --env-file .env unitune-api
```

### Option 3: Cloudflare Workers
Die Landing-Page-Logik kann auch im Cloudflare Worker implementiert werden (siehe `unitune/web/cloudflare-worker/`).

## App-Integration

### Aktuell (verwendet externe Odesli API):
```dart
// unitune/lib/data/repositories/odesli_repository.dart
static const String _baseUrl = 'https://api.song.link/v1-alpha.1/links';
```

### Zukünftig (eigene API nutzen):
```dart
static const String _baseUrl = 'https://your-api.com/v1-alpha.1/links';
```

## Testing

### Test Share-Link (Browser):
```bash
curl http://localhost:5000/s/https%3A%2F%2Fopen.spotify.com%2Ftrack%2F3n3Ppam7vgaVa1iaRUc9Lp
```

### Test API-Endpoint (JSON):
```bash
curl -H "Accept: application/json" \
  http://localhost:5000/s/https%3A%2F%2Fopen.spotify.com%2Ftrack%2F3n3Ppam7vgaVa1iaRUc9Lp
```

### Test Original-Endpoint:
```bash
curl "http://localhost:5000/v1-alpha.1/links?url=https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
```

## Nächste Schritte

1. **API deployen** (Heroku, Railway, Fly.io, etc.)
2. **Domain konfigurieren** (z.B. `api.unitune.art`)
3. **App anpassen** um eigene API zu nutzen statt Odesli
4. **Cloudflare Worker** als Proxy/Cache vor die API schalten (optional)

## Vorteile der eigenen API

- ✅ Keine Abhängigkeit von Odesli
- ✅ Volle Kontrolle über Features
- ✅ Eigene Landing-Page mit Branding
- ✅ Keine Rate-Limits von Drittanbietern
- ✅ Privacy: Keine Daten an Odesli
- ✅ Erweiterbar für zukünftige Features
