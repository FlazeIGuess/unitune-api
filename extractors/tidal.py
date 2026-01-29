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
        Get track metadata from TIDAL
        https://developer.tidal.com/documentation/api/api-reference
        
        Args:
            track_id: TIDAL track ID
            
        Returns:
            Dictionary with track metadata
        """
        # Ensure we have a valid token
        if not self.access_token:
            if not self._get_access_token():
                # Fallback to public API
                return self._get_track_public(track_id)
        
        try:
            url = f"{self.BASE_URL}/v2/tracks/{track_id}"
            
            headers = {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/json'
            }
            
            params = {
                'countryCode': 'US'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 401:
                # Token expired, refresh and retry
                if self._get_access_token():
                    headers['Authorization'] = f'{self.token_type} {self.access_token}'
                    response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.ok:
                data = response.json()
                resource = data.get('resource', {})
                
                # Extract metadata
                title = resource.get('title', '')
                artist_name = ''
                
                # Get artist name
                artists = resource.get('artists', [])
                if artists:
                    artist_name = artists[0].get('name', '')
                
                # Get album art
                album = resource.get('album', {})
                image_cover = album.get('imageCover', [])
                thumbnail_url = None
                if image_cover:
                    # Get highest quality image
                    thumbnail_url = image_cover[-1].get('url') if image_cover else None
                
                # Get ISRC
                isrc = resource.get('isrc')
                
                return {
                    'id': track_id,
                    'title': title,
                    'artist': artist_name,
                    'isrc': isrc,
                    'thumbnail': thumbnail_url,
                    'url': f"https://tidal.com/browse/track/{track_id}",
                    'duration': resource.get('duration'),
                    'explicit': resource.get('explicit', False)
                }
            else:
                print(f"TIDAL API error: {response.status_code}")
                # Fallback to public API
                return self._get_track_public(track_id)
                
        except Exception as e:
            print(f"Error getting TIDAL track: {e}")
            # Fallback to public API
            return self._get_track_public(track_id)
    
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
        Search for track on TIDAL
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, more accurate)
            
        Returns:
            Dictionary with track metadata
        """
        # Ensure we have a valid token
        if not self.access_token:
            if not self._get_access_token():
                # Fallback to public search
                return self._search_public(artist, title, isrc)
        
        try:
            # Try ISRC search first (most accurate)
            if isrc:
                result = self._search_by_isrc(isrc)
                if result:
                    return result
            
            # Fallback to text search
            return self._search_by_text(artist, title)
            
        except Exception as e:
            print(f"Error searching TIDAL: {e}")
            return self._search_public(artist, title, isrc)
    
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
