"""
Response Builder - Build Odesli-compatible JSON responses
"""
from typing import Dict, Any, Optional
from utils.url_parser import ContentType

class ResponseBuilder:
    """Build Odesli-compatible API responses"""
    
    @staticmethod
    def build_response(
        metadata: Dict[str, Any],
        links: Dict[str, Dict[str, Any]],
        source_platform: str,
        content_type: ContentType = ContentType.TRACK
    ) -> Dict[str, Any]:
        """
        Build Odesli-compatible response
        
        Args:
            metadata: Content metadata (title, artist, etc.)
            links: Links to all platforms
            source_platform: Original platform
            content_type: Type of content (track, album, artist)
            
        Returns:
            Odesli-compatible JSON response
        """
        from utils.link_encoder import LinkEncoder
        
        # Map content type to entity type string
        type_map = {
            ContentType.TRACK: 'song',
            ContentType.ALBUM: 'album',
            ContentType.ARTIST: 'artist',
            ContentType.PLAYLIST: 'playlist',
            ContentType.UNKNOWN: 'song'
        }
        entity_type = type_map.get(content_type, 'song')
        
        # Build entity unique ID
        content_type_upper = content_type.value.upper()
        entity_id = f"{source_platform.upper()}::{content_type_upper}::{metadata.get('id', 'unknown')}"
        
        # Build entity based on content type
        entity = {
            'id': metadata.get('id'),
            'type': entity_type,
            'apiProvider': source_platform,
            'platforms': list(links.keys())
        }
        
        # Add type-specific fields
        if content_type == ContentType.TRACK:
            entity.update({
                'title': metadata.get('title', 'Unknown Title'),
                'artistName': metadata.get('artist', 'Unknown Artist'),
                'thumbnailUrl': metadata.get('thumbnail'),
                'thumbnailWidth': 640,
                'thumbnailHeight': 640,
            })
        elif content_type == ContentType.ALBUM:
            entity.update({
                'title': metadata.get('album') or metadata.get('title', 'Unknown Album'),
                'artistName': metadata.get('artist', 'Unknown Artist'),
                'thumbnailUrl': metadata.get('thumbnail'),
                'thumbnailWidth': 640,
                'thumbnailHeight': 640,
                'releaseDate': metadata.get('release_date'),
                'totalTracks': metadata.get('total_tracks'),
            })
        elif content_type == ContentType.ARTIST:
            entity.update({
                'name': metadata.get('name') or metadata.get('artist', 'Unknown Artist'),
                'thumbnailUrl': metadata.get('thumbnail'),
                'thumbnailWidth': 640,
                'thumbnailHeight': 640,
                'genres': metadata.get('genres', []),
                'followers': metadata.get('followers'),
            })
        
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
        
        # Generate new-format share URL (base64-encoded)
        content_id = metadata.get('id', 'unknown')
        encoded_id = LinkEncoder.encode(source_platform, content_id, content_type)
        page_url = f"https://unitune.art/s/{encoded_id}"
        
        # Build full response
        response = {
            'entityUniqueId': entity_id,
            'userCountry': 'US',  # Could be dynamic based on request
            'pageUrl': page_url,
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
