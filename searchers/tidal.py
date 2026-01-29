"""
TIDAL Searcher - Generates direct track links using TIDAL API
"""
from typing import Optional, Dict, Any
from extractors.tidal import TidalExtractor

class TidalSearcher:
    """Search for tracks on TIDAL using official API to get direct track links"""
    
    def __init__(self):
        self.extractor = TidalExtractor()
    
    def search(self, artist: str, title: str, isrc: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for track on TIDAL and return direct track link
        Uses official TIDAL v2 API
        
        Args:
            artist: Artist name
            title: Track title
            isrc: ISRC code (optional, not used currently)
            
        Returns:
            Dictionary with TIDAL direct track link
        """
        try:
            # Use TidalExtractor to search and get direct track link
            result = self.extractor.search_track(artist, title, isrc)
            
            if result:
                return result
            
            # Fallback: generate search link if API fails
            import urllib.parse
            query = f"{artist} {title}"
            encoded_query = urllib.parse.quote(query)
            
            return {
                'url': f"https://listen.tidal.com/search?q={encoded_query}",
                'id': 'search',
                'is_search': True
            }
            
        except Exception as e:
            print(f"Error searching TIDAL: {e}")
            return None
