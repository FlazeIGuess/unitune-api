# Supported Platforms

## Input Platforms (Source URLs)

These platforms can be used as **input** to convert to other platforms:

| Platform | Status | Notes |
|----------|--------|-------|
| ✅ **Spotify** | Fully Supported | Official API with full metadata |
| ✅ **Deezer** | Fully Supported | Public API, no authentication needed |
| ✅ **YouTube** | Supported | Requires YouTube API key |
| ✅ **YouTube Music** | Supported | Same as YouTube |
| ❌ **TIDAL** | Not Supported | API requires special access tier |
| ❌ **Apple Music** | Not Supported | No public API available |
| ❌ **Amazon Music** | Not Supported | No public API available |

## Output Platforms (Target Links)

These platforms are available as **output** (generated links):

| Platform | Status | Link Type | Notes |
|----------|--------|-----------|-------|
| ✅ **Spotify** | Fully Supported | Direct Track Link | Official API |
| ✅ **Apple Music** | Supported | Search Link | No API, uses search |
| ✅ **YouTube Music** | Supported | Direct Video Link | YouTube API |
| ✅ **YouTube** | Supported | Direct Video Link | YouTube API |
| ✅ **Deezer** | Fully Supported | Direct Track Link | Public API |
| ✅ **TIDAL** | Supported | Search Link | API limitations* |
| ✅ **Amazon Music** | Supported | Search Link | No API, uses search |

\* TIDAL API requires special access tier. We generate search links instead of direct track links.

## Examples

### ✅ Supported Input URLs

```bash
# Spotify
https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp

# Deezer
https://www.deezer.com/track/2947340

# YouTube
https://www.youtube.com/watch?v=l7MaKmKJqoc
https://music.youtube.com/watch?v=l7MaKmKJqoc
```

### ❌ Unsupported Input URLs

```bash
# TIDAL (not supported as input)
https://tidal.com/track/192227506

# Apple Music (not supported as input)
https://music.apple.com/us/album/mr-brightside/1440873107?i=1440873426

# Amazon Music (not supported as input)
https://music.amazon.com/albums/B000QKGGQK
```

## Why is TIDAL not supported as input?

TIDAL's Developer API has **access tier limitations**:

1. **Basic Tier** (what we have):
   - ✅ OAuth2 authentication works
   - ❌ Cannot access track metadata
   - ❌ Cannot search catalog
   - Error: `"Client does not have required access tier"`

2. **Advanced Tier** (not available):
   - ✅ Full catalog access
   - ✅ Track metadata
   - ✅ Search functionality
   - ⚠️ Only available to selected partners

### Workaround

TIDAL is still available as an **output** platform:
- We generate search links: `https://listen.tidal.com/search?q=Artist+Title`
- User clicks → TIDAL opens → Shows search results → One click to play
- Good user experience with minimal friction

## API Response Format

### Successful Conversion

```json
{
  "entityUniqueId": "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp",
  "linksByPlatform": {
    "spotify": {
      "url": "https://open.spotify.com/track/3n3Ppam7vgaVa1iaRUc9Lp",
      "entityUniqueId": "SPOTIFY::TRACK::3n3Ppam7vgaVa1iaRUc9Lp"
    },
    "tidal": {
      "url": "https://listen.tidal.com/search?q=The%20Killers%20Mr.%20Brightside",
      "entityUniqueId": "TIDAL::TRACK::search"
    },
    ...
  }
}
```

### Error Response (Unsupported Platform)

```json
{
  "error": "TIDAL URLs are currently not supported as input due to API limitations. Please use Spotify, Deezer, or YouTube URLs instead."
}
```

## Future Plans

### Possible Solutions for TIDAL Input

1. **Apply for Advanced API Access**
   - Contact: developer@tidal.com
   - Explain use case
   - Wait for approval (no guarantee)

2. **Web Scraping** (not recommended)
   - Against TIDAL Terms of Service
   - Unreliable and can break anytime
   - Legal risks

3. **User-provided TIDAL credentials**
   - Requires user login
   - Complex OAuth flow
   - Privacy concerns

For now, we recommend users to:
- Use Spotify, Deezer, or YouTube as input
- TIDAL links will be generated as output (search links)

## Summary

**Input**: Spotify, Deezer, YouTube ✅  
**Output**: All platforms including TIDAL ✅  
**TIDAL as input**: Not supported due to API limitations ❌

---

Last updated: January 29, 2026
