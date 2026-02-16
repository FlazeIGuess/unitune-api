"""
UniTune Music Link API
Self-hosted Odesli/SongLink alternative
"""
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import secrets
from flask_cors import CORS
from config import Config
from utils.url_parser import URLParser, ContentType
from utils.response_builder import ResponseBuilder
from utils.link_encoder import LinkEncoder
from extractors.spotify import SpotifyExtractor
from extractors.tidal import TidalExtractor
from extractors.universal import UniversalExtractor
from extractors.web_scraper import WebScraper
from searchers.youtube import YouTubeSearcher
from searchers.deezer import DeezerSearcher
from searchers.tidal import TidalSearcher
from searchers.apple_music import AppleMusicSearcher
from searchers.amazon_music import AmazonMusicSearcher
from db import Base, engine, get_session
from sqlalchemy.exc import OperationalError
from models import Playlist

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Validate configuration
Config.validate()

# Initialize extractors and searchers
spotify_extractor = SpotifyExtractor()
tidal_extractor = TidalExtractor()
universal_extractor = UniversalExtractor()
web_scraper = WebScraper()
youtube_searcher = YouTubeSearcher()
deezer_searcher = DeezerSearcher()
tidal_searcher = TidalSearcher()  # Uses its own TidalExtractor instance
apple_music_searcher = AppleMusicSearcher()
amazon_music_searcher = AmazonMusicSearcher()

try:
    Base.metadata.create_all(bind=engine, checkfirst=True)
except OperationalError as e:
    if 'already exists' not in str(e).lower():
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.1.0',
        'spotify_configured': bool(Config.SPOTIFY_CLIENT_ID),
        'youtube_configured': bool(Config.YOUTUBE_API_KEY),
        'playlist_storage': Config.DATABASE_URL.split(':')[0]
    })

@app.route('/s/<path:encoded_id>', methods=['GET'])
def handle_share_link(encoded_id):
    """
    Handle UniTune share links: /s/{encodedId}
    
    Format: Base64-encoded platform:type:id (e.g., /s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw)
    Supports tracks, albums, and artists
    
    Returns JSON response. Frontend (Cloudflare Worker) handles HTML rendering.
    """
    try:
        # Decode base64 identifier
        decoded = LinkEncoder.decode(encoded_id)
        if not decoded:
            return ResponseBuilder.build_error_response('Invalid share link format', 400)
        
        platform, content_type_str, content_id = decoded
        
        # Map content type string to ContentType enum
        content_type_map = {
            'track': ContentType.TRACK,
            'album': ContentType.ALBUM,
            'artist': ContentType.ARTIST,
            'playlist': ContentType.PLAYLIST
        }
        content_type = content_type_map.get(content_type_str, ContentType.TRACK)
        
        # Reconstruct URL for processing based on content type
        platform_urls = {
            'spotify': {
                ContentType.TRACK: f'https://open.spotify.com/track/{content_id}',
                ContentType.ALBUM: f'https://open.spotify.com/album/{content_id}',
                ContentType.ARTIST: f'https://open.spotify.com/artist/{content_id}',
            },
            'tidal': {
                ContentType.TRACK: f'https://tidal.com/track/{content_id}',
                ContentType.ALBUM: f'https://tidal.com/album/{content_id}',
                ContentType.ARTIST: f'https://tidal.com/artist/{content_id}',
            },
            'appleMusic': {
                ContentType.TRACK: f'https://music.apple.com/song/{content_id}',
                ContentType.ALBUM: f'https://music.apple.com/album/{content_id}',
                ContentType.ARTIST: f'https://music.apple.com/artist/{content_id}',
            },
            'youtube': {
                ContentType.TRACK: f'https://youtube.com/watch?v={content_id}',
                ContentType.ARTIST: f'https://youtube.com/@{content_id}',
            },
            'youtubeMusic': {
                ContentType.TRACK: f'https://music.youtube.com/watch?v={content_id}',
            },
            'deezer': {
                ContentType.TRACK: f'https://deezer.com/track/{content_id}',
                ContentType.ALBUM: f'https://deezer.com/album/{content_id}',
                ContentType.ARTIST: f'https://deezer.com/artist/{content_id}',
            },
            'amazonMusic': {
                ContentType.TRACK: f'https://music.amazon.com/tracks/{content_id}',
                ContentType.ALBUM: f'https://music.amazon.com/albums/{content_id}',
                ContentType.ARTIST: f'https://music.amazon.com/artists/{content_id}',
            }
        }
        
        platform_type_urls = platform_urls.get(platform, {})
        reconstructed_url = platform_type_urls.get(content_type)
        
        if not reconstructed_url:
            return ResponseBuilder.build_error_response(f'Unsupported platform or content type: {platform}/{content_type_str}', 400)
        
        # Process the reconstructed URL
        return _process_music_link(reconstructed_url)
        
    except Exception as e:
        return ResponseBuilder.build_error_response(f'Error processing share link: {str(e)}', 400)

@app.route('/v1-alpha.1/links', methods=['GET'])
def convert_link():
    """
    Main endpoint - Convert music link between platforms
    Compatible with Odesli API format
    """
    # Get URL parameter
    music_url = request.args.get('url')
    
    if not music_url:
        return ResponseBuilder.build_error_response('Missing url parameter', 400)
    
    return _process_music_link(music_url)

@app.route('/v1-alpha.1/batch', methods=['POST'])
def convert_batch():
    """
    Batch conversion endpoint - Convert multiple music links at once
    
    Request body:
    {
        "urls": ["url1", "url2", ...],  # Max 10 URLs
        "preferred_service": "spotify"   # Optional
    }
    
    Response:
    {
        "tracks": [
            {
                "original_url": "...",
                "title": "...",
                "artist": "...",
                "thumbnail_url": "...",
                "links": {...}
            },
            ...
        ],
        "success_count": 8,
        "failed_count": 2,
        "errors": [...]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return ResponseBuilder.build_error_response('Invalid JSON body', 400)
        
        urls = data.get('urls', [])
        
        # Validate
        if not urls or not isinstance(urls, list):
            return ResponseBuilder.build_error_response('Invalid request: urls array required', 400)
        
        if len(urls) > 10:
            return ResponseBuilder.build_error_response('Maximum 10 URLs allowed', 400)
        
        # Process each URL
        results = []
        errors = []
        success_count = 0
        
        for idx, url in enumerate(urls):
            try:
                # Parse URL
                parsed = URLParser.parse(url)
                if not parsed:
                    errors.append({
                        'index': idx,
                        'url': url,
                        'error': 'Unsupported URL format'
                    })
                    continue
                
                platform, track_id = parsed
                
                # Extract metadata
                metadata = None
                
                if platform == 'spotify':
                    metadata = spotify_extractor.get_track_metadata(track_id)
                elif platform == 'tidal':
                    metadata = web_scraper.scrape_tidal(track_id)
                    if not metadata:
                        metadata = tidal_extractor.get_track_metadata(track_id)
                elif platform == 'appleMusic':
                    metadata = web_scraper.scrape_apple_music(track_id)
                elif platform == 'amazonMusic':
                    metadata = web_scraper.scrape_amazon_music(track_id)
                elif platform == 'deezer':
                    metadata = universal_extractor.extract_from_deezer(track_id)
                elif platform == 'youtube':
                    metadata = universal_extractor.extract_from_youtube(track_id)
                
                if not metadata:
                    errors.append({
                        'index': idx,
                        'url': url,
                        'error': 'Track not found'
                    })
                    continue
                
                # Get Spotify cover
                artist = metadata['artist']
                title = metadata['title']
                isrc = metadata.get('isrc')
                
                spotify_cover_result = spotify_extractor.search_track(artist, title, isrc)
                if spotify_cover_result and spotify_cover_result.get('thumbnail'):
                    metadata['thumbnail'] = spotify_cover_result['thumbnail']
                    if not metadata.get('isrc') and spotify_cover_result.get('isrc'):
                        metadata['isrc'] = spotify_cover_result['isrc']
                
                # Search on all platforms
                links = {}
                
                # Spotify
                if platform != 'spotify':
                    if spotify_cover_result:
                        links['spotify'] = {
                            'url': spotify_cover_result['url'],
                            'entityUniqueId': f"SPOTIFY::TRACK::{spotify_cover_result['id']}"
                        }
                else:
                    links['spotify'] = {
                        'url': metadata['url'],
                        'entityUniqueId': f"SPOTIFY::TRACK::{metadata['id']}"
                    }
                
                # YouTube Music
                youtube_result = youtube_searcher.search(artist, title)
                if youtube_result:
                    links['youtubeMusic'] = {
                        'url': youtube_result['url'],
                        'entityUniqueId': f"YOUTUBE::VIDEO::{youtube_result.get('video_id', 'unknown')}"
                    }
                
                # Deezer
                deezer_result = deezer_searcher.search(artist, title, isrc)
                if deezer_result:
                    links['deezer'] = {
                        'url': deezer_result['url'],
                        'entityUniqueId': f"DEEZER::TRACK::{deezer_result.get('id', 'unknown')}"
                    }
                
                # TIDAL
                tidal_result = tidal_searcher.search(artist, title, isrc)
                if tidal_result:
                    links['tidal'] = {
                        'url': tidal_result['url'],
                        'entityUniqueId': f"TIDAL::TRACK::{tidal_result.get('id', 'unknown')}"
                    }
                
                # Apple Music
                apple_result = apple_music_searcher.search(artist, title)
                if apple_result:
                    links['appleMusic'] = {
                        'url': apple_result['url'],
                        'entityUniqueId': f"APPLEMUSIC::SONG::unknown"
                    }
                
                # Amazon Music
                amazon_result = amazon_music_searcher.search(artist, title)
                if amazon_result:
                    links['amazonMusic'] = {
                        'url': amazon_result['url'],
                        'entityUniqueId': f"AMAZONMUSIC::SONG::unknown"
                    }
                
                # Add to results
                results.append({
                    'original_url': url,
                    'title': metadata['title'],
                    'artist': metadata['artist'],
                    'thumbnail_url': metadata.get('thumbnail'),
                    'links': links
                })
                success_count += 1
                
            except Exception as e:
                print(f"[ERROR] Batch conversion error for URL {idx}: {str(e)}")
                errors.append({
                    'index': idx,
                    'url': url,
                    'error': str(e)
                })
        
        return jsonify({
            'tracks': results,
            'success_count': success_count,
            'failed_count': len(errors),
            'errors': errors
        }), 200
        
    except Exception as e:
        print(f"[ERROR] Batch conversion error: {str(e)}")
        return ResponseBuilder.build_error_response('Internal server error', 500)

@app.route('/v1/playlists', methods=['POST'])
def create_playlist():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    description = data.get('description')
    tracks = data.get('tracks', [])

    if not title:
        return ResponseBuilder.build_error_response('Missing title', 400)
    if not isinstance(tracks, list) or len(tracks) == 0:
        return ResponseBuilder.build_error_response('Tracks required', 400)
    if len(tracks) > Config.PLAYLIST_MAX_TRACKS:
        return ResponseBuilder.build_error_response('Too many tracks', 400)

    normalized_tracks = []
    for track in tracks:
        if not isinstance(track, dict):
            return ResponseBuilder.build_error_response('Invalid track data', 400)
        original_url = str(track.get('originalUrl', '')).strip()
        if not original_url:
            return ResponseBuilder.build_error_response('Track originalUrl required', 400)
        normalized_tracks.append({
            'title': str(track.get('title', '')).strip() or None,
            'artist': str(track.get('artist', '')).strip() or None,
            'originalUrl': original_url,
            'thumbnailUrl': track.get('thumbnailUrl'),
            'addedAt': track.get('addedAt')
        })

    playlist_id = None
    delete_token = secrets.token_urlsafe(24)
    with get_session() as session:
        for _ in range(5):
            candidate = secrets.token_urlsafe(8).replace('-', '').replace('_', '')
            if not session.query(Playlist).filter_by(id=candidate).first():
                playlist_id = candidate
                break
        if not playlist_id:
            return ResponseBuilder.build_error_response('Failed to create playlist', 500)

        expires_at = datetime.utcnow() + timedelta(days=Config.PLAYLIST_TTL_DAYS)
        playlist = Playlist(
            id=playlist_id,
            delete_token=delete_token,
            title=title,
            description=description,
            tracks=normalized_tracks,
            expires_at=expires_at
        )
        session.add(playlist)
        session.commit()

    return jsonify({
        'id': playlist_id,
        'deleteToken': delete_token,
        'expiresAt': expires_at.isoformat() + 'Z'
    }), 201

@app.route('/v1/playlists/<playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    with get_session() as session:
        playlist = session.query(Playlist).filter_by(id=playlist_id).first()
        if not playlist:
            return ResponseBuilder.build_error_response('Playlist not found', 404)
        if playlist.expires_at and playlist.expires_at < datetime.utcnow():
            session.delete(playlist)
            session.commit()
            return ResponseBuilder.build_error_response('Playlist expired', 404)

        return jsonify({
            'id': playlist.id,
            'title': playlist.title,
            'description': playlist.description,
            'tracks': playlist.tracks,
            'createdAt': playlist.created_at.isoformat() + 'Z',
            'updatedAt': playlist.updated_at.isoformat() + 'Z',
            'expiresAt': playlist.expires_at.isoformat() + 'Z' if playlist.expires_at else None
        }), 200

@app.route('/v1/playlists/<playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    token = request.args.get('token', '')
    if not token:
        return ResponseBuilder.build_error_response('Delete token required', 403)
    with get_session() as session:
        playlist = session.query(Playlist).filter_by(id=playlist_id).first()
        if not playlist:
            return ResponseBuilder.build_error_response('Playlist not found', 404)
        if playlist.delete_token != token:
            return ResponseBuilder.build_error_response('Invalid delete token', 403)
        session.delete(playlist)
        session.commit()
        return jsonify({'status': 'deleted'}), 200

def _process_music_link(music_url):
    """
    Internal function to process a music link and return all platform links
    Used by both /v1-alpha.1/links and /s/{encoded_url} endpoints
    Supports tracks, albums, and artists
    """
    # Parse URL to get platform, content ID, and content type
    parsed = URLParser.parse_with_type(music_url)
    
    if not parsed:
        # Log the failed URL for debugging
        print(f"[ERROR] Failed to parse URL: {music_url}")
        return ResponseBuilder.build_error_response(
            'Unsupported URL format. Supported platforms: Spotify, Apple Music, YouTube, Deezer, TIDAL, Amazon Music',
            400
        )
    
    platform, content_id, content_type = parsed
    
    # Route to appropriate processor based on content type
    if content_type == ContentType.TRACK:
        return _process_track(platform, content_id)
    elif content_type == ContentType.ALBUM:
        return _process_album(platform, content_id)
    elif content_type == ContentType.ARTIST:
        return _process_artist(platform, content_id)
    else:
        return ResponseBuilder.build_error_response(
            f'Unsupported content type: {content_type.value}',
            400
        )


def _process_track(platform: str, track_id: str):
    """Process a track URL and return all platform links"""
    # Extract metadata from source platform
    metadata = None
    
    if platform == 'spotify':
        metadata = spotify_extractor.get_track_metadata(track_id)
    elif platform == 'tidal':
        # Try web scraping first (more reliable than API with limited access)
        metadata = web_scraper.scrape_tidal(track_id)
        if not metadata:
            # Fallback to TIDAL API if scraping fails
            metadata = tidal_extractor.get_track_metadata(track_id)
        if not metadata:
            print(f"[ERROR] Tidal track not found: {track_id}")
            return ResponseBuilder.build_error_response(
                'TIDAL track not found. The track might be unavailable or the ID is incorrect.',
                404
            )
    elif platform == 'appleMusic':
        # Try web scraping for Apple Music
        metadata = web_scraper.scrape_apple_music(track_id)
    elif platform == 'amazonMusic':
        # Try web scraping for Amazon Music
        metadata = web_scraper.scrape_amazon_music(track_id)
    elif platform == 'deezer':
        metadata = universal_extractor.extract_from_deezer(track_id)
    elif platform == 'youtube':
        # YouTube extraction with API key
        metadata = universal_extractor.extract_from_youtube(track_id)
        if not metadata:
            return ResponseBuilder.build_error_response(
                'Could not extract track info from YouTube video. The video might not be a music track.',
                404
            )
    
    if not metadata:
        return ResponseBuilder.build_error_response(
            'Track not found. Please check the URL and try again.',
            404
        )
    
    # ALWAYS get cover from Spotify (regardless of input platform)
    # This ensures consistent, high-quality album art
    artist = metadata['artist']
    title = metadata['title']
    isrc = metadata.get('isrc')
    
    # Search on Spotify to get cover art
    spotify_cover_result = spotify_extractor.search_track(artist, title, isrc)
    if spotify_cover_result and spotify_cover_result.get('thumbnail'):
        # Override metadata thumbnail with Spotify's cover
        metadata['thumbnail'] = spotify_cover_result['thumbnail']
        # Also update ISRC if we didn't have it
        if not metadata.get('isrc') and spotify_cover_result.get('isrc'):
            metadata['isrc'] = spotify_cover_result['isrc']
    
    # Search on all other platforms
    links = {}
    
    # Always include source platform (but not Spotify yet, we handle it separately below)
    if platform != 'spotify':
        links[platform] = {
            'url': metadata['url'],
            'entityUniqueId': f"{platform.upper()}::TRACK::{metadata['id']}"
        }
    
    # Search on other platforms
    # Note: artist, title, isrc already defined above when getting Spotify cover
    
    # Spotify (if not source)
    if platform != 'spotify':
        # We already searched Spotify for the cover, reuse that result
        if spotify_cover_result:
            links['spotify'] = {
                'url': spotify_cover_result['url'],
                'entityUniqueId': f"SPOTIFY::TRACK::{spotify_cover_result['id']}"
            }
        else:
            # Fallback: search again if cover search failed
            spotify_result = spotify_extractor.search_track(artist, title, isrc)
            if spotify_result:
                links['spotify'] = {
                    'url': spotify_result['url'],
                    'entityUniqueId': f"SPOTIFY::TRACK::{spotify_result['id']}"
                }
    else:
        # Source is Spotify, just add it
        links['spotify'] = {
            'url': metadata['url'],
            'entityUniqueId': f"SPOTIFY::TRACK::{metadata['id']}"
        }
    
    # YouTube Music
    youtube_result = youtube_searcher.search(artist, title)
    if youtube_result:
        links['youtubeMusic'] = {
            'url': youtube_result['url'],
            'entityUniqueId': f"YOUTUBE::VIDEO::{youtube_result.get('video_id', 'unknown')}"
        }
        # Also add regular YouTube
        if 'youtube_url' in youtube_result:
            links['youtube'] = {
                'url': youtube_result['youtube_url'],
                'entityUniqueId': f"YOUTUBE::VIDEO::{youtube_result.get('video_id', 'unknown')}"
            }
    
    # Deezer
    deezer_result = deezer_searcher.search(artist, title, isrc)
    if deezer_result:
        links['deezer'] = {
            'url': deezer_result['url'],
            'entityUniqueId': f"DEEZER::TRACK::{deezer_result.get('id', 'unknown')}"
        }
    
    # TIDAL
    tidal_result = tidal_searcher.search(artist, title, isrc)
    if tidal_result:
        links['tidal'] = {
            'url': tidal_result['url'],
            'entityUniqueId': f"TIDAL::TRACK::{tidal_result.get('id', 'unknown')}"
        }
    
    # Apple Music
    apple_result = apple_music_searcher.search(artist, title)
    if apple_result:
        links['appleMusic'] = {
            'url': apple_result['url'],
            'entityUniqueId': f"APPLEMUSIC::SONG::unknown"
        }
    
    # Amazon Music
    amazon_result = amazon_music_searcher.search(artist, title)
    if amazon_result:
        links['amazonMusic'] = {
            'url': amazon_result['url'],
            'entityUniqueId': f"AMAZONMUSIC::SONG::unknown"
        }
    
    # Build Odesli-compatible response
    response = ResponseBuilder.build_response(metadata, links, platform, ContentType.TRACK)
    
    return jsonify(response)


def _process_album(platform: str, album_id: str):
    """Process an album URL and return all platform links"""
    # Extract metadata from source platform
    metadata = None
    
    if platform == 'spotify':
        metadata = spotify_extractor.get_album_metadata(album_id)
    elif platform == 'tidal':
        metadata = tidal_extractor.get_album_metadata(album_id)
    # TODO: Add other platforms (Apple Music, Deezer, etc.)
    
    if not metadata:
        return ResponseBuilder.build_error_response(
            'Album not found. Please check the URL and try again.',
            404
        )
    
    # Get album info
    artist = metadata['artist']
    album_title = metadata.get('album') or metadata.get('title')
    
    # Search on all platforms
    links = {}
    
    # Always include source platform
    if platform == 'spotify':
        links['spotify'] = {
            'url': metadata['url'],
            'entityUniqueId': f"SPOTIFY::ALBUM::{metadata['id']}"
        }
    elif platform == 'tidal':
        links['tidal'] = {
            'url': metadata['url'],
            'entityUniqueId': f"TIDAL::ALBUM::{metadata['id']}"
        }
    
    # Search on Spotify if not source (for consistent cover art)
    if platform != 'spotify':
        spotify_result = spotify_extractor.search_album(artist, album_title)
        if spotify_result:
            links['spotify'] = {
                'url': spotify_result['url'],
                'entityUniqueId': f"SPOTIFY::ALBUM::{spotify_result['id']}"
            }
            # Use Spotify's cover art
            if spotify_result.get('thumbnail'):
                metadata['thumbnail'] = spotify_result['thumbnail']
    
    # Search on other platforms using generic search
    from urllib.parse import quote
    
    # YouTube Music - Search for album
    youtube_search_query = quote(f"{artist} {album_title}")
    links['youtubeMusic'] = {
        'url': f"https://music.youtube.com/search?q={youtube_search_query}",
        'entityUniqueId': f"YOUTUBEMUSIC::ALBUM::search"
    }
    
    # YouTube - Search for album
    links['youtube'] = {
        'url': f"https://www.youtube.com/results?search_query={youtube_search_query}",
        'entityUniqueId': f"YOUTUBE::ALBUM::search"
    }
    
    # Deezer - Search for album
    deezer_search_query = quote(f"{artist} {album_title}")
    links['deezer'] = {
        'url': f"https://www.deezer.com/search/{deezer_search_query}/album",
        'entityUniqueId': f"DEEZER::ALBUM::search"
    }
    
    # Apple Music - Search for album
    apple_search_query = quote(f"{artist} {album_title}")
    links['appleMusic'] = {
        'url': f"https://music.apple.com/search?term={apple_search_query}",
        'entityUniqueId': f"APPLEMUSIC::ALBUM::search"
    }
    
    # Amazon Music - Search for album
    amazon_search_query = quote(f"{artist} {album_title}")
    links['amazonMusic'] = {
        'url': f"https://music.amazon.com/search/{amazon_search_query}",
        'entityUniqueId': f"AMAZONMUSIC::ALBUM::search"
    }
    
    # Build Odesli-compatible response
    response = ResponseBuilder.build_response(metadata, links, platform, ContentType.ALBUM)
    
    return jsonify(response)


def _process_artist(platform: str, artist_id: str):
    """Process an artist URL and return all platform links"""
    # Extract metadata from source platform
    metadata = None
    
    if platform == 'spotify':
        metadata = spotify_extractor.get_artist_metadata(artist_id)
    elif platform == 'tidal':
        metadata = tidal_extractor.get_artist_metadata(artist_id)
    # TODO: Add other platforms (Apple Music, Deezer, etc.)
    
    if not metadata:
        return ResponseBuilder.build_error_response(
            'Artist not found. Please check the URL and try again.',
            404
        )
    
    # Get artist name
    artist_name = metadata.get('name') or metadata.get('artist')
    
    # Search on all platforms
    links = {}
    
    # Always include source platform
    if platform == 'spotify':
        links['spotify'] = {
            'url': metadata['url'],
            'entityUniqueId': f"SPOTIFY::ARTIST::{metadata['id']}"
        }
    elif platform == 'tidal':
        links['tidal'] = {
            'url': metadata['url'],
            'entityUniqueId': f"TIDAL::ARTIST::{metadata['id']}"
        }
    
    # Search on Spotify if not source
    if platform != 'spotify':
        spotify_result = spotify_extractor.search_artist(artist_name)
        if spotify_result:
            links['spotify'] = {
                'url': spotify_result['url'],
                'entityUniqueId': f"SPOTIFY::ARTIST::{spotify_result['id']}"
            }
            # Use Spotify's artist image
            if spotify_result.get('thumbnail'):
                metadata['thumbnail'] = spotify_result['thumbnail']
    
    # Search on other platforms using generic search
    # Most platforms don't have dedicated artist pages, so we create search links
    
    # YouTube - Search for artist channel
    from urllib.parse import quote
    youtube_search_query = quote(f"{artist_name} official")
    links['youtube'] = {
        'url': f"https://www.youtube.com/results?search_query={youtube_search_query}",
        'entityUniqueId': f"YOUTUBE::ARTIST::search"
    }
    
    # YouTube Music - Search for artist
    links['youtubeMusic'] = {
        'url': f"https://music.youtube.com/search?q={youtube_search_query}",
        'entityUniqueId': f"YOUTUBEMUSIC::ARTIST::search"
    }
    
    # Deezer - Search for artist
    deezer_search_query = quote(artist_name)
    links['deezer'] = {
        'url': f"https://www.deezer.com/search/{deezer_search_query}/artist",
        'entityUniqueId': f"DEEZER::ARTIST::search"
    }
    
    # Apple Music - Search for artist
    apple_search_query = quote(artist_name)
    links['appleMusic'] = {
        'url': f"https://music.apple.com/search?term={apple_search_query}",
        'entityUniqueId': f"APPLEMUSIC::ARTIST::search"
    }
    
    # Amazon Music - Search for artist
    amazon_search_query = quote(artist_name)
    links['amazonMusic'] = {
        'url': f"https://music.amazon.com/search/{amazon_search_query}",
        'entityUniqueId': f"AMAZONMUSIC::ARTIST::search"
    }
    
    # Build Odesli-compatible response
    response = ResponseBuilder.build_response(metadata, links, platform, ContentType.ARTIST)
    
    return jsonify(response)

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    print(f"🎵 UniTune Music Link API starting...")
    print(f"📍 Port: {Config.PORT}")
    print(f"✅ Spotify: Configured")
    print(f"{'✅' if Config.YOUTUBE_API_KEY else '⚠️ '} YouTube: {'Configured' if Config.YOUTUBE_API_KEY else 'Not configured (search links only)'}")
    print(f"\n🚀 Server running at http://localhost:{Config.PORT}")
    print(f"📖 API Endpoint: http://localhost:{Config.PORT}/v1-alpha.1/links?url=YOUR_MUSIC_URL")
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )
