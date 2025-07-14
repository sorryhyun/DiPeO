"""Domain service for managing file backups with a standardized strategy."""

from datetime import UTC, datetime
from pathlib import Path


class BackupService:
    """Service that provides a standardized backup strategy for files.
    
    This service defines the domain logic for creating backup filenames
    and managing backup policies across the application.
    """
    
    def __init__(self, backup_suffix: str = ".bak"):
        """Initialize backup service.
        
        Args:
            backup_suffix: Default suffix for backup files
        """
        self.backup_suffix = backup_suffix
    
    def create_backup_name(self, original: Path, timestamp: datetime | None = None) -> Path:
        """Create a standardized backup filename for the given path.
        
        Args:
            original: Original file path
            timestamp: Optional timestamp to use (defaults to current UTC time)
            
        Returns:
            Path object for the backup file
            
        Example:
            original: /path/to/file.txt
            backup: /path/to/file.txt.20241225_120000.bak
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)
        
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original.name}.{timestamp_str}{self.backup_suffix}"
        
        return original.parent / backup_name
    
    def create_versioned_backup_name(self, original: Path, version: int) -> Path:
        """Create a versioned backup filename.
        
        Args:
            original: Original file path
            version: Version number
            
        Returns:
            Path object for the versioned backup
            
        Example:
            original: /path/to/file.txt
            backup: /path/to/file.txt.v1.bak
        """
        backup_name = f"{original.name}.v{version}{self.backup_suffix}"
        return original.parent / backup_name
    
    def create_legacy_backup_name(self, original: Path, timestamp: datetime | None = None) -> Path:
        """Create a backup filename using the legacy format.
        
        This method is provided for backward compatibility with existing
        backup files that use the format: file.backup.timestamp.ext
        
        Args:
            original: Original file path
            timestamp: Optional timestamp to use
            
        Returns:
            Path object for the backup file
            
        Example:
            original: /path/to/file.txt
            backup: /path/to/file.backup.20241225_120000.txt
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)
        
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        extension = original.suffix
        stem = original.stem
        
        backup_name = f"{stem}.backup.{timestamp_str}{extension}"
        return original.parent / backup_name
    
    def extract_backup_timestamp(self, backup_path: Path) -> datetime | None:
        """Extract timestamp from a backup filename.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Datetime object if timestamp found, None otherwise
        """
        name = backup_path.name
        
        # Try standard format: file.txt.20241225_120000.bak
        if self.backup_suffix in name:
            parts = name.split('.')
            for part in parts:
                try:
                    # Look for timestamp pattern YYYYMMDD_HHMMSS
                    if len(part) == 15 and '_' in part:
                        dt = datetime.strptime(part, "%Y%m%d_%H%M%S")
                        return dt.replace(tzinfo=UTC)
                except ValueError:
                    continue
        
        return None
    
    def is_backup_file(self, file_path: Path) -> bool:
        """Check if a file is a backup file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if the file appears to be a backup
        """
        name = file_path.name
        
        # Check for standard backup suffix
        if name.endswith(self.backup_suffix):
            return True
        
        # Check for legacy format: .backup. in filename
        if '.backup.' in name:
            return True
        
        # Check for versioned format: .v{number}.bak
        if self.backup_suffix in name:
            parts = name.split('.')
            for part in parts:
                if part.startswith('v') and part[1:].isdigit():
                    return True
        
        return False
    
    def get_original_filename(self, backup_path: Path) -> str | None:
        """Extract the original filename from a backup path.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Original filename if determinable, None otherwise
        """
        name = backup_path.name
        
        # Handle standard format: file.txt.20241225_120000.bak
        if name.endswith(self.backup_suffix):
            # Remove backup suffix and timestamp
            parts = name.rsplit('.', 2)
            if len(parts) >= 3:
                return parts[0]
        
        # Handle legacy format: file.backup.timestamp.ext
        if '.backup.' in name:
            parts = name.split('.backup.')
            if len(parts) == 2:
                # Get original name and extension from the second part
                timestamp_and_ext = parts[1]
                ext_parts = timestamp_and_ext.split('.')
                if len(ext_parts) >= 2:
                    original_ext = '.' + '.'.join(ext_parts[1:])
                    return parts[0] + original_ext
        
        return None