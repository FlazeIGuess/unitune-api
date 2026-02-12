"""
URL Parser - Extract platform and track ID from music URLs
"""
import re
from typing import Optional, Tuple
from enum import Enum

class ContentType(Enum):
    """Type of music content"""
    TRACK = "track"
    ALBUM = "album"
    ARTIST = "artist"
    PLAYLIST = "playlist"
    UNKNOWN = "unknown"

class URLParser:
    """Parse music URLs to extract platform and track ID"""
    
    # URL patterns for each platform
    PATTERNS = {
        'spotify': [
            r'open\.spotify\.com/(?:intl-[a-z]+/)?track/([a-zA-Z0-9]+)(?:\?.*)?',
            r'spotify:track:([a-zA-Z0-9]+)'
        ],
        'appleMusic': [
            r'music\.apple\.com/.+/album/.+\?i=(\d+)',
            r'music\.apple\.com/.+/song/.+/(\d+)'
        ],
        'youtube': [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtube\.com/shorts/([a-zA-Z0-9_-]+)'
        ],
        'deezer': [
            r'deezer\.com/(?:[a-z]{2}/)?track/(\d+)',
            r'deezer\.page\.link/.*track[=/](\d+)'
        ],
        'tidal': [
            r'tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?',
            r'tidal\.com/browse/track/(\d+)',
            r'listen\.tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?',
            r'tidal\.com/browse/track/(\d+)/u'
        ],
        'amazonMusic': [
            r'music\.amazon\.com/albums/([A-Z0-9]+)',
            r'music\.amazon\.com/tracks/([A-Z0-9]+)',
            r'amazon\.com/music/player/albums/([A-Z0-9]+)',
            r'amazon\.com/music/player/tracks/([A-Z0-9]+)'
        ]
    }
    
    @classmethod
    def parse(cls, url: str) -> Optional[Tuple[str, str]]:
        """
        Parse music URL and extract platform + track ID
        
        Args:
            url: Music URL from any supported platform
            
        Returns:
            Tuple of (platform, track_id) or None if not recognized
        """
        if not url:
            return None
        
        url = url.strip()
        
        for platform, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    track_id = match.group(1)
                    return (platform, track_id)
        
        return None
    
    @classmethod
    def is_valid_url(cls, url: str) -> bool:
        """Check if URL is from a supported platform"""
        return cls.parse(url) is not None
    
    @classmethod
    def detect_content_type(cls, url: str) -> ContentType:
        """
        Detect if URL is track, album, artist, or playlist
        
        Args:
            url: Music URL from any supported platform
            
        Returns:
            ContentType enum value
        """
        if not url:
            return ContentType.UNKNOWN
        
        url_lower = url.lower()
        
        # Spotify
        if 'spotify.com' in url_lower:
            if '/track/' in url_lower:
                return ContentType.TRACK
            elif '/album/' in url_lower:
                return ContentType.ALBUM
            elif '/artist/' in url_lower:
                return ContentType.ARTIST
            elif '/playlist/' in url_lower:
                return ContentType.PLAYLIST
        
        # Apple Music
        if 'music.apple.com' in url_lower:
            if '/song/' in url_lower:
                return ContentType.TRACK
            elif '/album/' in url_lower:
                return ContentType.ALBUM
            elif '/artist/' in url_lower:
                return ContentType.ARTIST
            elif '/playlist/' in url_lower:
                return ContentType.PLAYLIST
        
        # Tidal
        if 'tidal.com' in url_lower or 'listen.tidal.com' in url_lower:
            if '/track/' in url_lower:
                return ContentType.TRACK
            elif '/album/' in url_lower:
                return ContentType.ALBUM
            elif '/artist/' in url_lower:
                return ContentType.ARTIST
            elif '/playlist/' in url_lower:
                return ContentType.PLAYLIST
        
        # YouTube (always track/video)
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return ContentType.TRACK
        
        # Deezer
        if 'deezer.com' in url_lower:
            if '/track/' in url_lower:
                return ContentType.TRACK
            elif '/album/' in url_lower:
                return ContentType.ALBUM
            elif '/artist/' in url_lower:
                return ContentType.ARTIST
            elif '/playlist/' in url_lower:
                return ContentType.PLAYLIST
        
        # Amazon Music
        if 'music.amazon' in url_lower or 'amazon.com/music' in url_lower:
            if '/tracks/' in url_lower:
                return ContentType.TRACK
            elif '/albums/' in url_lower:
                return ContentType.ALBUM
            elif '/artists/' in url_lower:
                return ContentType.ARTIST
            elif '/playlists/' in url_lower:
                return ContentType.PLAYLIST
        
        # Default to track for backward compatibility
        return ContentType.TRACK
