# UniTune API

Backend API service for converting music links between different streaming platforms. Built with Flask and Python.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0.0-000000?logo=flask)](https://flask.palletsprojects.com)

## Overview

UniTune API provides music link conversion services, extracting metadata from various streaming platforms and generating universal links. The API supports Spotify, Apple Music, YouTube Music, Deezer, TIDAL, and Amazon Music.

## Features

- **Multi-Platform Support**: Extract metadata from 6 major music streaming services
- **Intelligent Fallback**: Multiple extraction strategies (API, web scraping)
- **Secure Share Links**: Base64-encoded links prevent phishing warnings (see [LINK_FORMAT_MIGRATION.md](LINK_FORMAT_MIGRATION.md))
- **Backward Compatible**: Supports both new and legacy link formats
- **Caching**: Reduces API calls and improves response times
- **CORS Enabled**: Ready for web and mobile clients
- **RESTful Design**: Clean and predictable API endpoints

## Supported Platforms

- Spotify (via official API)
- Apple Music (via web scraping)
- YouTube Music (via YouTube Data API)
- Deezer (via web scraping)
- TIDAL (via official API)
- Amazon Music (via web scraping)

## API Endpoints

### Convert Music Link

```http
GET /v1-alpha.1/links?url={music_url}
```

**Parameters:**
- `url` (required): Music link from any supported platform

**Response:**
```json
{
  "entityUniqueId": "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp",
  "userCountry": "US",
  "pageUrl": "https://unitune.art/s/c3BvdGlmeTp0cmFjazozbjNQcGFtN3ZnYVZhMWlhUlVjOUxw",
  "linksByPlatform": {
    "spotify": {
      "url": "https://open.spotify.com/track/...",
      "nativeAppUriMobile": "spotify:track:..."
    },
    "appleMusic": {
      "url": "https://music.apple.com/...",
      "nativeAppUriMobile": "music://..."
    }
  },
  "entitiesByUniqueId": {
    "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp": {
      "id": "3n3Ppam7vgaVa1iaRUc9Lp",
      "type": "song",
      "title": "Song Title",
      "artistName": "Artist Name",
      "thumbnailUrl": "https://...",
      "thumbnailWidth": 640,
      "thumbnailHeight": 640,
      "apiProvider": "spotify"
    }
  }
}
```

### Share Link Endpoint

```http
GET /s/{encoded_id}
```

**Supports two formats:**
- **New format** (Base64): `/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw` (recommended)
- **Legacy format** (URL-encoded): `/s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410` (backward compatible)

**Note:** New format prevents browser phishing warnings. See [LINK_FORMAT_MIGRATION.md](LINK_FORMAT_MIGRATION.md) for details.

## Installation

### Requirements
- Python 3.12 or higher
- pip (Python package manager)

### Setup

```bash
# Clone the repository
git clone https://github.com/FlazeIGuess/unitune-api.git
cd unitune-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables

Create a `.env` file with the following variables:

```env
# Spotify API (Required)
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

# YouTube Data API v3 (Optional but recommended)
YOUTUBE_API_KEY=your_youtube_api_key

# TIDAL API (Optional)
TIDAL_CLIENT_ID=your_tidal_client_id
TIDAL_CLIENT_SECRET=your_tidal_client_secret

# Server Configuration
PORT=10000
FLASK_ENV=production
LOG_LEVEL=ERROR
```

### API Keys

- **Spotify**: Get from [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
- **YouTube**: Get from [Google Cloud Console](https://console.cloud.google.com)
- **TIDAL**: Get from [TIDAL Developer Portal](https://developer.tidal.com/dashboard)

## Running

### Development

```bash
python app.py
```

The API will be available at `http://localhost:10000`

### Production

```bash
gunicorn app:app --bind 0.0.0.0:10000 --workers 4
```

## Deployment

### Heroku

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set SPOTIFY_CLIENT_ID=...
heroku config:set SPOTIFY_CLIENT_SECRET=...
heroku config:set YOUTUBE_API_KEY=...

# Deploy
git push heroku main
```

### Render

1. Create new Web Service on [Render](https://render.com)
2. Connect your GitHub repository
3. Set environment variables in Render dashboard
4. Deploy

### Docker

```bash
# Build image
docker build -t unitune-api .

# Run container
docker run -p 10000:10000 --env-file .env unitune-api
```

## Architecture

```
unitune-api/
├── app.py                 # Flask application entry point
├── config.py              # Configuration management
├── extractors/            # Platform-specific metadata extractors
│   ├── spotify.py
│   ├── tidal.py
│   ├── universal.py
│   └── web_scraper.py
├── searchers/             # Platform search implementations
│   ├── amazon_music.py
│   ├── apple_music.py
│   ├── deezer.py
│   ├── tidal.py
│   └── youtube.py
└── utils/                 # Utility functions
    ├── link_encoder.py    # Share link encoding/decoding
    ├── response_builder.py
    └── url_parser.py
```

## Dependencies

- **Flask 3.0.0**: Web framework
- **Flask-CORS 4.0.0**: Cross-origin resource sharing
- **Requests 2.31.0**: HTTP library
- **Spotipy 2.23.0**: Spotify API wrapper
- **google-api-python-client 2.108.0**: YouTube API client
- **BeautifulSoup4 4.12.3**: Web scraping
- **Gunicorn 21.2.0**: WSGI HTTP server

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## Rate Limiting

The API implements basic rate limiting:
- Caching reduces redundant API calls
- Spotify and YouTube APIs have their own rate limits
- Consider implementing Redis-based rate limiting for production

## Error Handling

The API returns standard HTTP status codes:
- `200 OK`: Successful request
- `400 Bad Request`: Invalid or missing URL parameter
- `404 Not Found`: Song not found on any platform
- `500 Internal Server Error`: Server error

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) before submitting pull requests.

## Related Projects

- [unitune](https://github.com/FlazeIGuess/unitune) - Flutter mobile application
- [unitune-worker](https://github.com/FlazeIGuess/unitune-worker) - Cloudflare Worker for web interface

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

See [LICENSE](LICENSE) for details.

### Attribution Requirement
Any use, modification, or distribution of this software must include proper attribution to the original author and project.

## Support

- **Issues**: [GitHub Issues](https://github.com/FlazeIGuess/unitune-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/FlazeIGuess/unitune-api/discussions)

---

Built with Flask and Python
