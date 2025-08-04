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
        base_directory: Optional[str] = None,
    ) -> None:
        self.allowed_extensions = (
            [ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in allowed_extensions]
            if allowed_extensions
            else None
        )
        self.max_size = max_size
        self.on_files = on_files
        self.base_directory = Path(base_directory).resolve() if base_directory else None

    def drop(self, file_paths: Iterable[str]) -> List[str]:
        files = self._filter_files(file_paths)
        if self.on_files:
            self.on_files(files)
        return files

    def _filter_files(self, file_paths: Iterable[str]) -> List[str]:
        valid: List[str] = []
        for path in file_paths:
            p = Path(path)
            try:
                resolved = p.resolve(strict=True)
            except (FileNotFoundError, OSError):
                continue

            # reject symlinks in the path
            if any(part.is_symlink() for part in [p, *p.parents]):
                continue

            if self.base_directory:
                try:
                    resolved.relative_to(self.base_directory)
                except ValueError:
                    continue

            if not resolved.is_file():
                continue

            suffix = resolved.suffix.lower()
            if self.allowed_extensions and suffix not in self.allowed_extensions:
                continue

            if self.max_size is not None:
                try:
                    if os.path.getsize(resolved) > self.max_size:
                        continue
                except OSError:
                    continue

            valid.append(str(resolved))
        return valid
