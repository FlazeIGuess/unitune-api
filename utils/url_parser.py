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
    
    # URL patterns for each platform with content type
    # Format: (pattern, content_type)
    PATTERNS = {
        'spotify': [
            (r'open\.spotify\.com/(?:intl-[a-z]+/)?track/([a-zA-Z0-9]+)(?:\?.*)?', ContentType.TRACK),
            (r'spotify:track:([a-zA-Z0-9]+)', ContentType.TRACK),
            (r'open\.spotify\.com/(?:intl-[a-z]+/)?album/([a-zA-Z0-9]+)(?:\?.*)?', ContentType.ALBUM),
            (r'spotify:album:([a-zA-Z0-9]+)', ContentType.ALBUM),
            (r'open\.spotify\.com/(?:intl-[a-z]+/)?artist/([a-zA-Z0-9]+)(?:\?.*)?', ContentType.ARTIST),
            (r'spotify:artist:([a-zA-Z0-9]+)', ContentType.ARTIST),
        ],
        'appleMusic': [
            (r'music\.apple\.com/.+/album/.+\?i=(\d+)', ContentType.TRACK),
            (r'music\.apple\.com/.+/song/.+/(\d+)', ContentType.TRACK),
            (r'music\.apple\.com/.+/album/[^/]+/(\d+)(?:\?.*)?$', ContentType.ALBUM),
            (r'music\.apple\.com/.+/artist/[^/]+/(\d+)(?:\?.*)?', ContentType.ARTIST),
        ],
        'youtube': [
            (r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', ContentType.TRACK),
            (r'youtu\.be/([a-zA-Z0-9_-]+)', ContentType.TRACK),
            (r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', ContentType.TRACK),
            (r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', ContentType.TRACK),
            (r'youtube\.com/channel/([a-zA-Z0-9_-]+)', ContentType.ARTIST),
            (r'youtube\.com/@([a-zA-Z0-9_-]+)', ContentType.ARTIST),
        ],
        'deezer': [
            (r'deezer\.com/(?:[a-z]{2}/)?track/(\d+)', ContentType.TRACK),
            (r'deezer\.page\.link/.*track[=/](\d+)', ContentType.TRACK),
            (r'deezer\.com/(?:[a-z]{2}/)?album/(\d+)', ContentType.ALBUM),
            (r'deezer\.page\.link/.*album[=/](\d+)', ContentType.ALBUM),
            (r'deezer\.com/(?:[a-z]{2}/)?artist/(\d+)', ContentType.ARTIST),
            (r'deezer\.page\.link/.*artist[=/](\d+)', ContentType.ARTIST),
        ],
        'tidal': [
            (r'tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?', ContentType.TRACK),
            (r'tidal\.com/browse/track/(\d+)', ContentType.TRACK),
            (r'listen\.tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?', ContentType.TRACK),
            (r'tidal\.com/browse/track/(\d+)/u', ContentType.TRACK),
            (r'tidal\.com/album/(\d+)(?:/[ua](?:Log)?)?', ContentType.ALBUM),
            (r'tidal\.com/browse/album/(\d+)', ContentType.ALBUM),
            (r'listen\.tidal\.com/album/(\d+)(?:/[ua](?:Log)?)?', ContentType.ALBUM),
            (r'tidal\.com/artist/(\d+)(?:/[ua](?:Log)?)?', ContentType.ARTIST),
            (r'tidal\.com/browse/artist/(\d+)', ContentType.ARTIST),
            (r'listen\.tidal\.com/artist/(\d+)(?:/[ua](?:Log)?)?', ContentType.ARTIST),
        ],
        'amazonMusic': [
            (r'music\.amazon\.com/tracks/([A-Z0-9]+)', ContentType.TRACK),
            (r'amazon\.com/music/player/tracks/([A-Z0-9]+)', ContentType.TRACK),
            (r'music\.amazon\.com/albums/([A-Z0-9]+)', ContentType.ALBUM),
            (r'amazon\.com/music/player/albums/([A-Z0-9]+)', ContentType.ALBUM),
            (r'music\.amazon\.com/artists/([A-Z0-9]+)', ContentType.ARTIST),
            (r'amazon\.com/music/player/artists/([A-Z0-9]+)', ContentType.ARTIST),
        ]
    }
    
    @classmethod
    def parse(cls, url: str) -> Optional[Tuple[str, str]]:
        """
        Parse music URL and extract platform + track ID (backward compatible)
        
        Args:
            url: Music URL from any supported platform
            
        Returns:
            Tuple of (platform, track_id) or None if not recognized
        """
        result = cls.parse_with_type(url)
        if result:
            platform, content_id, _ = result
            return (platform, content_id)
        return None
    
    @classmethod
    def parse_with_type(cls, url: str) -> Optional[Tuple[str, str, ContentType]]:
        """
        Parse music URL and extract platform + content ID + content type
        
        Args:
            url: Music URL from any supported platform
            
        Returns:
            Tuple of (platform, content_id, content_type) or None if not recognized
        """
        if not url:
            return None
        
        url = url.strip()
        
        for platform, patterns in cls.PATTERNS.items():
            for pattern_tuple in patterns:
                pattern, content_type = pattern_tuple
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    content_id = match.group(1)
                    return (platform, content_id, content_type)
        
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
