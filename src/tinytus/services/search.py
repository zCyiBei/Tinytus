from typing import Dict, Any
from urllib.parse import urlparse

class AudioSearch:
    
    def search(self, query: str) -> Dict[str, Any]:
        
        if not isinstance(query, str) or not query.strip():
            return {
                "success": False,
                "error": "Search query cannot be empty"
            }
            
        query = query.strip()
        
        if self._is_spotify_url(query):
            return {
                "success": False,
                "error": (
                    "Spotify URL resolution is not implemented yet. "
                    "Use the artist and song title instead."
                )
            }
            
        if self._is_url(query):
            return {
                "success": False,
                "error": "Unsupported URL. Use a song title or artist name."
            }
            
        return {
            "success": True,
            "query": query,
            "search_query": f"ytsearch1:{query}"
        }
        
    @staticmethod
    def _is_spotify_url(url: str) -> bool:
        
        parsed_url = urlparse(url)
        
        return (
            parsed_url.hostname in ("open.spotify.com", "www.open.spotify.com")
        )
        
    @staticmethod
    def _is_url(value: str) -> bool:
        
        parsed_url = urlparse(value)
        
        return parsed_url.scheme in ("http", "https")