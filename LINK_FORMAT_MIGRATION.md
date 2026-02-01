# Share Link Format

## Overview

UniTune API uses a secure, Base64-encoded link format to prevent browser phishing warnings while maintaining backward compatibility with legacy URL-encoded links.

## Problem Statement

Previous share links contained URL-encoded platform URLs in the path:

```
https://unitune.art/s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410
```

Browser security systems detected domain names like `tidal.com` in the URL path and flagged these as potential phishing sites, preventing users from accessing shared links.

## Solution

New Base64-encoded link format:

```
https://unitune.art/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw
```

### Benefits

- No domain names in URL path (prevents phishing warnings)
- 20% shorter URLs
- Fully backward compatible with legacy links
- Platform-agnostic and extensible

## Technical Details

### Encoding Schema

**Format:** `{platform}:{type}:{id}`

**Examples:**
```
spotify:track:3n3Ppam7vgaVa1iaRUc9Lp  → c3BvdGlmeTp0cmFjazozbjNQcGFtN3ZnYVZhMWlhUlVjOUxw
tidal:track:258735410                → dGlkYWw6dHJhY2s6MjU4NzM1NDEw
appleMusic:track:1440857781          → YXBwbGVNdXNpYzp0cmFjazoxNDQwODU3Nzgx
youtube:track:dQw4w9WgXcQ             → eW91dHViZTp0cmFjazpkUXc0dzlXZ1hjUQ
```

### Supported Platforms

| Platform | Identifier | Example Track ID |
|----------|-----------|-------------------|
| Spotify | `spotify` | `3n3Ppam7vgaVa1iaRUc9Lp` |
| TIDAL | `tidal` | `258735410` |
| Apple Music | `appleMusic` | `1440857781` |
| YouTube | `youtube` | `dQw4w9WgXcQ` |
| YouTube Music | `youtubeMusic` | `dQw4w9WgXcQ` |
| Deezer | `deezer` | `123456789` |
| Amazon Music | `amazonMusic` | `B08XYZ123` |

## API Behavior

### Endpoint: `/s/{encoded_id}`

The endpoint automatically detects and supports both formats:

#### New Format (Base64-encoded)
```
GET /s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw
```

Decodes to: `tidal:track:258735410`

#### Legacy Format (URL-encoded)
```
GET /s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410
```

Decodes to: `https://tidal.com/track/258735410`

### Response Format

Both formats return the same response structure:

```json
{
  "entityUniqueId": "TIDAL::TRACK::258735410",
  "userCountry": "US",
  "pageUrl": "https://unitune.art/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw",
  "linksByPlatform": {
    "spotify": {
      "url": "https://open.spotify.com/track/...",
      "entityUniqueId": "SPOTIFY::TRACK::..."
    },
    "tidal": {
      "url": "https://tidal.com/track/258735410",
      "entityUniqueId": "TIDAL::TRACK::258735410"
    }
  },
  "entitiesByUniqueId": {
    "TIDAL::TRACK::258735410": {
      "id": "258735410",
      "type": "song",
      "title": "Song Title",
      "artistName": "Artist Name",
      "thumbnailUrl": "https://...",
      "apiProvider": "tidal"
    }
  }
}
```

**Note:** The `pageUrl` field always contains the new Base64 format.

## Client Integration

### Python (Backend)

```python
from utils.link_encoder import LinkEncoder

# Create a share link
platform = 'spotify'
track_id = '3n3Ppam7vgaVa1iaRUc9Lp'

# Method 1: Encode ID only
encoded_id = LinkEncoder.encode(platform, track_id, 'track')
share_url = f"https://unitune.art/s/{encoded_id}"

# Method 2: Complete URL
share_url = LinkEncoder.create_share_url(
    'https://unitune.art',
    platform,
    track_id,
    'track'
)
```

### Flutter/Dart

```dart
import 'dart:convert';

String createShareLink(String platform, String trackId) {
  // Format: platform:type:id
  String identifier = '$platform:track:$trackId';
  
  // Base64 encode (URL-safe)
  String encoded = base64Url.encode(utf8.encode(identifier));
  
  // Remove padding
  encoded = encoded.replaceAll('=', '');
  
  return 'https://unitune.art/s/$encoded';
}

// Example
String shareLink = createShareLink('spotify', '3n3Ppam7vgaVa1iaRUc9Lp');
// Result: https://unitune.art/s/c3BvdGlmeTp0cmFjazozbjNQcGFtN3ZnYVZhMWlhUlVjOUxw
```

### JavaScript/TypeScript

```javascript
function createShareLink(platform, trackId, type = 'track') {
  // Format: platform:type:id
  const identifier = `${platform}:${type}:${trackId}`;
  
  // Base64 encode (URL-safe)
  const encoded = btoa(identifier)
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
  
  return `https://unitune.art/s/${encoded}`;
}

// Example
const shareLink = createShareLink('spotify', '3n3Ppam7vgaVa1iaRUc9Lp');
```

## Backward Compatibility

The API automatically supports legacy links with no changes required:

```dart
// Both formats work
String newLink = 'https://unitune.art/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw';
String oldLink = 'https://unitune.art/s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410';

// Both return the same response
```

## Testing

**Test 1: New Format**
```bash
curl "http://localhost:10000/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw"
```

**Test 2: Legacy Format**
```bash
curl "http://localhost:10000/s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410"
```

**Test 3: API Endpoint**
```bash
curl "http://localhost:10000/v1-alpha.1/links?url=https://tidal.com/track/258735410"
```

All three should work and return similar responses.

## Migration Guide

### For Existing Applications

1. **No immediate changes required** - The API is fully backward compatible
2. **Update link generation** - Use new format for newly created links
3. **Test both formats** - Verify old and new links work correctly
4. **Deploy** - No downtime required

### Recommended Steps

1. Update your client to generate new format links
2. Test with both old and new links
3. Monitor for any issues
4. Legacy support remains active indefinitely

## Examples

### Before (Legacy)
```
URL: https://unitune.art/s/https%3A%2F%2Ftidal.com%2Ftrack%2F258735410
Length: 68 characters
Issue: Contains "tidal.com" → Phishing warning
```

### After (New)
```
URL: https://unitune.art/s/dGlkYWw6dHJhY2s6MjU4NzM1NDEw
Length: 54 characters
Issue: None → No warnings
```

**Improvement:** 20% shorter + no phishing warnings

---

Built with Flask and Python
