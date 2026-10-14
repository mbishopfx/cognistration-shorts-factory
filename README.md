# Cognistration Shorts Factory

Offloaded video rendering pipeline for Cognistration YouTube Shorts. This repo lives on a machine with adequate disk space and CPU. It renders Remotion videos, generates binaural audio, and uploads finished files to Google Drive.

The main Cognistration agent (Hermes, on Matt's laptop) populates the batch queue and pulls finished videos from Drive for YouTube upload and metadata.

## Quick start

```bash
bash setup.sh
# Place cognistration-mark.png in remotion/public/images/
# Place service-account-key.json in scripts/
# Then follow AGENT_GUIDE.md
```

## Structure

```
├── AGENT_GUIDE.md          # Instructions for the render agent
├── setup.sh                # One-time dependency install
├── requirements.txt         # Python packages
├── remotion/               # Remotion video composition
│   ├── package.json
│   ├── index.tsx           # Entry point
│   ├── Composition.tsx     # Video layout (frequencies, waves, logo, CTA)
│   └── public/             # Static assets (logo)
├── scripts/
│   ├── generate_audio.py   # Pure binaural beat WAV generator
│   ├── upload_to_drive.py  # Google Drive upload via service account
│   └── update_queue.py     # Mark batch items complete
├── state/
│   └── batch_queue.json    # What to render next
└── output/                 # Rendered MP4s (clean up after Drive upload)
```

## Brain states

| State  | Beat Hz | Outcome                          |
|--------|---------|----------------------------------|
| delta  | 2.5     | Deep restorative sleep           |
| theta  | 6.0     | Meditation · Creative flow       |
| alpha  | 10.0    | Relaxed alertness · Calm flow    |
| smr    | 13.0    | Sensorimotor focus               |
| beta   | 18.0    | Active concentration             |
| gamma  | 38.0    | Cognitive synthesis              |