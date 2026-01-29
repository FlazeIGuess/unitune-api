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
            r'open\.spotify\.com/(?:intl-[a-z]+/)?track/([a-zA-Z0-9]+)',
            r'spotify:track:([a-zA-Z0-9]+)'
        ],
        'appleMusic': [
            r'music\.apple\.com/.+/album/.+\?i=(\d+)',
            r'music\.apple\.com/.+/song/.+/(\d+)'
        ],
        'youtube': [
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'
        ],
        'deezer': [
            r'deezer\.com/track/(\d+)',
            r'deezer\.com/.+/track/(\d+)'
        ],
        'tidal': [
            r'tidal\.com/track/(\d+)',
            r'tidal\.com/browse/track/(\d+)',
            r'listen\.tidal\.com/track/(\d+)'
        ],
        'amazonMusic': [
            r'music\.amazon\.com/.+/([A-Z0-9]+)',
            r'amazon\.com/music/player/([A-Z0-9]+)'
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
