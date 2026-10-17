#!/usr/bin/env python3
"""Render a BishopTech p5.js HTML sketch into a background MP4 for Remotion.

Runs headless Chromium through Playwright, drives the sketch one frame at a
time (so the output is deterministic and does not depend on wall-clock speed),
then encodes the frames with ffmpeg.

Usage:
  python3 scripts/render_background.py \
      --html backgrounds/2026-08-09-vertical-04-curl-field-weave.html \
      --out  remotion/public/backgrounds/theta.mp4 \
      --duration 65
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

OUT_W, OUT_H = 1080, 1920


def capture_frames(html_path, frames_dir, duration_sec, fps, cap_w, cap_h):
    """Drive the sketch frame by frame and write JPEGs to frames_dir."""
    from playwright.sync_api import sync_playwright

    html_url = "file://" + os.path.abspath(html_path) + "?obs=1"
    total_frames = int(round(duration_sec * fps))
    print(f"[capture] {os.path.basename(html_path)} -> {total_frames} frames "
          f"@ {fps}fps ({cap_w}x{cap_h})", flush=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--no-sandbox", "--disable-gpu", "--use-gl=swiftshader"])
        page = browser.new_page(
            viewport={"width": cap_w, "height": cap_h},
            device_scale_factor=1)

        # Take over requestAnimationFrame before any page script runs, so p5's
        # draw loop advances only when we tell it to.
        page.add_init_script("""
            window.__rq = [];
            window.requestAnimationFrame = function (cb) {
                window.__rq.push(cb);
                return window.__rq.length;
            };
            window.__step = function (t) {
                var cbs = window.__rq;
                window.__rq = [];
                for (var i = 0; i < cbs.length; i++) {
                    try { cbs[i](t); } catch (e) { window.__err = String(e); }
                }
                return cbs.length;
            };
        """)

        page.goto(html_url, wait_until="load", timeout=60000)
        page.wait_for_selector("canvas", timeout=30000)
        page.wait_for_timeout(400)          # let setup() finish

        pending = page.evaluate("window.__step(0)")
        print(f"[capture] first step produced {pending} callback(s)", flush=True)

        for i in range(total_frames):
            page.evaluate("window.__step(performance.now())")
            page.screenshot(
                path=os.path.join(frames_dir, f"f{i:06d}.jpg"),
                type="jpeg", quality=82,
                clip={"x": 0, "y": 0, "width": cap_w, "height": cap_h})
            if (i + 1) % 240 == 0:
                print(f"[capture]   {i + 1}/{total_frames}", flush=True)

        err = page.evaluate("window.__err || ''")
        if err:
            print(f"[capture] page error (non-fatal): {err}", flush=True)

        browser.close()


def encode(frames_dir, out_path, fps):
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    pattern = os.path.join(frames_dir, "f%06d.jpg")
    cmd = [
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pattern,
        "-vf", f"scale={OUT_W}:{OUT_H}:flags=lanczos",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "20", "-preset", "veryfast", "-an",
        out_path,
    ]
    print("\n$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"[encode] {out_path} ({size_mb:.1f} MB)", flush=True)


def main():
    ap = argparse.ArgumentParser(description="Render an HTML sketch to MP4")
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", "-d", type=float, default=65.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=1280)
    args = ap.parse_args()

    if not os.path.exists(args.html):
        print(f"ERROR: html not found: {args.html}")
        sys.exit(1)

    frames_dir = tempfile.mkdtemp(prefix="bgframes-")
    try:
        capture_frames(args.html, frames_dir, args.duration, args.fps,
                       args.width, args.height)
        encode(frames_dir, args.out, args.fps)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
