"""
Universal Extractor - Extract metadata from any platform by searching on Spotify
"""
import requests
from typing import Optional, Dict, Any
from extractors.spotify import SpotifyExtractor

class UniversalExtractor:
    """
    Extract metadata from any music URL by:
    1. Parsing the URL to get artist/title
    2. Searching on Spotify to get full metadata + ISRC
    """
    
    def __init__(self):
        self.spotify = SpotifyExtractor()
    
    def extract_from_tidal(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from TIDAL track"""
        try:
            # TIDAL public API endpoint
            url = f"https://api.tidal.com/v1/tracks/{track_id}"
            params = {'countryCode': 'US'}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.ok:
                data = response.json()
                artist = data.get('artist', {}).get('name', '')
                title = data.get('title', '')
                isrc = data.get('isrc')
                
                # Search on Spotify for full metadata
                if artist and title:
                    spotify_result = self.spotify.search_track(artist, title, isrc)
                    if spotify_result:
                        return spotify_result
        except:
            pass
        
        return None
    
    def extract_from_youtube(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from YouTube video using YouTube Data API"""
        from config import Config
        
        if not Config.YOUTUBE_API_KEY:
            return None
        
        try:
            from googleapiclient.discovery import build
            
            youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
            
            # Get video details
            request = youtube.videos().list(
                part='snippet',
                id=video_id
            )
            
            response = request.execute()
            
            if response.get('items'):
                video = response['items'][0]['snippet']
                title = video.get('title', '')
                
                # Try to extract artist from title
                # Common formats: "Artist - Title", "Title by Artist", "Artist: Title"
                artist = ''
                if ' - ' in title:
                    parts = title.split(' - ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                elif ' by ' in title.lower():
                    parts = title.lower().split(' by ', 1)
                    title = parts[0].strip()
                    artist = parts[1].strip()
                elif ': ' in title:
                    parts = title.split(': ', 1)
                    artist = parts[0].strip()
                    title = parts[1].strip()
                else:
                    # Use channel name as artist
                    artist = video.get('channelTitle', '').replace(' - Topic', '').replace('VEVO', '').strip()
                
                # Clean up title (remove common suffixes)
                title = title.replace('(Official Video)', '').replace('(Official Audio)', '').replace('[Official Video]', '').strip()
                
                # Search on Spotify for full metadata
                if artist and title:
                    spotify_result = self.spotify.search_track(artist, title)
                    if spotify_result:
                        return spotify_result
        except Exception as e:
            print(f"Error extracting from YouTube: {e}")
        
        return None
    
    def extract_from_deezer(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from Deezer track"""
        try:
            # Deezer public API (no key needed!)
            url = f"https://api.deezer.com/track/{track_id}"
            
            response = requests.get(url, timeout=5)
            
            if response.ok:
                data = response.json()
                if 'error' not in data:
                    artist = data.get('artist', {}).get('name', '')
                    title = data.get('title', '')
                    isrc = data.get('isrc')
                    
                    # Search on Spotify for full metadata
                    if artist and title:
                        spotify_result = self.spotify.search_track(artist, title, isrc)
                        if spotify_result:
                            return spotify_result
        except:
            pass
        
        return None
