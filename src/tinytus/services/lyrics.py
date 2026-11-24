from typing import Any, Dict, Optional
import requests
from tinytus.config.settings import Config

class LyricsDownloader:
    
    def __init__(self):
        self.search_url = Config.LYRICS_SEARCH_URL
        self.api_url = Config.LYRICS_API_URL
        
    def search_lyrics(
        self,
        title: str,
        artist: str,
        album: Optional[str] = None,
        duration: Optional[float] = None,
    ) -> Dict[str, Any]:
        
        try:
            if not title or not title.strip():
                raise ValueError("Song title cannot be empty")
            
            if not artist or not artist.strip():
                raise ValueError("Artist cannot be empty")
            
            params = {
                "track_name": title.strip(),
                "artist_name": artist.strip(),
            }
            
            if album:
                params["album_name"] = album.strip()
                
            if duration is not None:
                params["duration"] = int(duration)
                
            response = requests.get(
                self.search_url,
                params=params,
                timeout=15,
            )
            
            response.raise_for_status()
            
            results = response.json()
            
            if not results:
                return {
                    "success": False,
                    "error": "No lyrics found",
                }
                
            lyrics = self._select_lyrics(results)
            
            if lyrics is None:
                return {
                    "success": False,
                    "error": "No usable lyrics found",
                }
                
            return {
                "success": True,
                "title": lyrics.get("trackName"),
                "artist": lyrics.get("artistName"),
                "album": lyrics.get("albumName"),
                "duration": lyrics.get("duration"),
                "plain_lyrics": lyrics.get("plainLyrics"),
                "synced_lyrics": lyrics.get("syncedLyrics"),
                "instrumental": lyrics.get("instrumental", False),
            }
            
        except requests.RequestException as error:
            return {
                "success": False,
                "error": str(error),
            }
            
        except (ValueError, TypeError) as error:
            return {
                "success": False,
                "error": str(error),
            }
            
    @staticmethod
    def _select_lyrics(results: list) -> Optional[Dict[str, Any]]:
        
        if not isinstance(results, list):
            return None
        
        for lyrics in results:
            if lyrics.get("syncedLyrics"):
                return lyrics
            
        for lyrics in results:
            if lyrics.get("plainLyrics"):
                return lyrics
            
        for lyrics in results:
            if lyrics.get("instrumental"):
                return lyrics
            
        return None