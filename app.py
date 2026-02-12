"""
UniTune Music Link API
Self-hosted Odesli/SongLink alternative
"""
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import secrets
from flask_cors import CORS
from config import Config
from utils.url_parser import URLParser
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

Base.metadata.create_all(bind=engine)

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
    
    Returns JSON response. Frontend (Cloudflare Worker) handles HTML rendering.
    """
    try:
        # Decode base64 identifier
        decoded = LinkEncoder.decode(encoded_id)
        if not decoded:
            return ResponseBuilder.build_error_response('Invalid share link format', 400)
        
        platform, link_type, track_id = decoded
        
        # Reconstruct URL for processing
        platform_urls = {
            'spotify': f'https://open.spotify.com/track/{track_id}',
            'tidal': f'https://tidal.com/track/{track_id}',
            'appleMusic': f'https://music.apple.com/song/{track_id}',
            'youtube': f'https://youtube.com/watch?v={track_id}',
            'youtubeMusic': f'https://music.youtube.com/watch?v={track_id}',
            'deezer': f'https://deezer.com/track/{track_id}',
            'amazonMusic': f'https://music.amazon.com/tracks/{track_id}'
        }
        
        reconstructed_url = platform_urls.get(platform)
        if not reconstructed_url:
            return ResponseBuilder.build_error_response(f'Unsupported platform: {platform}', 400)
        
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
    """
    # Parse URL to get platform and track ID
    parsed = URLParser.parse(music_url)
    
    if not parsed:
        # Log the failed URL for debugging
        print(f"[ERROR] Failed to parse URL: {music_url}")
        return ResponseBuilder.build_error_response(
            'Unsupported URL format. Supported platforms: Spotify, Apple Music, YouTube, Deezer, TIDAL, Amazon Music',
            400
        )
    
    platform, track_id = parsed
    
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
    response = ResponseBuilder.build_response(metadata, links, platform)
    
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
