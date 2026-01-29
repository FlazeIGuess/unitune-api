"""
Deezer Searcher - No API key needed!
"""
import requests
from typing import Optional, Dict, Any

class DeezerSearcher:
    """Search for tracks on Deezer (public API, no key needed)"""
    
    BASE_URL = "https://api.deezer.com"
    
    def search(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for track on Deezer
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, more accurate)
            
        Returns:
            Dictionary with Deezer link or None
        """
        try:
            # Try ISRC first (most accurate)
            if isrc:
                result = self._search_by_isrc(isrc)
                if result:
                    return result
            
            # Fallback: Search by artist and title
            return self._search_by_query(artist, title)
            
        except Exception as e:
            print(f"Error searching Deezer: {e}")
            return self._fallback_link(artist, title)
    
    def _search_by_isrc(self, isrc: str) -> Optional[Dict[str, Any]]:
        """Search by ISRC code"""
        try:
            url = f"{self.BASE_URL}/track/isrc:{isrc}"
            response = requests.get(url, timeout=5)
            
            if response.ok:
                data = response.json()
                if 'id' in data and 'error' not in data:
                    return {
                        'url': data['link'],
                        'id': str(data['id']),
                        'title': data.get('title'),
                        'artist': data.get('artist', {}).get('name'),
                        'is_search': False
                    }
        except:
            pass
        
        return None
    
    def _search_by_query(self, artist: str, title: str) -> Optional[Dict[str, Any]]:
        """Search by artist and title"""
        try:
            # Build query
            query = f'artist:"{artist}" track:"{title}"'
            url = f"{self.BASE_URL}/search"
            
            response = requests.get(url, params={'q': query}, timeout=5)
            
            if response.ok:
                data = response.json()
                if data.get('data'):
                    track = data['data'][0]
                    return {
                        'url': track['link'],
                        'id': str(track['id']),
                        'title': track.get('title'),
                        'artist': track.get('artist', {}).get('name'),
                        'is_search': False
                    }
        except:
            pass
        
        return self._fallback_link(artist, title)
    
    def _fallback_link(self, artist: str, title: str) -> Dict[str, Any]:
        """Generate fallback search link"""
        query = f"{artist} {title}".replace(' ', '+')
        return {
            'url': f"https://www.deezer.com/search/{query}",
            'is_search': True
        }
