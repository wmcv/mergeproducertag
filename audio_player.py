"""Non-blocking producer-tag playback for macOS."""

from pathlib import Path
import shutil
import subprocess
import logging


logger = logging.getLogger(__name__)


class AudioPlayer:
    def __init__(self, audio_path: Path):
        self.audio_path = audio_path

    def play(self) -> bool:
        if not self.audio_path.is_file():
            logger.error("Audio file not found: %s", self.audio_path)
            return False
        if shutil.which("afplay") is None:
            logger.error("afplay was not found; producer tag requires macOS")
            return False

        try:
            subprocess.Popen(
                ["afplay", str(self.audio_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as error:
            logger.error("Could not start audio playback: %s", error)
            return False
        return True