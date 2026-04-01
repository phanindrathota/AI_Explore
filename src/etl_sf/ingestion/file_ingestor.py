from __future__ import annotations

import shutil
from pathlib import Path

from etl_sf.mappings.interpreter import FileMapping


class FileIngestor:
    def __init__(self, input_dir: Path, archive_dir: Path, error_dir: Path) -> None:
        self.input_dir = input_dir
        self.archive_dir = archive_dir
        self.error_dir = error_dir

    def list_files(self, mapping: FileMapping) -> list[Path]:
        return sorted(self.input_dir.glob(mapping.file_pattern))

    def archive(self, path: Path) -> None:
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), self.archive_dir / path.name)

    def move_to_error(self, path: Path) -> None:
        self.error_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), self.error_dir / path.name)
