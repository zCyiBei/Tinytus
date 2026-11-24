import re
from pathlib import Path
from typing import Any, Dict, Optional
from mutagen import File, MutagenError
from mutagen.id3 import (
    ID3,
    TIT2,
    TPE1,
    TALB,
    TDRC,
    TCON,
    TRCK,
    TPE2,
    SYLT,
    USLT,
    error as ID3Error,
)
from mutagen.flac import FLAC

class AudioMetadata:
    
    SUPPORTED_FORMATS = (".mp3", ".flac")
    
    LRC_TIMESTAMP_PATTERN = re.compile(
        r"\[(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?\]"
    )
    
    def add_metadata(
        self,
        file_path: Path,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        year: Optional[str] = None,
        genre: Optional[str] = None,
        track_number: Optional[str] = None,
        album_artist: Optional[str] = None,
    ) -> Dict[str, Any]:
        
        try:
            file_path = Path(file_path)
            
            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Audio file not found: {file_path}"
                )
                
            if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    "Only MP3 and FLAC files are supported"
                )
                
            values = {
                "title": title,
                "artist": artist,
                "album": album,
                "year": year,
                "genre": genre,
                "track_number": track_number,
                "album_artist": album_artist,
            }
            
            values = {
                key: str(value).strip()
                if value is not None and str(value).strip()
                else None
                for key, value in values.items()
            }
            
            if file_path.suffix.lower() == ".mp3":
                self._add_mp3_metadata(file_path, **values)
            else:
                audio = FLAC(file_path)
                self._add_flac_metadata(audio, **values)
                
            return {
                "success": True,
                "filename": file_path.name,
                "file_path": file_path,
            }
            
        except (OSError, ValueError, MutagenError, TypeError) as error:
            return {
                "success": False,
                "error": str(error),
            }
            
    def add_lyrics(
        self,
        file_path: Path,
        lyrics: str,
        lyrics_type: str = "plain",
    ) -> Dict[str, Any]:
        
        try:
            file_path = Path(file_path)
            
            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Audio file not found: {file_path}"
                )
                
            if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(
                    "Only MP3 and FLAC files are supported"
                )
                
            if not isinstance(lyrics, str) or not lyrics.strip():
                raise ValueError("Lyrics cannot be empty")
            
            if lyrics_type not in ("plain", "synced"):
                raise ValueError(
                    "Lyrics type must be 'plain' or 'synced'"
                )
                
            if file_path.suffix.lower() == ".mp3":
                self._add_mp3_lyrics(
                    file_path,
                    lyrics,
                    lyrics_type
                )
            else:
                self._add_flac_lyrics(
                    file_path,
                    lyrics
                )
                
            return {
                "success": True,
                "filename": file_path.name,
                "file_path": file_path,
                "lyrics_type": lyrics_type,
                "embedded": True,
            }
            
        except (
            OSError,
            ValueError,
            MutagenError,
            TypeError,
            ID3Error,
        ) as error:
            return {
                "success": False,
                "error": str(error),
            }
            
    @classmethod
    def _add_mp3_lyrics(
        cls,
        file_path: Path,
        lyrics: str,
        lyrics_type: str,
    ) -> None:
        
        try:
            audio = ID3(file_path)
        except ID3Error:
            audio = ID3()
            
        audio.delall("USLT")
        audio.delall("SYLT")
        
        if lyrics_type == "synced":
            synchronized_lyrics = cls._parse_lrc(lyrics)
            
            if synchronized_lyrics:
                audio.add(
                    SYLT(
                        encoding=3,
                        lang="eng",
                        format=2,
                        type=1,
                        desc="Lyrics",
                        text=synchronized_lyrics,
                    )
                )
                
                plain_lyrics = "\n".join(
                    line.strip()
                    for line in cls.LRC_TIMESTAMP_PATTERN.sub(
                        "",
                        lyrics
                    ).splitlines()
                    if line.strip()
                )
                
                if plain_lyrics:
                    audio.add(
                        USLT(
                            encoding=3,
                            lang="eng",
                            desc="Lyrics",
                            text=plain_lyrics,
                        )
                    )
            else:
                audio.add(
                    USLT(
                        encoding=3,
                        lang="eng",
                        desc="Lyrics",
                        text=lyrics,
                    )
                )
        else:
            audio.add(
                USLT(
                    encoding=3,
                    lang="eng",
                    desc="Lyrics",
                    text=lyrics,
                )
            )
            
        audio.save(file_path, v2_version=3)
        
    @classmethod
    def _parse_lrc(cls, lyrics: str) -> list[tuple[str, int]]:
        
        synchronized_lyrics = []
        
        for line in lyrics.splitlines():
            timestamps = cls.LRC_TIMESTAMP_PATTERN.findall(line)
            
            if not timestamps:
                continue
            
            text = cls.LRC_TIMESTAMP_PATTERN.sub(
                "",
                line
            ).strip()
            
            if not text:
                continue
            
            for minutes, seconds, fraction in timestamps:
                milliseconds = int(
                    (fraction or "0").ljust(3, "0")
                )
                
                timestamp = (
                    int(minutes) * 60 * 1000
                    + int(seconds) * 1000
                    + milliseconds
                )
                
                synchronized_lyrics.append(
                    (text, timestamp)
                )
                
        return sorted(
            synchronized_lyrics,
            key=lambda item: item[1]
        )
        
    @staticmethod
    def _format_lrc(synchronized_lyrics: list) -> str:
        
        lines = []
        
        for text, timestamp in synchronized_lyrics:
            minutes = timestamp // 60000
            seconds = (timestamp % 60000) / 1000
            
            lines.append(
                f"[{minutes:02d}:{seconds:06.3f}]{text}"
            )
            
        return "\n".join(lines)
        
    @staticmethod
    def _get_mp3_lyrics(file_path: Path) -> Dict[str, Any]:
        
        try:
            audio = ID3(file_path)
        except ID3Error:
            return {
                "lyrics": None,
                "lyrics_type": None,
            }
            
        synchronized_lyrics = audio.getall("SYLT")
        
        if synchronized_lyrics:
            lyrics = AudioMetadata._format_lrc(
                synchronized_lyrics[0].text
            )
            
            return {
                "lyrics": lyrics,
                "lyrics_type": "synced",
            }
            
        plain_lyrics = audio.getall("USLT")
        
        if plain_lyrics:
            return {
                "lyrics": plain_lyrics[0].text,
                "lyrics_type": "plain",
            }
            
        return {
            "lyrics": None,
            "lyrics_type": None,
        }
        
    @staticmethod
    def _add_flac_lyrics(
        audio: FLAC,
        lyrics: str,
    ) -> None:
        
        audio["lyrics"] = lyrics
        audio.save()
        
    @staticmethod
    def _add_mp3_metadata(
        file_path: Path,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        year: Optional[str] = None,
        genre: Optional[str] = None,
        track_number: Optional[str] = None,
        album_artist: Optional[str] = None,
    ) -> None:
        
        try:
            audio = ID3(file_path)
        except ID3Error:
            audio = ID3()
            
        tags = {
            "TIT2": (TIT2, title),
            "TPE1": (TPE1, artist),
            "TALB": (TALB, album),
            "TDRC": (TDRC, year),
            "TCON": (TCON, genre),
            "TRCK": (TRCK, track_number),
            "TPE2": (TPE2, album_artist),
        }
        
        for frame_id, (frame_class, value) in tags.items():
            
            if value is not None:
                audio.delall(frame_id)
                audio.add(
                    frame_class(
                        encoding=3,
                        text=value
                    )
                )
                
        audio.save(file_path, v2_version=3)
        
    @staticmethod
    def _add_flac_metadata(
        audio: FLAC,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        year: Optional[str] = None,
        genre: Optional[str] = None,
        track_number: Optional[str] = None,
        album_artist: Optional[str] = None,
    ) -> None:
        
        tags = {
            "title": title,
            "artist": artist,
            "album": album,
            "date": year,
            "genre": genre,
            "tracknumber": track_number,
            "albumartist": album_artist,
        }
        
        for key, value in tags.items():
            
            if value is not None:
                audio[key] = value
                
        audio.save()
        
    @staticmethod
    def get_metadata(file_path: Path) -> Dict[str, Any]:
        
        try:
            file_path = Path(file_path)
            
            if not file_path.is_file():
                raise FileNotFoundError(
                    f"Audio file not found: {file_path}"
                )
                
            if file_path.suffix.lower() not in AudioMetadata.SUPPORTED_FORMATS:
                raise ValueError(
                    "Only MP3 and FLAC files are supported"
                )
                
            audio = File(file_path, easy=True)
            
            if audio is None:
                raise ValueError("Unsupported audio format")
            
            def get_tag(key: str) -> Optional[str]:
                values = audio.get(key)
                
                if not values:
                    return None
                
                return str(values[0])
            
            if file_path.suffix.lower() == ".mp3":
                lyrics_data = AudioMetadata._get_mp3_lyrics(
                    file_path
                )
            else:
                flac_audio = FLAC(file_path)
                lyrics_values = flac_audio.get("lyrics")
                
                lyrics_data = {
                    "lyrics": (
                        str(lyrics_values[0])
                        if lyrics_values
                        else None
                    ),
                    "lyrics_type": (
                        "synced"
                        if lyrics_values
                        and AudioMetadata.LRC_TIMESTAMP_PATTERN.search(
                            str(lyrics_values[0])
                        )
                        else "plain" if lyrics_values else None
                    ),
                }
            
            return {
                "success": True,
                "title": get_tag("title"),
                "artist": get_tag("artist"),
                "album": get_tag("album"),
                "year": get_tag("date"),
                "genre": get_tag("genre"),
                "track_number": get_tag("tracknumber"),
                "album_artist": get_tag("albumartist"),
                "lyrics": lyrics_data["lyrics"],
                "lyrics_type": lyrics_data["lyrics_type"],
            }
            
        except (OSError, ValueError, MutagenError, TypeError) as error:
            return {
                "success": False,
                "error": str(error),
            }