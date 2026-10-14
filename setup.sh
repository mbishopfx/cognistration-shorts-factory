#!/usr/bin/env bash
set -euo pipefail

echo "============================================"
echo " Cognistration Shorts Factory — Setup"
echo "============================================"
echo ""

# --- Node / Remotion ---
echo "[1/4] Installing Node dependencies (Remotion)..."
cd remotion
npm install
cd ..
echo "  Done."

# --- Python ---
echo "[2/4] Creating Python virtual environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  Done."

# --- Playwright (for background pre-rendering, optional) ---
echo "[3/4] Installing Playwright browsers (optional)..."
python3 -m playwright install chromium 2>/dev/null || echo "  Playwright skipped (not needed for core rendering)"
echo "  Done."

# --- Verify ---
echo "[4/4] Verifying tools..."
echo -n "  ffmpeg: "
ffmpeg -version 2>/dev/null | head -1 || echo "NOT FOUND — install with 'brew install ffmpeg'"
echo -n "  node:   "
node --version 2>/dev/null || echo "NOT FOUND"
echo -n "  python: "
python3 --version 2>/dev/null || echo "NOT FOUND"
echo -n "  remotion: "
cd remotion && npx remotion --version 2>/dev/null || echo "checking..." && cd ..

echo ""
echo "============================================"
echo " Setup complete!"
echo ""
echo " Next steps:"
echo " 1. Place cognistration-mark.png in remotion/public/images/"
echo " 2. Place service-account-key.json in scripts/"
echo " 3. Read AGENT_GUIDE.md"
echo "============================================"