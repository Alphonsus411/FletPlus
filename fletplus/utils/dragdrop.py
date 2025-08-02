import os
from pathlib import Path
from typing import Callable, Iterable, List, Optional


class FileDropZone:
    """Control simplificado para gestionar drop de archivos."""

    def __init__(
        self,
        allowed_extensions: Optional[Iterable[str]] = None,
        max_size: Optional[int] = None,
        on_files: Optional[Callable[[List[str]], None]] = None,
    ) -> None:
        self.allowed_extensions = (
            [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed_extensions]
            if allowed_extensions
            else None
        )
        self.max_size = max_size
        self.on_files = on_files

    def drop(self, file_paths: Iterable[str]) -> List[str]:
        files = self._filter_files(file_paths)
        if self.on_files:
            self.on_files(files)
        return files

    def _filter_files(self, file_paths: Iterable[str]) -> List[str]:
        valid: List[str] = []
        for path in file_paths:
            suffix = Path(path).suffix.lower()
            if self.allowed_extensions and suffix not in self.allowed_extensions:
                continue
            if self.max_size is not None and os.path.getsize(path) > self.max_size:
                continue
            valid.append(str(path))
        return valid
