#!/usr/bin/env python3
"""Generate pure binaural beat WAV files for Cognistration Shorts.

Left ear: carrier Hz. Right ear: carrier + beat Hz.
Output: 48 kHz 16-bit stereo WAV with fade in/out.
"""

import argparse, math, os, struct, sys, wave

SAMPLE_RATE = 48000
BIT_DEPTH = 16


def generate(output_path: str, duration_sec: float, carrier_hz: float,
             beat_hz: float, volume: float = 0.7):
    """Generate a pure binaural beat WAV file."""
    left_freq = carrier_hz
    right_freq = carrier_hz + beat_hz
    total_samples = int(duration_sec * SAMPLE_RATE)

    fade_in_samples = int(0.5 * SAMPLE_RATE)
    fade_out_samples = int(3.0 * SAMPLE_RATE)

    left_phase_inc = 2.0 * math.pi * left_freq / SAMPLE_RATE
    right_phase_inc = 2.0 * math.pi * right_freq / SAMPLE_RATE

    print(f"Binaural: {left_freq:.1f} Hz L / {right_freq:.1f} Hz R  "
          f"(beat={beat_hz:.1f} Hz)  duration={duration_sec:.1f}s")

    left_phase = 0.0
    right_phase = 0.0
    frames = []

    for i in range(total_samples):
        # Envelope
        if i < fade_in_samples:
            env = i / fade_in_samples
        elif i >= total_samples - fade_out_samples:
            env = (total_samples - i) / fade_out_samples
        else:
            env = 1.0

        left_val = math.sin(left_phase) * volume * env
        right_val = math.sin(right_phase) * volume * env
        left_int = int(left_val * 32767)
        right_int = int(right_val * 32767)
        frames.append(struct.pack('<hh', left_int, right_int))

        left_phase += left_phase_inc
        right_phase += right_phase_inc

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)

    with wave.open(output_path, 'w') as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.setnframes(total_samples)
        wf.writeframes(b''.join(frames))

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Wrote: {output_path} ({size_mb:.1f} MB)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate binaural beat WAV')
    parser.add_argument('--output', '-o', required=True, help='Output WAV path')
    parser.add_argument('--duration', '-d', type=float, default=65.0,
                        help='Duration in seconds (default: 65)')
    parser.add_argument('--carrier', '-c', type=float, default=200.0,
                        help='Carrier frequency Hz (default: 200)')
    parser.add_argument('--beat', '-b', type=float, default=6.0,
                        help='Beat frequency Hz — theta=6, alpha=10, delta=2.5, etc.')
    parser.add_argument('--volume', '-v', type=float, default=0.7,
                        help='Volume 0–1 (default: 0.7)')
    args = parser.parse_args()
    generate(args.output, args.duration, args.carrier, args.beat, args.volume)