import subprocess
from pathlib import Path
from typing import Dict, Any
from tinytus.config.settings import Config
from tinytus.services.storage import AudioStorage

class AudioConverter:
    
    def __init__(self):
        self.convert_dir = Config.CONVERT_DIR
        self.ffmpeg_path = Config.FFMPEG_PATH
        self.storage = AudioStorage()
        
    def convert_audio(
        self,
        input_file: Path,
        output_format: str = Config.DEFAULT_FORMAT
    ) -> Dict[str, Any]:
        
        try:
            input_file = Path(input_file)
            
            if not input_file.is_file():
                raise FileNotFoundError(
                    f"Input file not found: {input_file}"
                )
                
            output_format = self._validate_format(output_format)
            
            output_path = self.storage.get_output_path(
                input_file.name,
                output_format
            )
            
            cmd = [
                self.ffmpeg_path,
                "-i", str(input_file),
                "-map", "0:a:0",
                "-vn",
                "-n",
            ]
            
            if input_file.suffix.lower() == f".{output_format}":
                cmd.extend(["-c:a", "copy"])
                
            elif output_format == "mp3":
                cmd.extend([
                    "-c:a", "libmp3lame",
                    "-q:a", "0",
                ])
                
            elif output_format == "flac":
                cmd.extend([
                    "-c:a", "flac",
                ])
                
            cmd.append(str(output_path))
            
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return {
                "success": True,
                "title": input_file.stem,
                "filename": output_path.name,
                "file_path": output_path,
                "input_format": input_file.suffix[1:],
                "output_format": output_format,
                "size": output_path.stat().st_size,
            }
            
        except subprocess.CalledProcessError as error:
            return {
                "success": False,
                "error": f"FFmpeg conversion failed: {error.stderr}",
                "file_path": input_file,
            }
            
        except (FileNotFoundError, ValueError, OSError) as error:
            return {
                "success": False,
                "error": str(error),
                "file_path": input_file,
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
    
    def convert_batch(
        self,
        input_files: list[Path],
        output_format: str = Config.DEFAULT_FORMAT
    ) -> Dict[str, Any]:
        
        results = []
        
        for input_file in input_files:
            result = self.convert_audio(input_file, output_format)
            results.append(result)
            
        return {
            "success": all(result["success"] for result in results),
            "results": results,
            "total": len(results),
            "successful": sum(
                1 for result in results if result["success"]
            ),
        }