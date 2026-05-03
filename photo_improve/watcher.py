"""Folder watcher — STUB (v0.5).

Implementation outline (v0.5):
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class _Handler(FileSystemEventHandler):
        def __init__(self, cfg): self.cfg = cfg
        def on_created(self, event):
            if event.is_directory: return
            p = Path(event.src_path)
            if p.suffix.lower() not in PHOTO_EXTENSIONS: return
            # Wait briefly for the file to finish being written, then process.
            time.sleep(self.cfg.watcher.poll_interval_seconds)
            _process_one(p, instantiated_steps, self.cfg)

    def watch(cfg):
        observer = Observer()
        observer.schedule(_Handler(cfg), str(cfg.input_dir), recursive=False)
        observer.start()
        try:
            while True: time.sleep(1)
        finally:
            observer.stop()
            observer.join()
"""
from __future__ import annotations

from photo_improve.config import Config


def watch(cfg: Config) -> None:
    raise NotImplementedError(
        "Folder watcher is planned for v0.5. "
        "Use `photo-improve run` for now."
    )
