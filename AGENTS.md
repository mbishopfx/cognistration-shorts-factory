# Cognistration Shorts Factory

Cloud renderer for Cognistration YouTube Shorts. This repository is the whole
environment: it builds the video, puts the finished MP4 in Google Drive, and
never writes anything to the machine that produced it.

## What lives here

| Path | Purpose |
|------|---------|
| `remotion/Composition.tsx` | The video: HTML animation backdrop, machine readout, three wave panels, App Store CTA |
| `remotion/index.tsx` | Composition registration (duration comes from `durationSec`) |
| `backgrounds/*.html` | BishopTech p5.js sketches used as the moving backdrop |
| `scripts/render_batch.py` | Driver: audio, background, render, upload, cleanup |
| `scripts/render_background.py` | Renders a p5.js sketch to a background MP4 with Playwright |
| `scripts/generate_audio.py` | Pure binaural beat WAV (left ear carrier, right ear carrier plus beat) |
| `scripts/descriptions.py` | Title, description, and tags for each brain state |
| `scripts/upload_to_drive.py` | Drive upload, stamps the YouTube copy onto the file |
| `state/batch_queue.json` | What to render next |
| `state/metadata/*.json` | Finished YouTube copy per batch item (written during a run) |

## Environment setup

```bash
bash setup.sh
python3 -m playwright install --with-deps chromium
```

## How to run one item

```bash
# Next pending item in the queue
python3 scripts/render_batch.py

# A specific brain state
python3 scripts/render_batch.py --target-state theta

# Everything pending
python3 scripts/render_batch.py --all

# See what would happen
python3 scripts/render_batch.py --dry-run
```

Credentials come from the environment, not from files:

```
COGNISTRATION_SHORTS_DRIVE_FOLDER_ID
GOOGLE_OAUTH_CLIENT_ID
GOOGLE_OAUTH_CLIENT_SECRET
GOOGLE_OAUTH_REFRESH_TOKEN
```

A service account key at `scripts/service-account-key.json` also works, but a
plain service account has no Drive storage quota of its own, so the OAuth
refresh token is the supported path.

## Rules

- Never commit rendered media. `output/`, `remotion/public/audio/`, and
  `remotion/public/backgrounds/` are generated per run and deleted afterwards.
- Every run cleans up its own WAV, MP3, background MP4, and final MP4. Only the
  Drive upload survives.
- Copy rules for brain state descriptions: factual neuroscience first, no em
  dashes, no medical or treatment claims, no government program framing, no
  URLs in the body. See `scripts/descriptions.py`.
- Commits use `mbishopfx <mattbishopfx@gmail.com>`.
