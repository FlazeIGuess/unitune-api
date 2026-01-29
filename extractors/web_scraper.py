"""
Web Scraper - Extract metadata from platforms without official APIs
Uses web scraping to extract track information from HTML pages
"""
import requests
import re
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from extractors.spotify import SpotifyExtractor

class WebScraper:
    """
    Extract metadata from music platforms using web scraping
    Supports: TIDAL, Apple Music, Amazon Music
    """
    
    def __init__(self):
        self.spotify = SpotifyExtractor()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def scrape_tidal(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from TIDAL track page
        
        Args:
            track_id: TIDAL track ID
            
        Returns:
            Dictionary with track metadata
        """
        try:
            # Try both URL formats
            urls = [
                f"https://tidal.com/browse/track/{track_id}",
                f"https://listen.tidal.com/track/{track_id}"
            ]
            
            for url in urls:
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    
                    if response.ok:
                        html = response.text
                        
                        # Extract from meta tags
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Try og:title
                        title_tag = soup.find('meta', property='og:title')
                        title = title_tag['content'] if title_tag else ''
                        
                        # Try og:description for artist
                        desc_tag = soup.find('meta', property='og:description')
                        description = desc_tag['content'] if desc_tag else ''
                        
                        # Extract artist from description or title
                        artist = ''
                        if description:
                            # Description often contains "Artist - Title" or "Title by Artist"
                            if ' - ' in description:
                                parts = description.split(' - ', 1)
                                artist = parts[0].strip()
                                if not title:
                                    title = parts[1].strip()
                            elif ' by ' in description.lower():
                                parts = description.lower().split(' by ', 1)
                                if not title:
                                    title = parts[0].strip()
                                artist = parts[1].strip()
                        
                        # Try to extract from JSON-LD
                        json_ld = soup.find('script', type='application/ld+json')
                        if json_ld:
                            import json
                            try:
                                data = json.loads(json_ld.string)
                                if isinstance(data, dict):
                                    if 'name' in data and not title:
                                        title = data['name']
                                    if 'byArtist' in data and not artist:
                                        if isinstance(data['byArtist'], dict):
                                            artist = data['byArtist'].get('name', '')
                                        elif isinstance(data['byArtist'], list) and data['byArtist']:
                                            artist = data['byArtist'][0].get('name', '')
                            except:
                                pass
                        
                        # Get thumbnail
                        thumbnail_url = None
                        img_tag = soup.find('meta', property='og:image')
                        if img_tag:
                            thumbnail_url = img_tag['content']
                        
                        if title and artist:
                            # Search on Spotify for full metadata + ISRC
                            spotify_result = self.spotify.search_track(artist, title)
                            if spotify_result:
                                # Keep TIDAL as the source
                                spotify_result['url'] = url
                                spotify_result['id'] = track_id
                                spotify_result['apiProvider'] = 'tidal'
                                if thumbnail_url:
                                    spotify_result['thumbnailUrl'] = thumbnail_url
                                return spotify_result
                            
                            # Fallback: return basic metadata
                            return {
                                'id': track_id,
                                'title': title,
                                'artist': artist,
                                'url': url,
                                'thumbnailUrl': thumbnail_url,
                                'apiProvider': 'tidal',
                                'platforms': ['tidal']
                            }
                except:
                    continue
                    
        except Exception as e:
            print(f"Error scraping TIDAL: {e}")
        
        return None
    
    def scrape_apple_music(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from Apple Music track page
        
        Args:
            track_id: Apple Music track ID (song ID)
            
        Returns:
            Dictionary with track metadata
        """
        try:
            # Apple Music URLs need the full path, but we can try to construct it
            # Format: https://music.apple.com/us/song/{name}/{id}
            # We'll try the API endpoint first
            
            # Try iTunes Search API (public, no key needed)
            url = f"https://itunes.apple.com/lookup?id={track_id}&entity=song"
            
            response = requests.get(url, timeout=10)
            
            if response.ok:
                data = response.json()
                results = data.get('results', [])
                
                if results:
                    track = results[0]
                    artist = track.get('artistName', '')
                    title = track.get('trackName', '')
                    
                    if artist and title:
                        # Search on Spotify for full metadata + ISRC
                        spotify_result = self.spotify.search_track(artist, title)
                        if spotify_result:
                            # Keep Apple Music as the source
                            spotify_result['url'] = track.get('trackViewUrl', f"https://music.apple.com/song/{track_id}")
                            spotify_result['id'] = track_id
                            spotify_result['apiProvider'] = 'appleMusic'
                            spotify_result['thumbnailUrl'] = track.get('artworkUrl100', '').replace('100x100', '640x640')
                            return spotify_result
                        
                        # Fallback: return basic metadata
                        return {
                            'id': track_id,
                            'title': title,
                            'artist': artist,
                            'url': track.get('trackViewUrl', f"https://music.apple.com/song/{track_id}"),
                            'thumbnailUrl': track.get('artworkUrl100', '').replace('100x100', '640x640'),
                            'apiProvider': 'appleMusic',
                            'platforms': ['appleMusic']
                        }
                        
        except Exception as e:
            print(f"Error scraping Apple Music: {e}")
        
        return None
    
    def scrape_amazon_music(self, track_id: str) -> Optional[Dict[str, Any]]:
        """
        Extract metadata from Amazon Music track page
        
        Args:
            track_id: Amazon Music track ID (ASIN)
            
        Returns:
            Dictionary with track metadata
        """
        try:
            url = f"https://music.amazon.com/albums/{track_id}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.ok:
                html = response.text
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract from meta tags
                title_tag = soup.find('meta', property='og:title')
                title = title_tag['content'] if title_tag else ''
                
                desc_tag = soup.find('meta', property='og:description')
                description = desc_tag['content'] if desc_tag else ''
                
                # Extract artist from description
                artist = ''
                if description:
                    # Description often contains "Artist - Title" or "Title by Artist"
                    if ' - ' in description:
                        parts = description.split(' - ', 1)
                        artist = parts[0].strip()
                        if not title:
                            title = parts[1].strip()
                    elif ' by ' in description.lower():
                        parts = description.lower().split(' by ', 1)
                        if not title:
                            title = parts[0].strip()
                        artist = parts[1].strip()
                
                # Get thumbnail
                thumbnail_url = None
                img_tag = soup.find('meta', property='og:image')
                if img_tag:
                    thumbnail_url = img_tag['content']
                
                if title and artist:
                    # Search on Spotify for full metadata + ISRC
                    spotify_result = self.spotify.search_track(artist, title)
                    if spotify_result:
                        # Keep Amazon Music as the source
                        spotify_result['url'] = url
                        spotify_result['id'] = track_id
                        spotify_result['apiProvider'] = 'amazonMusic'
                        if thumbnail_url:
                            spotify_result['thumbnailUrl'] = thumbnail_url
                        return spotify_result
                    
                    # Fallback: return basic metadata
                    return {
                        'id': track_id,
                        'title': title,
                        'artist': artist,
                        'url': url,
                        'thumbnailUrl': thumbnail_url,
                        'apiProvider': 'amazonMusic',
                        'platforms': ['amazonMusic']
                    }
                    
        except Exception as e:
            print(f"Error scraping Amazon Music: {e}")
        
        return None
