# Architecture: Hedra Downloader ULTIMATE

## Tech Stack

* **Language:** Python
* **GUI Framework:** `customtkinter` (Dark-themed, modern UI)
* **Core Engine:** `yt-dlp`
* **Media Processing:** Standalone binaries `ffmpeg.exe` and `ffprobe.exe`
* **Image Processing:** `PIL` (Optional, with text fallback)
* **Metadata:** `mutagen` (auto-installs in background if missing)

## File & Data Structure

* **Main Script:** `Hedra Downloader PRO.pyw` (Contains all UI and logic)
* **Local Binaries:** `ffmpeg.exe`, `ffprobe.exe` located alongside the main script.
* **Downloads Output:** `~/Downloads/YT Downloader/Video/` and `~/Downloads/YT Downloader/Audio/`
* **Persistent App Data:** `~/.hedra_downloader/` (Stores `history.json`, `downloaded_archive.txt`, config).

## Core Components

1.  **UI Layout:** Tabview system (Single Video/Audio, Batch Video/Audio, Playlist Video/Audio, Queue, History, Settings). Footer is packed at the bottom.
2.  **JobQueue:** A thread-safe background manager handling concurrent downloads (configurable 1-5 max). 
3.  **Downloader:** `yt-dlp` configured via dynamic dictionaries (`ydl_opts`).
4.  **Threading Model:** Main loop strictly for GUI. All network requests, metadata fetching, and downloading occur in background `threading.Thread` processes.
5.  **Color Palette Theme System:** Configured early during execution (before CTk initialization) from `settings.json`. Theme switching in settings prompts an instant process restart via `os.execv` to safely apply the appearance mode and color tokens across all widgets.
6.  **Segment / Clip Downloader:** Converts start/end timestamps (`hh:mm:ss`) to seconds and injects them into the `yt-dlp` `download_ranges` option, forcing keyframes at cuts via FFmpeg.
7.  **Layout Management:** Layout safety rules dictate that bottom-aligned control bars and boxes are packed first using `side="bottom"` to guarantee visibility on small windows, while textboxes and lists expand (`expand=True, fill="both"`) in the remaining space.
