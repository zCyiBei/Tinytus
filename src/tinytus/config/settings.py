from pathlib import Path

class Config:
    
    # Project base directory
    BASE_DIR = Path(__file__).resolve().parents[3]
    
    # Working directories
    DOWNLOAD_DIR = BASE_DIR / "temp"
    CONVERT_DIR = BASE_DIR / "converted"
    
    # Audio formats
    DEFAULT_FORMAT = "mp3"
    SUPPORTED_FORMATS = ("mp3", "flac")
    
    # Supported files extensions
    ALLOWED_EXTENSIONS = {".mp3", ".flac", ".wav", ".m4a", ".webm"}
    
    # FFmpeg configuration
    FFMPEG_PATH = str(
        BASE_DIR.parent / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
        )
    YTDLP_PATH = "yt-dlp"
    
    # Default yt-dlp options
    YTDLP_OPTIONS = {
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    
    # Lyrics API endpoints
    LYRICS_API_URL = "https://lrclib.net/api/get"
    LYRICS_SEARCH_URL = "https://lrclib.net/api/search"