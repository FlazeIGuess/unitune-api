"""
Apple Music Searcher - Generic search links (no API)
"""
from typing import Dict, Any

class AppleMusicSearcher:
    """Generate Apple Music search links"""
    
    def search(self, artist: str, title: str) -> Dict[str, Any]:
        """
        Generate Apple Music search link
        
        Args:
            artist: Artist name
            title: Track title
            
        Returns:
            Dictionary with Apple Music search link
        """
        query = f"{artist} {title}".replace(' ', '+')
        
        return {
            'url': f"https://music.apple.com/search?term={query}",
            'is_search': True
        }
