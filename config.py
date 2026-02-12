"""
Configuration for UniTune Music Link API
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Server
    PORT = int(os.getenv('PORT', 10000))
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    
    # Spotify API (Required)
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # YouTube API (Optional)
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
    
    # TIDAL API (Optional - for better metadata extraction)
    TIDAL_CLIENT_ID = os.getenv('TIDAL_CLIENT_ID')
    TIDAL_CLIENT_SECRET = os.getenv('TIDAL_CLIENT_SECRET')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'ERROR')
    
    # Cache
    CACHE_TTL = 86400  # 24 hours

    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///unitune_playlists.db')
    PLAYLIST_MAX_TRACKS = int(os.getenv('PLAYLIST_MAX_TRACKS', 500))
    PLAYLIST_TTL_DAYS = int(os.getenv('PLAYLIST_TTL_DAYS', 180))
    
    # Platform URLs
    PLATFORM_URLS = {
        'spotify': 'https://open.spotify.com',
        'appleMusic': 'https://music.apple.com',
        'youtubeMusic': 'https://music.youtube.com',
        'youtube': 'https://www.youtube.com',
        'deezer': 'https://www.deezer.com',
        'tidal': 'https://tidal.com',
        'amazonMusic': 'https://music.amazon.com'
    }
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.SPOTIFY_CLIENT_ID or not cls.SPOTIFY_CLIENT_SECRET:
            raise ValueError(
                "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET are required. "
                "Get them from https://developer.spotify.com/dashboard"
            )
        
        if not cls.YOUTUBE_API_KEY:
            print("⚠️  Warning: YOUTUBE_API_KEY not set. YouTube Music links will be limited.")
        
        if not cls.TIDAL_CLIENT_ID or not cls.TIDAL_CLIENT_SECRET:
            print("⚠️  Warning: TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET not set. Using public TIDAL API (less reliable).")
