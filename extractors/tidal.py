"""
TIDAL Extractor - Official TIDAL API Integration
Uses TIDAL Developer API with OAuth 2.1
"""
import requests
import base64
from typing import Optional, Dict, Any
from config import Config

class TidalExtractor:
    """
    Extract metadata from TIDAL using official API
    Requires TIDAL_CLIENT_ID and TIDAL_CLIENT_SECRET
    """
    
    BASE_URL = "https://openapi.tidal.com"
    AUTH_URL = "https://auth.tidal.com/v1/oauth2/token"
    
    def __init__(self):
        self.access_token = None
        self.token_type = None
    
    def _get_access_token(self) -> bool:
        """
        Get access token using Client Credentials flow
        https://developer.tidal.com/documentation/authorization/authorization-client-credentials
        """
        if not Config.TIDAL_CLIENT_ID or not Config.TIDAL_CLIENT_SECRET:
            return False
        
        try:
            # Create Basic Auth header
            credentials = f"{Config.TIDAL_CLIENT_ID}:{Config.TIDAL_CLIENT_SECRET}"
            encoded = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'grant_type': 'client_credentials'
            }
            
            response = requests.post(self.AUTH_URL, headers=headers, data=data, timeout=10)
            
            if response.ok:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                self.token_type = token_data.get('token_type', 'Bearer')
                return True
            else:
                print(f"TIDAL auth error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"Error getting TIDAL access token: {e}")
            return False
    
    def get_track_metadata(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get track metadata from TIDAL using track ID
        Uses v2 API with proper JSON:API format
        
        Args:
            track_id: TIDAL track ID
            
        Returns:
            Dictionary with track metadata
        """
        # Ensure we have a valid token
        if not self.access_token:
            if not self._get_access_token():
                return None
        
        try:
            # v2 API endpoint for tracks
            url = f"{self.BASE_URL}/v2/tracks/{track_id}"
            
            headers = {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/vnd.api+json'
            }
            
            params = {
                'countryCode': 'US',
                'include': 'artists,albums'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                if self._get_access_token():
                    headers['Authorization'] = f'{self.token_type} {self.access_token}'
                    response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                resource = data.get('data', {})
                attributes = resource.get('attributes', {})
                
                # Extract metadata
                title = attributes.get('title', '')
                artist_name = ''
                
                # Get artist from included data
                included = data.get('included', [])
                for item in included:
                    if item.get('type') == 'artists':
                        artist_name = item.get('attributes', {}).get('name', '')
                        break
                
                # Get ISRC
                isrc = attributes.get('isrc')
                
                # Get album art from included albums
                thumbnail_url = None
                for item in included:
                    if item.get('type') == 'albums':
                        image_cover = item.get('attributes', {}).get('imageCover', [])
                        if image_cover:
                            thumbnail_url = image_cover[-1].get('url') if image_cover else None
                        break
                
                return {
                    'id': track_id,
                    'title': title,
                    'artist': artist_name,
                    'isrc': isrc,
                    'thumbnailUrl': thumbnail_url,
                    'url': f"https://tidal.com/browse/track/{track_id}",
                    'apiProvider': 'tidal',
                    'platforms': ['tidal']
                }
            else:
                print(f"TIDAL API error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"Error getting TIDAL track: {e}")
        
        return None
    
    def _get_track_public(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Fallback: Use public TIDAL API (no auth required)
        This is less reliable but works without credentials
        """
        try:
            url = f"https://api.tidal.com/v1/tracks/{track_id}"
            params = {'countryCode': 'US'}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                
                artist_name = ''
                if 'artist' in data:
                    artist_name = data['artist'].get('name', '')
                elif 'artists' in data and data['artists']:
                    artist_name = data['artists'][0].get('name', '')
                
                # Get album art
                thumbnail_url = None
                if 'album' in data and 'cover' in data['album']:
                    cover_id = data['album']['cover']
                    # TIDAL image URL format
                    thumbnail_url = f"https://resources.tidal.com/images/{cover_id.replace('-', '/')}/640x640.jpg"
                
                return {
                    'id': track_id,
                    'title': data.get('title', ''),
                    'artist': artist_name,
                    'isrc': data.get('isrc'),
                    'thumbnail': thumbnail_url,
                    'url': f"https://tidal.com/browse/track/{track_id}",
                    'duration': data.get('duration'),
                    'explicit': data.get('explicit', False)
                }
        except Exception as e:
            print(f"Error with public TIDAL API: {e}")
        
        return None
    
    def search_track(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for track on TIDAL using v2 API
        According to official docs: https://openapi.tidal.com/v2/searchResults/{query}/relationships/tracks
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, more accurate)
            
        Returns:
            Dictionary with track metadata including direct track link
        """
        # Ensure we have a valid token
        if not self.access_token:
            if not self._get_access_token():
                return None
        
        try:
            # Build search query
            query = f"{artist} {title}"
            
            # URL encode the query - the query is part of the URL path, not a parameter
            from urllib.parse import quote
            encoded_query = quote(query)
            
            # Use v2 search endpoint - query is in the URL path
            url = f"{self.BASE_URL}/v2/searchResults/{encoded_query}/relationships/tracks"
            
            headers = {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/vnd.api+json'
            }
            
            params = {
                'countryCode': 'US',
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                # Token expired, refresh
                if self._get_access_token():
                    headers['Authorization'] = f'{self.token_type} {self.access_token}'
                    response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                tracks = data.get('data', [])
                
                if tracks:
                    track = tracks[0]
                    track_id = track.get('id')
                    
                    if track_id:
                        # Return direct track link instead of search link
                        return {
                            'url': f"https://tidal.com/browse/track/{track_id}",
                            'id': track_id,
                            'is_search': False
                        }
            else:
                print(f"TIDAL search error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"Error searching TIDAL: {e}")
        
        return None
    
    def _search_by_isrc(self, isrc: str) -> Optional[Dict[str, Any]]:
        """Search by ISRC using official API"""
        try:
            url = f"{self.BASE_URL}/v2/searchresults/tracks"
            
            headers = {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/json'
            }
            
            params = {
                'query': isrc,
                'countryCode': 'US',
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                tracks = data.get('tracks', [])
                if tracks:
                    track = tracks[0].get('resource', {})
                    track_id = track.get('id')
                    if track_id:
                        return self.get_track_metadata(str(track_id))
        except:
            pass
        
        return None
    
    def _search_by_text(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search by artist and title using official API"""
        try:
            query = f"{artist} {title}"
            url = f"{self.BASE_URL}/v2/searchresults/tracks"
            
            headers = {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/json'
            }
            
            params = {
                'query': query,
                'countryCode': 'US',
                'limit': 1
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                tracks = data.get('tracks', [])
                if tracks:
                    track = tracks[0].get('resource', {})
                    track_id = track.get('id')
                    if track_id:
                        return self.get_track_metadata(str(track_id))
        except:
            pass
        
        return None
    
    def _search_public(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Fallback: Search using public API"""
        try:
            # Try ISRC first
            if isrc:
                url = "https://api.tidal.com/v1/search/tracks"
                params = {
                    'query': isrc,
                    'limit': 1,
                    'countryCode': 'US'
                }
                
                response = requests.get(url, params=params, timeout=5)
                
                if response.ok:
                    data = response.json()
                    if data.get('items'):
                        track = data['items'][0]
                        track_id = track['id']
                        return self._get_track_public(str(track_id))
            
            # Fallback to text search
            query = f"{artist} {title}"
            url = "https://api.tidal.com/v1/search/tracks"
            params = {
                'query': query,
                'limit': 1,
                'countryCode': 'US'
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                if data.get('items'):
                    track = data['items'][0]
                    track_id = track['id']
                    return self._get_track_public(str(track_id))
        except:
            pass
        
        return None
