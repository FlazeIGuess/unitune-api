"""
YouTube Music Searcher
"""
from typing import Optional, Dict, Any
from config import Config

try:
    from googleapiclient.discovery import build
    YOUTUBE_AVAILABLE = True
except ImportError:
    YOUTUBE_AVAILABLE = False
    print("⚠️  google-api-python-client not installed. YouTube search disabled.")

class YouTubeSearcher:
    """Search for tracks on YouTube Music"""
    
    def __init__(self):
        """Initialize YouTube API client"""
        self.youtube = None
        if YOUTUBE_AVAILABLE and Config.YOUTUBE_API_KEY:
            try:
                self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
            except Exception as e:
                print(f"Error initializing YouTube API: {e}")
    
    def search(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """
        Search for track on YouTube Music
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Dictionary with YouTube links or None
        """
        if not self.youtube:
            # Fallback: Generic search link
            query = f"{artist} {title}".replace(' ', '+')
            return {
                'url': f"https://music.youtube.com/search?q={query}",
                'youtube_url': f"https://www.youtube.com/results?search_query={query}",
                'is_search': True
            }
        
        try:
            # Search for "Artist - Title official audio"
            query = f"{artist} - {title} official audio"
            
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='video',
                maxResults=5
            )
            
            response = request.execute()
            
            if not response.get('items'):
                return self._fallback_link(artist, title)
            
            # Prefer "Topic" channels (official music)
            for item in response['items']:
                channel = item['snippet']['channelTitle']
                if 'Topic' in channel or 'VEVO' in channel:
                    video_id = item['id']['videoId']
                    return {
                        'url': f"https://music.youtube.com/watch?v={video_id}",
                        'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                        'video_id': video_id,
                        'is_search': False
                    }
            
            # Fallback: First result
            video_id = response['items'][0]['id']['videoId']
            return {
                'url': f"https://music.youtube.com/watch?v={video_id}",
                'youtube_url': f"https://www.youtube.com/watch?v={video_id}",
                'video_id': video_id,
                'is_search': False
            }
            
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            return self._fallback_link(artist, title)
    
    def _fallback_link(self, artist: str, title: str) -> Dict[str, Any]:
        """Generate fallback search link"""
        query = f"{artist} {title}".replace(' ', '+')
        return {
            'url': f"https://music.youtube.com/search?q={query}",
            'youtube_url': f"https://www.youtube.com/results?search_query={query}",
            'is_search': True
        }
