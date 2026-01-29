"""
UniTune Music Link API
Self-hosted Odesli/SongLink alternative
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from utils.url_parser import URLParser
from utils.response_builder import ResponseBuilder
from extractors.spotify import SpotifyExtractor
from extractors.tidal import TidalExtractor
from extractors.universal import UniversalExtractor
from searchers.youtube import YouTubeSearcher
from searchers.deezer import DeezerSearcher
from searchers.tidal import TidalSearcher
from searchers.apple_music import AppleMusicSearcher
from searchers.amazon_music import AmazonMusicSearcher

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Validate configuration
Config.validate()

# Initialize extractors and searchers
spotify_extractor = SpotifyExtractor()
tidal_extractor = TidalExtractor()
universal_extractor = UniversalExtractor()
youtube_searcher = YouTubeSearcher()
deezer_searcher = DeezerSearcher()
tidal_searcher = TidalSearcher()  # Uses its own TidalExtractor instance
apple_music_searcher = AppleMusicSearcher()
amazon_music_searcher = AmazonMusicSearcher()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'version': '1.0.0',
        'spotify_configured': bool(Config.SPOTIFY_CLIENT_ID),
        'youtube_configured': bool(Config.YOUTUBE_API_KEY)
    })

@app.route('/s/<path:encoded_url>', methods=['GET'])
def handle_share_link(encoded_url):
    """
    Handle UniTune share links: /s/{encodedUrl}
    Decodes the URL and returns JSON response
    Frontend (Cloudflare Worker) handles HTML rendering
    """
    from urllib.parse import unquote
    
    # Decode the URL
    try:
        decoded_url = unquote(encoded_url)
        # Process the link and return JSON
        return _process_music_link(decoded_url)
    except Exception as e:
        return ResponseBuilder.build_error_response(f'Invalid share link: {str(e)}', 400)

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

def _process_music_link(music_url):
    """
    Internal function to process a music link and return all platform links
    Used by both /v1-alpha.1/links and /s/{encoded_url} endpoints
    """
    # Parse URL to get platform and track ID
    parsed = URLParser.parse(music_url)
    
    if not parsed:
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
        # TIDAL as input is not supported due to API limitations
        # TIDAL's public API requires authentication and our credentials
        # don't have the required access tier for track metadata
        return ResponseBuilder.build_error_response(
            'TIDAL URLs are currently not supported as input due to API limitations. Please use Spotify, Deezer, or YouTube URLs instead.',
            400
        )
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
    else:
        # Apple Music, Amazon Music don't have public APIs
        return ResponseBuilder.build_error_response(
            f'{platform} URLs are not supported as input. Please use Spotify, Deezer, or YouTube URLs.',
            400
        )
    
    if not metadata:
        return ResponseBuilder.build_error_response(
            'Track not found. Please check the URL and try again.',
            404
        )
    
    # Search on all other platforms
    links = {}
    
    # Always include source platform
    links[platform] = {
        'url': metadata['url'],
        'entityUniqueId': f"{platform.upper()}::TRACK::{metadata['id']}"
    }
    
    # Search on other platforms
    artist = metadata['artist']
    title = metadata['title']
    isrc = metadata.get('isrc')
    
    # Spotify (if not source)
    if platform != 'spotify':
        spotify_result = spotify_extractor.search_track(artist, title, isrc)
        if spotify_result:
            links['spotify'] = {
                'url': spotify_result['url'],
                'entityUniqueId': f"SPOTIFY::TRACK::{spotify_result['id']}"
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
