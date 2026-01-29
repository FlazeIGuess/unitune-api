"""
Spotify Metadata Extractor
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, Dict, Any
from config import Config

class SpotifyExtractor:
    """Extract metadata from Spotify tracks"""
    
    def __init__(self):
        """Initialize Spotify client"""
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyClientCredentials(
                client_id=Config.SPOTIFY_CLIENT_ID,
                client_secret=Config.SPOTIFY_CLIENT_SECRET
            )
        )
    
    def get_track_metadata(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Get track metadata from Spotify
        
        Args:
            track_id: Spotify track ID
            
        Returns:
            Dictionary with track metadata or None if not found
        """
        try:
            track = self.sp.track(track_id)
            
            # Extract metadata
            metadata = {
                'id': track['id'],
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'isrc': track['external_ids'].get('isrc'),
                'thumbnail': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'url': track['external_urls']['spotify'],
                'duration_ms': track['duration_ms'],
                'platform': 'spotify'
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting Spotify metadata: {e}")
            return None
    
    def search_track(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for track on Spotify
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, more accurate)
            
        Returns:
            Track metadata or None if not found
        """
        try:
            # Try ISRC first (most accurate)
            if isrc:
                results = self.sp.search(q=f'isrc:{isrc}', type='track', limit=1)
                if results['tracks']['items']:
                    track = results['tracks']['items'][0]
                    return self.get_track_metadata(track['id'])
            
            # Fallback: Search by artist and title
            query = f'artist:{artist} track:{title}'
            results = self.sp.search(q=query, type='track', limit=1)
            
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                return self.get_track_metadata(track['id'])
            
            return None
            
        except Exception as e:
            print(f"Error searching Spotify: {e}")
            return None
