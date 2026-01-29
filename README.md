# UniTune Music Link API

Self-hosted music link conversion API - Alternative to Odesli/SongLink.

## Features

- 🎵 Convert music links between platforms (Spotify, Apple Music, YouTube Music, Deezer, TIDAL, Amazon Music)
- 🚀 Fast and lightweight
- 🔒 Privacy-focused (no tracking, minimal logging)
- 🌍 GDPR compliant
- 🆓 Free and open source

## Supported Platforms

### Input (Source)
- Spotify
- TIDAL
- Deezer
- YouTube/YouTube Music

### Output (Target)
- Spotify
- Apple Music
- YouTube Music
- Deezer
- TIDAL
- Amazon Music

## Quick Start

### Prerequisites

- Python 3.11+
- Spotify API credentials ([Get here](https://developer.spotify.com/dashboard))
- YouTube API key (optional, [Get here](https://console.cloud.google.com))
- TIDAL API credentials (optional, [Get here](https://developer.tidal.com))

### Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/unitune-api.git
cd unitune-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Add your API credentials to `.env`:
```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
YOUTUBE_API_KEY=your_youtube_api_key
TIDAL_CLIENT_ID=your_tidal_client_id
TIDAL_CLIENT_SECRET=your_tidal_client_secret
```

5. Run the server:
```bash
python app.py
```

The API will be available at `http://localhost:10000`

## API Usage

### Convert a music link

```bash
GET /v1-alpha.1/links?url={MUSIC_URL}
```

**Example**:
```bash
curl "http://localhost:10000/v1-alpha.1/links?url=https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp"
```

**Response**:
```json
{
  "entityUniqueId": "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp",
  "userCountry": "US",
  "pageUrl": "https://unitune.art/s/https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
  "entitiesByUniqueId": {
    "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp": {
      "id": "3n3Ppam7vgaVa1iaRUc9Lp",
      "type": "song",
      "title": "Mr. Brightside",
      "artistName": "The Killers",
      "thumbnailUrl": "https://i.scdn.co/image/...",
      "apiProvider": "spotify",
      "platforms": ["spotify", "appleMusic", "youtubeMusic", "deezer", "tidal"]
    }
  },
  "linksByPlatform": {
    "spotify": {
      "url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
      "entityUniqueId": "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp"
    },
    "appleMusic": {
      "url": "https://music.apple.com/search?term=The+Killers+Mr.+Brightside",
      "entityUniqueId": "APPLEMUSIC::SONG::unknown"
    },
    "youtubeMusic": {
      "url": "https://music.youtube.com/watch?v=...",
      "entityUniqueId": "YOUTUBE::VIDEO::..."
    },
    "deezer": {
      "url": "https://www.deezer.com/track/2947340",
      "entityUniqueId": "DEEZER::TRACK::2947340"
    },
    "tidal": {
      "url": "https://listen.tidal.com/search?q=The%20Killers%20Mr.%20Brightside",
      "entityUniqueId": "TIDAL::TRACK::search"
    }
  }
}
```

### Health check

```bash
GET /health
```

**Response**:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "spotify_configured": true,
  "youtube_configured": true
}
```

## Deployment

### Deploy to Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your Git repository
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3

4. Add environment variables:
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

5. Deploy!

### Deploy to Heroku

```bash
heroku create your-app-name
heroku config:set SPOTIFY_CLIENT_ID=...
heroku config:set SPOTIFY_CLIENT_SECRET=...
heroku config:set YOUTUBE_API_KEY=...
git push heroku main
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│         Flask API Server            │
├─────────────────────────────────────┤
│  • URL Parser                       │
│  • Platform Extractors              │
│    - Spotify (Official API)         │
│    - TIDAL (Official API)           │
│    - Deezer (Public API)            │
│    - YouTube (Official API)         │
│  • Platform Searchers               │
│    - Apple Music (Search)           │
│    - Amazon Music (Search)          │
│    - YouTube Music (Search)         │
│    - Deezer (Search)                │
│    - TIDAL (Search)                 │
│  • Response Builder                 │
└─────────────────────────────────────┘
```

## TIDAL Integration Note

TIDAL API has access tier limitations. The current implementation uses search links instead of direct track links due to API restrictions. This provides a good user experience with one additional click.

For more details, see [TIDAL_API_SETUP.md](TIDAL_API_SETUP.md)

## Privacy & GDPR

- ✅ No user tracking
- ✅ No personal data storage
- ✅ Minimal logging (errors only)
- ✅ No cookies
- ✅ No analytics

## License

MIT License - See [LICENSE](LICENSE) file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

- 📧 Email: support@unitune.art
- 🐛 Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/unitune-api/issues)

## Related Projects

- [UniTune App](https://github.com/YOUR_USERNAME/unitune) - Flutter mobile app
- [UniTune Worker](https://github.com/YOUR_USERNAME/unitune-worker) - Cloudflare Worker for web interface

---

Made with ❤️ for music lovers
