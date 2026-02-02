"""
URL Parser - Extract platform and track ID from music URLs
"""
import re
from typing import Optional, Tuple

class URLParser:
    """Parse music URLs to extract platform and track ID"""
    
    # URL patterns for each platform
    PATTERNS = {
        'spotify': [
            r'open\.spotify\.com/(?:intl-[a-z]+/)?track/([a-zA-Z0-9]+)(?:\?.*)?',  # Ignore query params
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
            r'youtube\.com/shorts/([a-zA-Z0-9_-]+)'  # Support YouTube Shorts
        ],
        'deezer': [
            r'deezer\.com/(?:[a-z]{2}/)?track/(\d+)',  # Support country codes
            r'deezer\.page\.link/.*track[=/](\d+)'  # Support deep links
        ],
        'tidal': [
            r'tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?',  # Matches /track/123, /track/123/u, /track/123/uLog
            r'tidal\.com/browse/track/(\d+)',
            r'listen\.tidal\.com/track/(\d+)(?:/[ua](?:Log)?)?',
            r'tidal\.com/browse/track/(\d+)/u'  # Explicit /u support
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
        
        # Clean URL
        url = url.strip()
        
        # Try each platform's patterns
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
