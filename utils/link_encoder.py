"""
Link Encoder/Decoder - Convert between music URLs and safe share links
Prevents phishing warnings by encoding platform/track info instead of full URLs
"""
import base64
import re
from typing import Optional, Tuple
from urllib.parse import unquote


class LinkEncoder:
    """Encode and decode UniTune share links"""
    
    @staticmethod
    def encode(platform: str, track_id: str, link_type: str = 'track') -> str:
        """
        Encode platform and track ID into a safe share link identifier
        
        Args:
            platform: Platform name (spotify, tidal, appleMusic, etc.)
            track_id: Track/song ID from the platform
            link_type: Type of content (track, album, playlist)
            
        Returns:
            Base64-encoded identifier safe for URLs
            
        Example:
            encode('tidal', '258735410', 'track') -> 'dGlkYWw6dHJhY2s6MjU4NzM1NDEw'
        """
        # Create identifier string: platform:type:id
        identifier = f"{platform}:{link_type}:{track_id}"
        
        # Encode to base64 (URL-safe variant)
        encoded_bytes = base64.urlsafe_b64encode(identifier.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')
        
        # Remove padding (= characters) for cleaner URLs
        return encoded_str.rstrip('=')
    
    @staticmethod
    def decode(encoded_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Decode a share link identifier back to platform and track ID
        
        Args:
            encoded_id: Base64-encoded identifier
            
        Returns:
            Tuple of (platform, link_type, track_id) or None if invalid
            
        Example:
            decode('dGlkYWw6dHJhY2s6MjU4NzM1NDEw') -> ('tidal', 'track', '258735410')
        """
        try:
            # Add padding back if needed
            padding = 4 - (len(encoded_id) % 4)
            if padding != 4:
                encoded_id += '=' * padding
            
            # Decode from base64
            decoded_bytes = base64.urlsafe_b64decode(encoded_id.encode('utf-8'))
            identifier = decoded_bytes.decode('utf-8')
            
            # Parse identifier: platform:type:id
            parts = identifier.split(':')
            if len(parts) != 3:
                return None
            
            platform, link_type, track_id = parts
            return (platform, link_type, track_id)
            
        except Exception:
            return None
    
    @staticmethod
    def is_legacy_format(path: str) -> bool:
        """
        Check if a share link uses the old URL-encoded format
        
        Args:
            path: The path part after /s/
            
        Returns:
            True if it's a legacy format (contains URL-encoded URL)
        """
        # Legacy format contains URL patterns like http:// or https://
        # even when URL-encoded (%3A%2F%2F or ://)
        return bool(re.search(r'(https?%3A%2F%2F|https?://)', path, re.IGNORECASE))
    
    @staticmethod
    def decode_legacy(encoded_url: str) -> Optional[str]:
        """
        Decode legacy URL-encoded share links for backward compatibility
        
        Args:
            encoded_url: URL-encoded music URL
            
        Returns:
            Decoded music URL or None if invalid
            
        Example:
            decode_legacy('https%3A%2F%2Ftidal.com%2Ftrack%2F258735410')
            -> 'https://tidal.com/track/258735410'
        """
        try:
            return unquote(encoded_url)
        except Exception:
            return None
    
    @staticmethod
    def create_share_url(base_url: str, platform: str, track_id: str, link_type: str = 'track') -> str:
        """
        Create a complete share URL
        
        Args:
            base_url: Base URL (e.g., 'https://unitune.art')
            platform: Platform name
            track_id: Track ID
            link_type: Content type
            
        Returns:
            Complete share URL
            
        Example:
            create_share_url('https://unitune.art', 'spotify', '3n3Ppam7vgaVa1iaRUc9Lp')
            -> 'https://unitune.art/s/c3BvdGlmeTp0cmFjazozbjNQcGFtN3ZnYVZhMWlhUlVjOUxw'
        """
        encoded_id = LinkEncoder.encode(platform, track_id, link_type)
        return f"{base_url}/s/{encoded_id}"
