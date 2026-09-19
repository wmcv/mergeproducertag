# Push Producer Tag

Push Producer Tag watches any GitHub repository and plays a local producer-tag
audio clip whenever a new push is detected.

## Requirements

- macOS with `afplay`
- Python 3.9 or newer
- A GitHub personal access token for private repositories (optional for public repositories)

## Install

```bash
git clone <repository-url>
cd mergeproducertag
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Create a fine-grained GitHub personal access token at GitHub **Settings > Developer settings > Personal access tokens > Fine-grained tokens**. Give it read-only **Contents** access to the repository you want to monitor. Public repositories can be monitored without a token, but setting `GITHUB_TOKEN` is recommended for higher API limits.

## Configure

Edit `.env` with any owner, repository, and branch:

```dotenv
GITHUB_TOKEN=github_pat_xxxxxxxxx
GITHUB_OWNER=wmcv
GITHUB_REPO=mergeproducertag
GITHUB_BRANCH=main
```

Place the audio file at `audio/producer-tag.mp3`. The file is intentionally not included in this project.

## Run

```bash
python main.py
```

The current commit is recorded as the startup baseline, so it will not play on launch. The monitor polls GitHub about every three seconds and plays the tag once when the branch's latest SHA changes. The last processed SHA and its repository/branch are stored in `.push-producer-tag-state.json`; it is ignored by Git. Paths are resolved relative to the project, so the program also works when invoked from another directory.

To test it, start the monitor, create a commit in the configured repository, and push it to the configured branch:

```bash
git commit --allow-empty -m "Test producer tag"
git push origin main
```

The next poll should print the push details and play the audio. Temporary network and GitHub API failures are logged and retried.

The polling boundary is isolated in `github_monitor.py`, so a future version can replace polling with GitHub `push` webhook events without changing audio or state handling.
