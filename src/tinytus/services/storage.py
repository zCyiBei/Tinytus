from pathlib import Path
from typing import Any
import shutil
from tinytus.config.settings import Config

class AudioStorage:
    
    def __init__(self):
        self.download_dir = Config.DOWNLOAD_DIR
        self.convert_dir = Config.CONVERT_DIR
        
    def create_directories(self) -> None:
        
        self._ensure_directory_exists(self.download_dir)
        self._ensure_directory_exists(self.convert_dir)
        
    def _ensure_directory_exists(self, directory: Path) -> None:
        
        directory.mkdir(parents=True, exist_ok=True)
        
    def get_output_path(
        self,
        filename: str,
        output_format: str,
        directory: Path = None
    ) -> Path:
        
        output_format = output_format.lower()
        
        if output_format not in Config.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {output_format}")
        
        if directory is None:
            directory = self.convert_dir
            
        self._ensure_directory_exists(directory)
        
        filename = Path(filename).stem
        output_path = directory / f"{filename}.{output_format}"
        
        counter = 1
        
        while output_path.exists():
            output_path = directory / f"{filename}_{counter}.{output_format}"
            counter += 1
            
        return output_path
    
    def file_exists(self, file_path: Path) -> bool:
        
        return file_path.is_file()
    
    def get_file_info(self, file_path: Path) -> dict[str, Any]:
        
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return {
            "filename": file_path.name,
            "file_path": file_path,
            "extension": file_path.suffix.lower(),
            "size": file_path.stat().st_size
        }
        
    def save(self, source_path: Path, output_filename: str, directory: Path = None) -> Path:
        
        if not source_path.is_file():
            raise FileNotFoundError(f"File not found: {source_path}")
        
        if directory is None:
            directory = self.download_dir
            
        self._ensure_directory_exists(directory)
        
        filename = Path(output_filename).stem
        output_path = directory / f"{filename}{source_path.suffix}"
        
        counter = 1
        
        while output_path.exists():
            output_path = directory / f"{filename}_{counter}{source_path.suffix}"
            counter += 1
            
        shutil.copy2(source_path, output_path)
        
        return output_path
    
    def delete_file(self, file_path: Path) -> bool:
        
        if not file_path.is_file():
            return False
        
        file_path.unlink()
        return True