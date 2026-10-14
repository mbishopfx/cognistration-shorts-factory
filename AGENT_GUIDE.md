# Cognistration Shorts Factory — Agent Guide

## Your job

You are a video rendering agent. Your ONLY job is to:

1. Read the batch queue
2. For each pending item: generate binaural audio → render the Remotion video → upload to Google Drive
3. Mark items complete in the queue

You do NOT upload to YouTube. You do NOT write descriptions or titles. You just render videos and put them in the shared Drive folder.

---

## One-time setup

```bash
# Clone this repo
git clone https://github.com/mbishopfx/cognistration-shorts-factory.git
cd cognistration-shorts-factory

# Run setup (installs Node deps, Python deps, Playwright browsers)
bash setup.sh

# Place the logo
# Download cognistration-mark.png from the shared Drive or copy it in:
cp /path/to/cognistration-mark.png remotion/public/images/cognistration-mark.png
```

---

## Google Drive auth

This repo uses a Google service account to upload to Drive. Get the service account JSON key from the shared 1Password vault or from Matt, and save it as:

```
scripts/service-account-key.json
```

The shared Drive folder ID is stored in `state/batch_queue.json` under `driveFolderId`. Videos land in that folder, organized by brain state.

---

## Every time you run

### Step 1: Read the queue

```bash
cat state/batch_queue.json
```

Each batch item looks like:

```json
{
  "id": "theta-2026-10-14-a",
  "brainState": "theta",
  "carrierHz": 200,
  "durationSec": 65,
  "status": "pending",
  "outputFile": null,
  "driveFileId": null
}
```

Only work on items with `"status": "pending"`.

### Step 2: Generate audio

```bash
python3 scripts/generate_audio.py \
  --output output/audio/<id>.wav \
  --duration <durationSec> \
  --carrier <carrierHz> \
  --beat <beatHz>   # see brain state map below
```

Brain state → beat Hz map:

| State  | Hz   |
|--------|------|
| delta  | 2.5  |
| theta  | 6.0  |
| alpha  | 10.0 |
| smr    | 13.0 |
| beta   | 18.0 |
| gamma  | 38.0 |

### Step 3: Convert to MP3

```bash
ffmpeg -y -i output/audio/<id>.wav -codec:a libmp3lame -b:a 192k output/audio/<id>.mp3
```

### Step 4: Render the Remotion video

```bash
cd remotion
npx remotion render index.tsx CognistrationShort ../output/<id>.mp4 \
  --props='{"brainState":"<brainState>","audioPath":"output/audio/<id>.mp3","carrierHz":<carrierHz>}'
cd ..
```

This takes ~2-3 minutes per 65-second video on a decent machine.

### Step 5: Verify the output

```bash
ffprobe -v error -show_entries format=duration,size -show_entries stream=width,height,codec_name output/<id>.mp4
```

Expected: 1080x1920, h264 video + aac audio, duration matches input.

### Step 6: Upload to Google Drive

```bash
python3 scripts/upload_to_drive.py output/<id>.mp4 --id <id> --state <brainState>
```

This uploads to the shared folder and prints the Drive file ID.

### Step 7: Mark complete

Update `state/batch_queue.json` — change the item's status to `"done"`, set `outputFile` and `driveFileId`:

```bash
python3 scripts/update_queue.py --id <id> --status done --file output/<id>.mp4 --drive-id <FILE_ID>
```

---

## Batch queue population

You don't create the queue. The queue is populated by the main Cognistration agent (Hermes on Matt's laptop). When you see new pending items, render them.

The main agent watches the Drive folder and pulls completed videos from there.

---

## Troubleshooting

### "Remotion not found"
```bash
cd remotion && npm install && cd ..
```

### "ffmpeg not found"
```bash
brew install ffmpeg
# or: apt install ffmpeg
```

### "Google Drive auth failed"
Check that `scripts/service-account-key.json` exists and has not expired. The service account needs Drive write access to the shared folder.

### Out of disk space
Rendered videos are ~15-20 MB each. Delete `output/*.mp4` after successful Drive upload. The upload script can do this with `--cleanup`.

### Rendering is slow
Remotion renders CPU-only by default. On Apple Silicon, it uses multiple cores. Close other apps. A 65-second 1080x1920 video takes ~2-3 minutes on M1/M2, ~5-8 minutes on Intel Mac.

---

## State file format reference

`state/batch_queue.json`:
```json
{
  "driveFolderId": "1AbCdEfGhIjKlMnOpQrStUvWxYz",
  "batches": [
    {
      "id": "theta-2026-10-14-a",
      "brainState": "theta",
      "carrierHz": 200,
      "durationSec": 65,
      "status": "pending",
      "outputFile": null,
      "driveFileId": null,
      "createdAt": "2026-10-14T12:00:00Z"
    }
  ]
}
```

Status values: `pending` → `rendering` → `uploading` → `done` | `failed`

Never delete completed items — the main agent reads them to know what's available.