#!/usr/bin/env python3
"""Render pending Cognistration Shorts — designed to run in a cloud CI runner.

Reads state/batch_queue.json, renders the next pending item (optionally
filtered to one brain state), uploads the finished MP4 to Google Drive,
marks the queue entry done, and deletes every intermediate artifact.

Nothing is kept on the machine that runs this: audio, the MP4, and the
Remotion/Chromium caches are all removed when the run finishes. The only
thing that leaves the runner is the upload to the shared Drive folder.

Usage:
  python3 scripts/render_batch.py                     # next pending item
  python3 scripts/render_batch.py --target-state theta
  python3 scripts/render_batch.py --all               # every pending item
  python3 scripts/render_batch.py --dry-run           # show what would run
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_PATH = os.path.join(REPO_ROOT, "state", "batch_queue.json")
REMOTION_DIR = os.path.join(REPO_ROOT, "remotion")
PUBLIC_DIR = os.path.join(REMOTION_DIR, "public")
PUBLIC_AUDIO_DIR = os.path.join(PUBLIC_DIR, "audio")
OUTPUT_DIR = os.path.join(REPO_ROOT, "output")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

# The Remotion composition is registered at durationInFrames=1950 / fps=30.
# Audio is always generated to exactly this length so audio and video end
# together, whatever durationSec the queue entry carries.
COMPOSITION_SECONDS = 65.0

# Carrier stays at 200 Hz; only the beat frequency changes per brain state.
CARRIER_HZ = 200.0
BEAT_HZ = {
    "delta": 2.5,
    "theta": 6.0,
    "alpha": 10.0,
    "smr": 13.0,
    "beta": 18.0,
    "gamma": 38.0,
}


def run(cmd, cwd=None):
    """Run a command, stream its output, raise on failure."""
    printable = " ".join(str(c) for c in cmd)
    print(f"\n$ {printable}", flush=True)
    proc = subprocess.run(cmd, cwd=cwd, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {printable}")


def load_state():
    with open(STATE_PATH) as f:
        return json.load(f)


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def set_status(state, batch_id, status, output_file=None, drive_id=None):
    for batch in state.get("batches", []):
        if batch["id"] == batch_id:
            batch["status"] = status
            if output_file:
                batch["outputFile"] = output_file
            if drive_id:
                batch["driveFileId"] = drive_id
            break
    save_state(state)


def folder_id(state):
    """Env var wins so the folder ID can live in CI config instead of the repo."""
    return (os.environ.get("COGNISTRATION_SHORTS_DRIVE_FOLDER_ID")
            or state.get("driveFolderId") or "")


def pick_items(state, target_state=None, render_all=False):
    batches = [b for b in state.get("batches", []) if b.get("status") == "pending"]
    if target_state:
        matching = [b for b in batches if b.get("brainState") == target_state]
        if matching:
            return matching[:1]
        print(f"  no pending '{target_state}' item — falling back to the next pending item")
    if render_all:
        return batches
    return batches[:1]


def render_one(state, batch):
    batch_id = batch["id"]
    brain_state = batch.get("brainState", "theta")
    beat = BEAT_HZ.get(brain_state, 6.0)

    print("\n" + "=" * 62)
    print(f"  {batch_id}  ({brain_state}, beat {beat} Hz)")
    print("=" * 62)

    os.makedirs(PUBLIC_AUDIO_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    wav_path = os.path.join(OUTPUT_DIR, f"{batch_id}.wav")
    mp3_path = os.path.join(PUBLIC_AUDIO_DIR, f"{batch_id}.mp3")
    mp4_path = os.path.join(OUTPUT_DIR, f"{batch_id}.mp4")

    set_status(state, batch_id, "rendering")

    try:
        # 1. Binaural audio
        run([sys.executable, os.path.join(SCRIPTS_DIR, "generate_audio.py"),
             "--output", wav_path,
             "--duration", str(COMPOSITION_SECONDS),
             "--carrier", str(CARRIER_HZ),
             "--beat", str(beat)])

        # 2. WAV -> MP3, into Remotion's public dir so staticFile() resolves it
        run(["ffmpeg", "-y", "-i", wav_path,
             "-codec:a", "libmp3lame", "-b:a", "192k", mp3_path])
        os.remove(wav_path)

        # 3. Render — audioPath is relative to remotion/public/
        props = json.dumps({
            "brainState": brain_state,
            "audioPath": f"audio/{batch_id}.mp3",
            "carrierHz": CARRIER_HZ,
        })
        run(["npx", "remotion", "render", "index.tsx", "CognistrationShort",
             mp4_path, f"--props={props}"], cwd=REMOTION_DIR)

        # 4. Verify
        run(["ffprobe", "-v", "error",
             "-show_entries", "format=duration,size",
             "-show_entries", "stream=width,height,codec_name",
             "-of", "default=noprint_wrappers=1", mp4_path])
        if not os.path.exists(mp4_path):
            raise RuntimeError("render produced no file")

        # 5. Upload to Drive and delete the local copy in the same step
        set_status(state, batch_id, "uploading")
        out = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "upload_to_drive.py"),
             mp4_path, "--id", batch_id, "--state", brain_state, "--cleanup"],
            text=True, capture_output=True)
        print(out.stdout)
        if out.returncode != 0:
            print(out.stderr)
            raise RuntimeError("drive upload failed")

        drive_id = None
        for line in out.stdout.splitlines():
            if "File ID:" in line:
                drive_id = line.split("File ID:")[-1].strip()
        set_status(state, batch_id, "done",
                   output_file=f"output/{batch_id}.mp4", drive_id=drive_id)
        print(f"\n  ✓ {batch_id} complete — Drive id {drive_id}")

    except Exception as exc:
        print(f"\n  ✗ {batch_id} failed: {exc}")
        set_status(state, batch_id, "failed")
        return False

    finally:
        # Nothing rendered here should survive the run.
        for leftover in (wav_path, mp3_path, mp4_path):
            if os.path.exists(leftover):
                os.remove(leftover)
                print(f"  cleaned up {os.path.relpath(leftover, REPO_ROOT)}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Render pending shorts in CI")
    parser.add_argument("--target-state", dest="target_state",
                        help="Prefer the pending item for this brain state")
    parser.add_argument("--all", action="store_true",
                        help="Render every pending item in the queue")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be rendered and exit")
    args = parser.parse_args()

    if not os.path.exists(os.path.join(SCRIPTS_DIR, "service-account-key.json")):
        print("ERROR: scripts/service-account-key.json is missing.")
        print("In CI this is written from the GDRIVE_SERVICE_ACCOUNT_JSON secret.")
        sys.exit(1)

    state = load_state()

    if not folder_id(state):
        print("ERROR: no Drive folder id. Set COGNISTRATION_SHORTS_DRIVE_FOLDER_ID.")
        sys.exit(1)

    items = pick_items(state, args.target_state, args.all)
    if not items:
        print("Nothing pending — exiting cleanly.")
        return

    print(f"\nRendering {len(items)} item(s):")
    for b in items:
        print(f"  • {b['id']}  ({b.get('brainState')})")

    if args.dry_run:
        print("\nDry run — nothing rendered.")
        return

    ok = sum(1 for b in items if render_one(state, b))
    print(f"\nFinished: {ok}/{len(items)} rendered and uploaded.")


if __name__ == "__main__":
    main()
