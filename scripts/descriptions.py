#!/usr/bin/env python3
"""Per-brain-state title, description, and discovery tags for Cognistration Shorts.

One source of truth, used by the cloud renderer (which stamps the copy onto the
Drive file) and by the local uploader.

Copy rules:
  - factual neuroscience first, then the felt experience
  - no em dashes, no middle dots
  - no medical claims, no treatment language, no government program framing
  - no URLs in the body (the channel keeps descriptions link free)
"""

# Discovery terms live in both the visible hashtag line and the tag metadata.
TAGS = [
    "binaural beats", "brain waves", "theta waves", "alpha waves", "delta waves",
    "gamma waves", "beta waves", "meditation", "neuroscience",
    "frequency following response", "brainwave entrainment", "deep focus",
    "flow state", "inner voice", "consciousness", "higher self",
    "cognistration", "binaural beat science",
]

NEURO = {
    "delta": (
        "Delta is the slowest band the brain produces, roughly 0.5 to 4 Hz, and it "
        "dominates during the deepest stage of non REM sleep. In that window the "
        "brain clears metabolic waste through the glymphatic system, consolidates "
        "memory, and releases growth hormone. A binaural beat at 2.5 Hz presents two "
        "nearly identical tones, one per ear, so the auditory brainstem resolves a "
        "phantom pulse at the difference frequency and firing patterns across the "
        "cortex begin to follow it."
    ),
    "theta": (
        "Theta runs about 4 to 8 Hz and rises in the borderland between waking and "
        "sleep, the hypnagogic state, and in deep meditative absorption. When two "
        "tones a few hertz apart are played one per ear, the auditory brainstem "
        "resolves a phantom beat at the difference frequency, and cortical firing "
        "starts to follow it. That is the frequency following response, and it is "
        "measured, not imagined. Theta is where the default mode network quiets and "
        "associative thinking loosens."
    ),
    "alpha": (
        "Alpha sits at roughly 8 to 13 Hz and shows up when you are awake but "
        "settled, eyes closed, attention soft rather than narrow. Hans Berger first "
        "recorded it a century ago. Binaural beats in this band present a phantom "
        "difference tone that the auditory brainstem tracks, and the cortex tends to "
        "follow, which is why alpha is associated with calm alertness rather than "
        "drowsiness."
    ),
    "smr": (
        "The sensorimotor rhythm runs about 12 to 15 Hz and is measured over the "
        "sensorimotor cortex when the body is still and the mind is quiet. It is the "
        "band neurofeedback clinicians have used for decades with attention and "
        "impulse control work. A binaural beat at 13 Hz gives the auditory brainstem "
        "a steady difference tone to lock onto, and the resulting drive tends to "
        "settle restless motor activity while attention stays sharp."
    ),
    "beta": (
        "Beta spans about 13 to 30 Hz and tracks active, outward facing cognition: "
        "problem solving, conversation, deliberate focus. A binaural beat at 18 Hz "
        "creates a difference tone the auditory brainstem resolves and follows, which "
        "tends to lift arousal toward engaged wakefulness. This is the band people "
        "reach for when the work needs to move."
    ),
    "gamma": (
        "Gamma runs above 30 Hz and appears in bursts during binding, the moment "
        "separate sensory streams resolve into one perception. It is also studied in "
        "long term meditators. A binaural beat at 38 Hz gives the auditory brainstem "
        "a fast difference tone to track, and because entrainment in this range is "
        "harder to hold, it is best treated as something to explore rather than "
        "something promised."
    ),
}

OUTCOME = {
    "delta": "Deep sleep, inner restoration",
    "theta": "Meditation, creative flow, inner voice",
    "alpha": "Calm awareness, quiet the noise",
    "smr":   "Still body, sharp mind",
    "beta":  "Active focus, mental clarity",
    "gamma": "Higher awareness, connected consciousness",
}

TITLE = {
    "delta": "Delta 2.5 Hz | Deep Sleep, Inner Restoration",
    "theta": "Theta 6 Hz | Meditation and Creative Flow",
    "alpha": "Alpha 10 Hz | Calm Awareness, Quiet the Noise",
    "smr":   "SMR 13 Hz | Still Body, Sharp Mind",
    "beta":  "Beta 18 Hz | Active Focus, Mental Clarity",
    "gamma": "Gamma 38 Hz | Higher Awareness, Connected Consciousness",
}

FOOTER = (
    "Headphones are required, since the two ears have to hear two different tones "
    "for the phantom beat to exist. Listen at a comfortable volume.\n\n"
    "Cognistration is an exploration tool, not a medical device, and nothing here "
    "is a treatment for any condition. If you have a seizure disorder, tinnitus, "
    "or a hearing concern, talk to a clinician before experimenting with tones."
)


def build(brain_state: str, duration_sec: float, carrier_hz: float, beat_hz: float) -> dict:
    """Return title, description, and tags for one queue item."""
    state = brain_state if brain_state in NEURO else "theta"
    right_hz = carrier_hz + beat_hz
    outcome = OUTCOME[state]

    description = "\n".join([
        f"{outcome}.",
        "",
        NEURO[state],
        "",
        f"This session: {carrier_hz:.0f} Hz in the left ear, {right_hz:.1f} Hz in the "
        f"right ear, so the beat lands at {beat_hz:.1f} Hz. Length {duration_sec:.0f} seconds.",
        "",
        FOOTER,
        "",
        " ".join("#" + t.replace(" ", "").replace("-", "") for t in TAGS[:12]),
    ])

    return {
        "title": TITLE[state],
        "description": description,
        "tags": list(TAGS),
        "outcome": outcome,
        "brainState": state,
    }


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Print Shorts metadata as JSON")
    ap.add_argument("--state", required=True)
    ap.add_argument("--duration", type=float, default=65.0)
    ap.add_argument("--carrier", type=float, default=200.0)
    ap.add_argument("--beat", type=float, default=None)
    args = ap.parse_args()

    from render_batch import BEAT_HZ  # noqa: E402  (same directory)

    beat = args.beat if args.beat is not None else BEAT_HZ.get(args.state, 6.0)
    print(json.dumps(build(args.state, args.duration, args.carrier, beat), indent=2))
