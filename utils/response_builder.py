"""
Response Builder - Build Odesli-compatible JSON responses
"""
from typing import Dict, Any, Optional

class ResponseBuilder:
    """Build Odesli-compatible API responses"""
    
    @staticmethod
    def build_response(
        metadata: Dict[str, Any],
        links: Dict[str, Dict[str, Any]],
        source_platform: str
    ) -> Dict[str, Any]:
        """
        Build Odesli-compatible response
        
        Args:
            metadata: Track metadata (title, artist, etc.)
            links: Links to all platforms
            source_platform: Original platform
            
        Returns:
            Odesli-compatible JSON response
        """
        # Build entity unique ID
        entity_id = f"{source_platform.upper()}::TRACK::{metadata.get('id', 'unknown')}"
        
        # Build entity
        entity = {
            'id': metadata.get('id'),
            'type': 'song',
            'title': metadata.get('title', 'Unknown Title'),
            'artistName': metadata.get('artist', 'Unknown Artist'),
            'thumbnailUrl': metadata.get('thumbnail'),
            'thumbnailWidth': 640,
            'thumbnailHeight': 640,
            'apiProvider': source_platform,
            'platforms': list(links.keys())
        }
        
        # Build links by platform
        links_by_platform = {}
        for platform, link_data in links.items():
            links_by_platform[platform] = {
                'url': link_data['url'],
                'entityUniqueId': link_data.get('entityUniqueId', entity_id)
            }
            
            # Add native app URI if available
            if 'nativeAppUri' in link_data:
                links_by_platform[platform]['nativeAppUriMobile'] = link_data['nativeAppUri']
        
        # Build full response
        response = {
            'entityUniqueId': entity_id,
            'userCountry': 'US',  # Could be dynamic based on request
            'pageUrl': f"https://unitune.art/s/{metadata.get('url', '')}",
            'entitiesByUniqueId': {
                entity_id: entity
            },
            'linksByPlatform': links_by_platform
        }
        
        return response
    
    @staticmethod
    def build_error_response(message: str, status_code: int = 400) -> tuple:
        """Build error response"""
        return {
            'error': message,
            'status': status_code
        }, status_code
