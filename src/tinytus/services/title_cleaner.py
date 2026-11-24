import re

class TitleCleaner:
    
    REMOVE_PATTERNS = [
        r"\bofficial\s+music\s+video\b",
        r"\bofficial\s+video\b",
        r"\bofficial\s+audio\b",
        r"\bofficial\s+lyric\s+video\b",
        r"\blyric\s+video\b",
        r"\blyrics?\b",
        r"\bvisualizer\b",
        r"\bofficial\b",
        r"\bvideo\s+oficial\b",
        r"\bvídeo\s+oficial\b",
        r"\baudio\s+oficial\b",
        r"\bvideoclip\s+oficial\b",
        r"\bvideo\s+musical\s+oficial\b",
        r"\bvídeo\s+musical\s+oficial\b",
        r"\bvideo\s+con\s+letra\b",
        r"\bvídeo\s+con\s+letra\b",
        r"\bletra\s+oficial\b",
        r"\bvisualizador\b",
        r"\bsubtitulado\b",
        r"\bsubtitulada\b",
        r"\bcon\s+subtítulos\b",
        r"\bcon\s+subtitulos\b",
        r"\ben\s+vivo\b",
        r"\blive\s+video\b",
        r"\blive\s+audio\b",
        r"\bhd\b",
        r"\bfhd\b",
        r"\b4k\b",
        r"\bhq\b",
        r"\bremastered\b",
        r"\bremasterizado\b",
        r"\bremasterizada\b",
    ]
    
    @classmethod
    def clean(cls, title: str) -> str:
        if not isinstance(title, str):
            return ""
        
        cleaned = title.strip()
        
        for pattern in cls.REMOVE_PATTERNS:
            cleaned = re.sub(
                rf"[\(\[]\s*{pattern}\s*[\)\]]",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            
        for pattern in cls.REMOVE_PATTERNS:
            cleaned = re.sub(
                pattern,
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            
        cleaned = re.sub(r"\s+", " ", cleaned)
        cleaned = re.sub(r"\s*[-|_]+\s*", " - ", cleaned)
        cleaned = re.sub(r"\s*-\s*-\s*", " - ", cleaned)
        
        return cleaned.strip(" -|_")
    
    @classmethod
    def split_artist_title(cls, title: str) -> tuple[str | None, str]:
        cleaned = cls.clean(title)
        
        if " - " not in cleaned:
            return None, cleaned
        
        artist, track = cleaned.split(" - ", 1)
        
        return artist.strip(), track.strip()