from typing import Any
from urllib.parse import urlparse
from tinytus.config.settings import Config
from tinytus.services.search import AudioSearch
from tinytus.services.extractor import AudioExtractor
from tinytus.services.converter import AudioConverter
from tinytus.services.storage import AudioStorage
from tinytus.services.artwork import ArtworkDownloader
from tinytus.services.metadata import AudioMetadata
from tinytus.services.lyrics import LyricsDownloader
from tinytus.services.title_cleaner import TitleCleaner

class AudioManager:
    
    def __init__(self):
        self.search = AudioSearch()
        self.extractor = AudioExtractor()
        self.converter = AudioConverter()
        self.storage = AudioStorage()
        self.artwork = ArtworkDownloader()
        self.metadata = AudioMetadata()
        self.lyrics = LyricsDownloader()
        self.title_cleaner = TitleCleaner()
        self.storage.create_directories()
        
    def process_audio(
        self,
        query: str,
        output_format: str = Config.DEFAULT_FORMAT
    ) -> dict[str, Any]:
        
        if not isinstance(query, str) or not query.strip():
            return {
                "success": False,
                "error": "Search query cannot be empty",
            }
            
        query = query.strip()
        
        try:
            output_format = self.converter._validate_format(
                output_format
            )
        except ValueError as error:
            return {
                "success": False,
                "error": str(error),
            }
            
        parsed_url = urlparse(query)
        
        if parsed_url.hostname in (
            "open.spotify.com",
            "www.open.spotify.com",
        ):
            search_result = self.search.search(query)
            
            if not search_result["success"]:
                return search_result
            
            extraction_query = search_result["search_query"]
            
        elif parsed_url.scheme in ("http", "https"):
            extraction_query = query
            
        else:
            search_result = self.search.search(query)
            
            if not search_result["success"]:
                return search_result
            
            extraction_query = search_result["search_query"]
            
        extraction_result = self.extractor.extract_audio(
            extraction_query,
            output_format
        )
        
        if not extraction_result["success"]:
            return extraction_result
        
        input_file = extraction_result["file_path"]
        
        conversion_result = self.converter.convert_audio(
            input_file,
            output_format
        )
        
        if not conversion_result["success"]:
            return conversion_result
        
        output_file = conversion_result["file_path"]
        
        original_title = extraction_result.get("title", "Unknown")
        artist = extraction_result.get("artist")
        album = extraction_result.get("album")
        duration = extraction_result.get("duration")
        
        cleaned_title = self.title_cleaner.clean(original_title)
        parsed_artist, parsed_title = (
            self.title_cleaner.split_artist_title(cleaned_title)
        )
        
        if parsed_artist:
            if not artist:
                artist = parsed_artist
                title = parsed_title
            elif parsed_artist.casefold() == artist.casefold():
                title = parsed_title
            else:
                title = cleaned_title
        else:
            title = cleaned_title
            
        if not title:
            title = original_title
            
        try:
            clean_output_path = self.storage.get_output_path(
                title,
                output_format
            )
            output_file.rename(clean_output_path)
            output_file = clean_output_path
            
        except OSError as error:
            return {
                "success": False,
                "error": f"Could not rename output file: {error}",
                "file_path": output_file,
            }
        
        warnings = {}
        
        metadata_result = self.metadata.add_metadata(
            file_path=output_file,
            title=title,
            artist=artist,
            album=album,
        )
        
        if not metadata_result["success"]:
            warnings["metadata"] = metadata_result.get(
                "error",
                "Could not add audio metadata"
            )
            
        thumbnail = extraction_result.get("thumbnail")
        artwork_result = None
        
        if thumbnail:
            artwork_result = self.artwork.download_artwork(
                thumbnail,
                title
            )
            
            if artwork_result["success"]:
                image_data = artwork_result["image_data"]
                
                embedding_result = self.artwork.embed_artwork(
                    audio_path=output_file,
                    image_data=image_data
                )
                
                artwork_result["embedded"] = embedding_result["success"]
                artwork_result.pop("image_data", None)
                
                if not embedding_result["success"]:
                    warnings["artwork"] = embedding_result.get(
                        "error",
                        "Could not embed artwork"
                    )
                    
            else:
                warnings["artwork"] = artwork_result.get(
                    "error",
                    "Could not download artwork"
                )
                
        else:
            warnings["artwork"] = "No artwork URL available"
            
        lyrics_result = None
        
        if artist:
            lyrics_search = self.lyrics.search_lyrics(
                title=title,
                artist=artist,
                album=album,
                duration=duration,
            )
            
            if lyrics_search["success"]:
                synced_lyrics = lyrics_search.get("synced_lyrics")
                plain_lyrics = lyrics_search.get("plain_lyrics")
                
                if synced_lyrics:
                    lyrics_content = synced_lyrics
                    lyrics_type = "synced"
                    
                elif plain_lyrics:
                    lyrics_content = plain_lyrics
                    lyrics_type = "plain"
                    
                else:
                    lyrics_content = None
                    lyrics_type = None
                    
                if lyrics_content:
                    lyrics_result = self.metadata.add_lyrics(
                        file_path=output_file,
                        lyrics=lyrics_content,
                        lyrics_type=lyrics_type,
                    )
                    
                    if lyrics_result["success"]:
                        lyrics_result["title"] = lyrics_search.get(
                            "title"
                        )
                        lyrics_result["artist"] = lyrics_search.get(
                            "artist"
                        )
                    else:
                        warnings["lyrics"] = lyrics_result.get(
                            "error",
                            "Could not embed lyrics"
                        )
                        
                else:
                    warnings["lyrics"] = "No usable lyrics available"
                    
            else:
                warnings["lyrics"] = lyrics_search.get(
                    "error",
                    "Could not find lyrics"
                )
                
        else:
            warnings["lyrics"] = "Artist information unavailable"
            
        cleanup_warning = None
        
        try:
            if input_file.exists():
                self.storage.delete_file(input_file)
                
        except OSError as error:
            cleanup_warning = str(error)
            
        return {
            "success": True,
            "title": title,
            "original_title": original_title,
            "artist": artist,
            "filename": output_file.name,
            "query": query,
            "duration": duration,
            "size": output_file.stat().st_size,
            "file_path": output_file,
            "artwork": artwork_result,
            "metadata": metadata_result,
            "lyrics": lyrics_result,
            "warnings": warnings,
            "cleanup_warning": cleanup_warning,
        }