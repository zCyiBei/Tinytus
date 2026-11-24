import argparse
from tinytus.config.settings import Config
from tinytus.services.manager import AudioManager

def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download and convert audio from YouTube.",
        prog="tinytus"
    )
    
    parser.add_argument(
        "query",
        help="Song name, artist, or YouTube URL"
    )
    
    parser.add_argument(
        "-f",
        "--format",
        choices=Config.SUPPORTED_FORMATS,
        default=Config.DEFAULT_FORMAT,
        help=f"Output format (default: {Config.DEFAULT_FORMAT})"
    )
    
    return parser

def main() -> int:
    parser = setup_parser()
    args = parser.parse_args()
    
    try:
        manager = AudioManager()
        
        print(f"Processing audio from: {args.query}")
        print(f"Output format: {args.format}")
        
        result = manager.process_audio(args.query, args.format)
        
        if not result["success"]:
            print(f"Error: {result['error']}")
            return 1
        
        print("\nAudio processed successfully!")
        print(f"Title: {result['title']}")
        print(f"File: {result['filename']}")
        print(f"Size: {result['size']} bytes")
        print(f"Location: {result['file_path']}")
        
        if result.get("artwork"):
            print(f"Artwork: {result['artwork']}")
            
        if result.get("lyrics"):
            print(f"Lyrics: {result['lyrics']}")
            
        if result.get("cleanup_warning"):
            print(f"Cleanup warning: {result['cleanup_warning']}")
            
        return 0
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    
if __name__ == "__main__":
    raise SystemExit(main())