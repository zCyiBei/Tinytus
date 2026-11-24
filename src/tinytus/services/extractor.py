import yt_dlp
from pathlib import Path
from typing import Any, Dict
from tinytus.config.settings import Config

class AudioExtractor:
    
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR
        
    def extract_audio(
        self,
        url: str,
        format_name: str = Config.DEFAULT_FORMAT
    ) -> Dict[str, Any]:
        
        try:
            self._validate_format(format_name)
            
            self.download_dir.mkdir(parents=True, exist_ok=True)
            
            options = self._build_options()
            
            with yt_dlp.YoutubeDL(options) as ydl:
                
                info = ydl.extract_info(url, download=True)
                
                if not info:
                    raise ValueError("No information found")
                
                if info.get("_type") == "playlist":
                    entries = [
                        entry for entry in info.get("entries", [])
                        if entry
                    ]
                    
                    if not entries:
                        raise ValueError("No search results found")
                    
                    info = entries[0]
                    
                    if info.get("_type") == "url":
                        info = ydl.extract_info(
                            info.get("url") or info.get("id"),
                            download=False
                        )
                        
                downloads = info.get("requested_downloads", [])
                
                if downloads and downloads[0].get("filepath"):
                    file_path = Path(downloads[0]["filepath"])
                else:
                    file_path = Path(ydl.prepare_filename(info))
                    
            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Downloaded file not found: {file_path}"
                )
                
            return {
                "success": True,
                "id": info.get("id"),
                "title": info.get("title", "Unknown"),
                "artist": (
                    info.get("artist")
                    or info.get("creator")
                    or info.get("uploader")
                ),
                "album": info.get("album"),
                "thumbnail": info.get("thumbnail"),
                "webpage_url": info.get("webpage_url"),
                "filename": file_path.name,
                "url": url,
                "duration": info.get("duration", 0),
                "file_path": file_path,
            }
            
        except yt_dlp.utils.DownloadError as error:
            return {
                "success": False,
                "error": str(error),
                "url": url,
            }
            
        except (ValueError, OSError, KeyError, TypeError) as error:
            return {
                "success": False,
                "error": str(error),
                "url": url,
            }
            
    @staticmethod
    def _validate_format(format_name: str) -> str:
        
        if not isinstance(format_name, str):
            raise ValueError("Format must be a string")
        
        format_name = format_name.lower()
        
        if format_name not in Config.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {format_name}. "
                f"Supported formats: {Config.SUPPORTED_FORMATS}"
            )
            
        return format_name
    
    def _build_options(self) -> dict:
        
        options = Config.YTDLP_OPTIONS.copy()
        
        options["outtmpl"] = str(
            self.download_dir / "%(title)s.%(ext)s"
        )
        
        return options