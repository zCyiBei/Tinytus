from io import BytesIO
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from PIL import Image, ImageOps
from mutagen.id3 import ID3, APIC, error as ID3Error
from mutagen.flac import FLAC, Picture

class ArtworkDownloader:
    
    MAX_IMAGE_SIZE = 15 * 1024 * 1024
    
    SUPPORTED_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
    
    def __init__(self):
        pass
        
    def download_artwork(
        self,
        image_url: str,
        title: str
    ) -> Dict[str, Any]:
        
        try:
            if not isinstance(image_url, str) or not image_url.strip():
                raise ValueError("Artwork URL cannot be empty")
            
            if not isinstance(title, str) or not title.strip():
                raise ValueError("Song title cannot be empty")
            
            parsed_url = urlparse(image_url)
            
            if parsed_url.scheme not in ("http", "https"):
                raise ValueError("Invalid artwork URL")
            
            request = Request(
                image_url,
                headers={"User-Agent": "TinyTUS/1.0"}
            )
            
            with urlopen(request, timeout=15) as response:
                
                content_type = response.headers.get(
                    "Content-Type", ""
                ).split(";")[0].lower()
                
                if content_type not in self.SUPPORTED_TYPES:
                    raise ValueError(
                        f"Unsupported image type: {content_type}"
                    )
                    
                image_data = response.read(self.MAX_IMAGE_SIZE + 1)
                
            if len(image_data) > self.MAX_IMAGE_SIZE:
                raise ValueError("Artwork image exceeds 15 MB")
            
            if not image_data:
                raise ValueError("Downloaded artwork is empty")
            
            with Image.open(BytesIO(image_data)) as image:
                
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")
                
                output = BytesIO()
                
                image.save(
                    output,
                    format="JPEG",
                    quality=95,
                    optimize=True
                )
                
                jpeg_data = output.getvalue()
                
            return {
                "success": True,
                "image_data": jpeg_data,
                "size": len(jpeg_data),
                "format": "JPEG",
            }
            
        except (
            ValueError,
            OSError,
            URLError,
            HTTPError
        ) as error:
            
            return {
                "success": False,
                "error": str(error),
            }
            
    @staticmethod
    def embed_artwork(
        audio_path: Path,
        image_data: bytes
    ) -> Dict[str, Any]:
        
        try:
            audio_path = Path(audio_path)
            
            if not audio_path.is_file():
                raise FileNotFoundError(
                    f"Audio file not found: {audio_path}"
                )
                
            if not isinstance(image_data, bytes) or not image_data:
                raise ValueError("Artwork image is empty or invalid")
            
            with Image.open(BytesIO(image_data)) as image:
                width, height = image.size
                
            extension = audio_path.suffix.lower()
            
            if extension == ".mp3":
                
                try:
                    audio = ID3(audio_path)
                except ID3Error:
                    audio = ID3()
                    
                audio.delall("APIC")
                
                audio.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=image_data,
                    )
                )
                
                audio.save(audio_path, v2_version=3)
                
            elif extension == ".flac":
                
                audio = FLAC(audio_path)
                
                picture = Picture()
                picture.type = 3
                picture.mime = "image/jpeg"
                picture.desc = "Cover"
                picture.width = width
                picture.height = height
                picture.depth = 24
                picture.data = image_data
                
                audio.clear_pictures()
                audio.add_picture(picture)
                audio.save()
                
            else:
                raise ValueError(
                    "Only MP3 and FLAC files are supported"
                )
                
            return {
                "success": True,
                "audio_file": audio_path,
            }
            
        except (OSError, ValueError, ID3Error) as error:
            
            return {
                "success": False,
                "error": str(error),
            }