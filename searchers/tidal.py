"""
TIDAL Searcher - Generates direct track links using TIDAL search
"""
from typing import Optional, Dict, Any
import urllib.parse

class TidalSearcher:
    """Search for tracks on TIDAL using direct search links"""
    
    def __init__(self):
        pass
    
    def search(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Generate TIDAL search link that opens directly in TIDAL app/web
        
        TIDAL's API requires special access tiers that are not available
        for all developer accounts. As a workaround, we generate search
        links that open in TIDAL and show the track directly.
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, not used currently)
            
        Returns:
            Dictionary with TIDAL search link
        """
        try:
            # Create search query
            query = f"{artist} {title}"
            encoded_query = urllib.parse.quote(query)
            
            # TIDAL listen.tidal.com search opens in app if installed
            # and shows results directly
            return {
                'url': f"https://listen.tidal.com/search?q={encoded_query}",
                'id': 'search',
                'is_search': True
            }
            
        except Exception as e:
            print(f"Error generating TIDAL link: {e}")
            return None
