"""
Spotify Metadata Extractor
"""
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Optional, Dict, Any
from config import Config

class SpotifyExtractor:
    """Extract metadata from Spotify tracks, albums, and artists"""
    
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

    def get_album_metadata(self, album_id: str) -> Optional[Dict[str, Any]]:
        """
        Get album metadata from Spotify
        
        Args:
            album_id: Spotify album ID
            
        Returns:
            Dictionary with album metadata or None if not found
        """
        try:
            album = self.sp.album(album_id)
            
            # Extract metadata
            metadata = {
                'id': album['id'],
                'title': album['name'],
                'artist': album['artists'][0]['name'] if album['artists'] else 'Unknown Artist',
                'album': album['name'],
                'thumbnail': album['images'][0]['url'] if album['images'] else None,
                'url': album['external_urls']['spotify'],
                'release_date': album.get('release_date'),
                'total_tracks': album.get('total_tracks', 0),
                'platform': 'spotify',
                'type': 'album'
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting Spotify album metadata: {e}")
            return None
    
    def get_artist_metadata(self, artist_id: str) -> Optional[Dict[str, Any]]:
        """
        Get artist metadata from Spotify
        
        Args:
            artist_id: Spotify artist ID
            
        Returns:
            Dictionary with artist metadata or None if not found
        """
        try:
            artist = self.sp.artist(artist_id)
            
            # Extract metadata
            metadata = {
                'id': artist['id'],
                'name': artist['name'],
                'artist': artist['name'],
                'thumbnail': artist['images'][0]['url'] if artist['images'] else None,
                'url': artist['external_urls']['spotify'],
                'genres': artist.get('genres', []),
                'followers': artist.get('followers', {}).get('total', 0),
                'platform': 'spotify',
                'type': 'artist'
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error extracting Spotify artist metadata: {e}")
            return None
    
    def search_album(self, artist: str, album_title: str) -> Optional[Dict[str, Any]]:
        """
        Search for album on Spotify
        
        Args:
            artist: Artist name
            album_title: Album title
            
        Returns:
            Album metadata or None if not found
        """
        try:
            query = f'artist:{artist} album:{album_title}'
            results = self.sp.search(q=query, type='album', limit=1)
            
            if results['albums']['items']:
                album = results['albums']['items'][0]
                return self.get_album_metadata(album['id'])
            
            return None
            
        except Exception as e:
            print(f"Error searching Spotify album: {e}")
            return None
    
    def search_artist(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for artist on Spotify
        
        Args:
            artist_name: Artist name
            
        Returns:
            Artist metadata or None if not found
        """
        try:
            results = self.sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            
            if results['artists']['items']:
                artist = results['artists']['items'][0]
                return self.get_artist_metadata(artist['id'])
            
            return None
            
        except Exception as e:
            print(f"Error searching Spotify artist: {e}")
            return None
