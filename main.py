"""Poll a configured GitHub branch and play a producer tag after pushes."""

import logging
import os
from pathlib import Path
import time

from dotenv import load_dotenv

from audio_player import AudioPlayer
from github_monitor import GitHubError, GitHubMonitor
from state import StateStore


POLL_SECONDS = 3
PROJECT_DIR = Path(__file__).resolve().parent
STATE_PATH = PROJECT_DIR / ".push-producer-tag-state.json"
AUDIO_PATH = PROJECT_DIR / "audio" / "producer-tag.mp3"


def required_setting(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def build_monitor() -> GitHubMonitor:
    return GitHubMonitor(
        owner=required_setting("GITHUB_OWNER"),
        repo=required_setting("GITHUB_REPO"),
        branch=required_setting("GITHUB_BRANCH"),
        token=os.getenv("GITHUB_TOKEN", "").strip() or None,
    )


def run() -> None:
    load_dotenv(PROJECT_DIR / ".env")
    try:
        monitor = build_monitor()
    except ValueError as error:
        raise SystemExit(str(error)) from error

    state = StateStore(STATE_PATH)
    player = AudioPlayer(AUDIO_PATH)
    logging.info("🎵 Push Producer Tag")
    logging.info("Watching: %s/%s", monitor.owner, monitor.repo)
    logging.info("Branch: %s", monitor.branch)

    while True:
        try:
            baseline = monitor.latest_commit()
            break
        except GitHubError as error:
            logging.error("Unable to establish startup baseline: %s; retrying", error)
            time.sleep(POLL_SECONDS)

    state_key = f"{monitor.owner}/{monitor.repo}@{monitor.branch}"
    previous_sha = state.load(state_key)
    try:
        state.save(state_key, baseline.sha)
    except OSError as error:
        logging.error("Could not persist startup state: %s; monitoring will continue", error)
    if previous_sha and previous_sha != baseline.sha:
        logging.info("Startup baseline changed from the stored SHA; no audio will play for it.")
    logging.info("Waiting for someone to ship 👀")

    while True:
        time.sleep(POLL_SECONDS)
        try:
            latest = monitor.latest_commit()
            if latest.sha == baseline.sha:
                continue

            # Save before playback so a restart cannot replay a successfully observed push.
            state.save(state_key, latest.sha)
            baseline = latest
            logging.info("🚀 PUSH DETECTED")
            logging.info("📦 %s/%s", monitor.owner, monitor.repo)
            logging.info("🌿 %s", monitor.branch)
            logging.info("👤 %s", latest.author)
            logging.info('📝 "%s"', latest.message)
            logging.info("🔗 %s", latest.sha[:7])
            if player.play():
                logging.info("🔥 PLAYING PRODUCER TAG")
        except GitHubError as error:
            logging.error("%s; retrying", error)
        except OSError as error:
            logging.error("Could not persist local state: %s; retrying", error)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        run()
    except KeyboardInterrupt:
        logging.info("\nMonitoring stopped.")
