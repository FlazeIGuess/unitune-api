"""
Link Encoder/Decoder - Convert between music URLs and safe share links
Prevents phishing warnings by encoding platform/track info instead of full URLs
"""
import base64
import re
from typing import Optional, Tuple
from urllib.parse import unquote
from .url_parser import ContentType


class LinkEncoder:
    """Encode and decode UniTune share links"""
    
    @staticmethod
    def encode(platform: str, content_id: str, content_type: ContentType = ContentType.TRACK) -> str:
        """
        Encode platform and content ID into a safe share link identifier
        
        Args:
            platform: Platform name (spotify, tidal, appleMusic, etc.)
            content_id: Content ID from the platform (track, album, or artist ID)
            content_type: Type of content (ContentType enum)
            
        Returns:
            Base64-encoded identifier safe for URLs
            
        Example:
            encode('tidal', '258735410', ContentType.TRACK) -> 'dGlkYWw6dHJhY2s6MjU4NzM1NDEw'
            encode('spotify', '6vV5UrXcfyQD1wu4Qo2I9K', ContentType.ALBUM) -> encoded album link
        """
        # Create identifier string: platform:type:id
        type_str = content_type.value if isinstance(content_type, ContentType) else str(content_type)
        identifier = f"{platform}:{type_str}:{content_id}"
        
        # Encode to base64 (URL-safe variant)
        encoded_bytes = base64.urlsafe_b64encode(identifier.encode('utf-8'))
        encoded_str = encoded_bytes.decode('utf-8')
        
        # Remove padding (= characters) for cleaner URLs
        return encoded_str.rstrip('=')
    
    @staticmethod
    def decode(encoded_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Decode a share link identifier back to platform, content type, and content ID
        
        Args:
            encoded_id: Base64-encoded identifier
            
        Returns:
            Tuple of (platform, content_type_str, content_id) or None if invalid
            
        Example:
            decode('dGlkYWw6dHJhY2s6MjU4NzM1NDEw') -> ('tidal', 'track', '258735410')
            decode('c3BvdGlmeTphbGJ1bTo2dlY1VXJYY2Z5UUQxd3U0UW8ySTlL') -> ('spotify', 'album', '6vV5UrXcfyQD1wu4Qo2I9K')
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
            
            platform, content_type_str, content_id = parts
            return (platform, content_type_str, content_id)
            
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
    def create_share_url(base_url: str, platform: str, content_id: str, content_type: ContentType = ContentType.TRACK) -> str:
        """
        Create a complete share URL
        
        Args:
            base_url: Base URL (e.g., 'https://unitune.art')
            platform: Platform name
            content_id: Content ID (track, album, or artist ID)
            content_type: Content type (ContentType enum)
            
        Returns:
            Complete share URL
            
        Example:
            create_share_url('https://unitune.art', 'spotify', '3n3Ppam7vgaVa1iaRUc9Lp', ContentType.TRACK)
            -> 'https://unitune.art/s/c3BvdGlmeTp0cmFjazozbjNQcGFtN3ZnYVZhMWlhUlVjOUxw'
        """
        encoded_id = LinkEncoder.encode(platform, content_id, content_type)
        return f"{base_url}/s/{encoded_id}"
