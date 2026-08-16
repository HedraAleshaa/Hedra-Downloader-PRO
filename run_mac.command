#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "================================================="
echo "   Hedra Downloader PRO 2.0 - macOS Launcher"
echo "================================================="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not found. Please install Python 3 or Homebrew."
    exit 1
fi

# Check FFmpeg (optional notice)
if ! command -v ffmpeg &> /dev/null; then
    echo "ℹ Notice: For highest quality audio extraction, install FFmpeg via:"
    echo "  brew install ffmpeg"
fi

# Install dependencies silently
echo "⚙ Checking dependencies..."
python3 -m pip install -r requirements.txt --quiet

# Launch GUI
echo "🚀 Launching Hedra Downloader PRO..."
python3 "Hedra Downloader PRO.pyw" &
