# Hedra Downloader ULTIMATE (V18)

## 📌 App's Purpose
**Hedra Downloader ULTIMATE** is a powerful, modern GUI application built in Python that allows users to seamlessly download videos, audio, batches, and playlists from YouTube and various other supported websites. It leverages `yt-dlp` for extraction and downloading, `ffmpeg` for post-processing and format conversion, and `customtkinter` for a sleek, dark-themed user interface.

## 🚀 Full Feature List
* **Persistent Concurrent Download Queue**: A dedicated "Queue" tab that manages background downloads. You can stack jobs using the new `➕ Add to Queue` button (which starts them paused), and independently pause, resume, or cancel them. Supports multiple concurrent downloads (configurable in Settings up to 5).
* **Rich Metadata Display**: Both the Queue and History tabs capture and display exact Video Titles, File Size, Quality, and File Formats in real-time.
* **Custom Segment / Clip Download**: Download only a specific segment from a video or audio file by providing a start and/or end time (in `hh:mm:ss` format). Works across Single, Batch, and Playlist tabs.
* **Premium Color Palette Themes**: Switch between three professionally curated color schemes in Settings:
  * *Default*: Modern dark navy theme with sky blue accents.
  * *Pure Dark*: Deep OLED-friendly pure black theme with violet accents.
  * *Light*: Sleek, clean light-gray theme with royal blue and slate accents.
* **Theme-Aware UI Components**: Utility buttons (clipboard paste, clear, file import), dividers, and the bottom footer bar adapt dynamically to the active palette, ensuring consistent and polished visual contrast.
* **Single Video Download**: Download a single video with quality, format, and subtitle options.
* **Single Audio Download**: Extract audio with custom bitrates and formats.
* **Batch Downloads**: Paste multiple URLs (one per line) to download multiple videos or audio files in bulk.
* **Playlist Downloads**: Fetch entire playlists, selectively check/uncheck specific entries, view total estimated size, and download. Playlist item selections are sticky and preserved across format/quality modifications!
* **Independent & Global Progress Tracking**: Queue jobs feature individual progress bars and real-time metric updates (ETA, Speed). A global progress bar at the bottom intelligently averages the progress across all concurrently downloading jobs.
* **Thumbnail Previews**: Displays the thumbnail of the video/audio being downloaded before processing.
* **Smart Auto-Calculations & State Cleanup**: Automatically re-analyzes sizes when you change qualities/formats, and instantly clears out stale data banners and old info boxes the moment you modify a URL input.
* **Interactive History Tab**: Tracks up to 200 recent downloads in a dedicated "History" tab (saved locally). Features a sleek grid layout with exact sizes, true titles, Quality/Format metadata, a clickable "Open Link" button, and an individual delete button for each entry.
* **Global Integrations & Metadata**: 
  * Automatically embeds chapters, descriptions, and thumbnails into Video (`ffmpeg`) and Audio (`mutagen`, automatically installed in the background if missing).
  * Optional SponsorBlock integration to automatically strip sponsored segments from YouTube videos (also strips intros and outros).
* **Global Settings**: 
  * Use browser cookies to bypass age-restrictions or access premium content.
  * Configurable **Max Downloads** (1 to 5) for background concurrency.
  * Configurable speed limits (e.g., "5M") and concurrent fragment connections (1–8).
  * Configurable **Retries** (1–10) for failed downloads.
  * Archive feature to skip previously downloaded files.
* **Cross-Layout Paste Fix**: Ensures that `Ctrl+V` works seamlessly regardless of the user's keyboard layout (e.g., Arabic).
* **Built-in yt-dlp Updater**: Easily update the underlying `yt-dlp` engine from within the app. Falls back to `pip install -U yt-dlp` automatically if the built-in updater fails.
* **Separate Batch Video & Batch Audio Tabs**: Batch mode is split into two dedicated tabs (Batch Video, Batch Audio) — each fully independent with their own options, textbox, thumbnail preview, and download controls.
* **Separate Playlist Video & Playlist Audio Tabs**: Playlist mode is likewise split into two dedicated tabs (Playlist Video, Playlist Audio) for independent management.
* **Keyboard Shortcuts**: `Ctrl+S` starts the download from any URL entry field; `Escape` stops the current active download; `Ctrl+V` / 📋 button pastes from clipboard on any layout.
* **Smart URL Type Hints**: When you paste a playlist URL into a Single tab (or vice versa), the status bar warns you and suggests the correct tab — preventing common user mistakes.
* **Live Playlist Loading Counter**: While a playlist is being analyzed, the status bar shows a live counter ("🎬 Loading… 14 entries fetched so far") so you can see progress as each entry is fetched.
* **Title Bar Download Progress**: While downloading, the window title updates in real-time to show download percentage (e.g., `[47%] Hedra Downloader ULTIMATE V18`).
* **Session Download Counter**: A persistent session counter in the footer shows how many downloads have been completed since the app was opened.
* **"📋 VIEW QUEUE" Shortcut Button**: A permanent button in the footer bar instantly navigates to the Queue tab from anywhere in the app.
* **Per-Tab Status Memory**: Each tab independently remembers its own status message. Switching tabs restores the status bar to the last state for that specific tab.
* **Automatic History Migration**: On first launch, any `history.json` or `downloaded_archive.txt` files found in the old `~/Downloads/YT Downloader/` location are automatically moved to the secure `~/.hedra_downloader/` directory.
* **Indeterminate Pulse Animation**: While fetching metadata, a smooth bouncing progress bar animation runs to visually indicate that the app is working.
* **Clear Finished Jobs Button**: The Queue tab has a "Clear Finished" button that removes all Completed, Error, and Cancelled jobs in one click.
* **Batch Textbox Controls**: The Batch tabs have a 📋 paste button and a ✕ clear button alongside the textbox for quick workflow.
* **Custom Save Path per Tab**: Every tab (Single, Batch, Playlist) has its own "Save to:" path selector with a Browse button to choose a custom output folder.
* **Embedded Thumbnail in Audio**: All audio downloads always have thumbnails embedded (using `EmbedThumbnail` post-processor), independent of the global metadata toggle.
* **Scrollable Settings Tab**: The Settings tab uses a scrollable frame so content like the About section, Tab Guide, and keyboard shortcuts are always accessible regardless of window size.
* **Inline Tab Guide in Settings**: The Settings tab contains a built-in guide describing the purpose of every tab, making the app self-documenting for new users.
* **Supported Websites Panel**: The Settings tab lists supported platforms (YouTube, Facebook, Twitter/X, Instagram, TikTok, Twitch, Reddit, Vimeo, SoundCloud, Dailymotion, and 1000+ more).
* **"Open Folder" Buttons in Settings**: Dedicated buttons to open the Video and Audio download folders directly in the system file explorer, using the correct cross-platform command (`os.startfile` / `open` / `xdg-open`).
* **Queue "Clear Finished" Button**: Removes all jobs in terminal states (Completed, Error, Cancelled) in one click, keeping the queue clean.
* **Playlist Organized into Subfolders**: Playlist downloads are saved into a subfolder named after the playlist title inside the selected output directory, with items prefixed by their playlist index (e.g., `01 - Title.mp4`).
* **Video Quality Options**: 8K (4320p), 4K (2160p), 1440p, Best Available, 1080p, 720p, 480p, 360p.
* **Video File Type Options**: Default, mp4, mkv.
* **Universal URL Expander & Normalizer**: Automatically normalizes and expands mobile share and embed links for TikTok (`vm.tiktok.com`, `vt.tiktok.com`, `tiktxk.com`), Twitter/X (`x.com`, `fixupx.com`, `vxtwitter.com`), Facebook (`fb.watch`, `/share/r/`, `/share/v/`), YouTube Music (`music.youtube.com`), Reddit (`redd.it/`), and Instagram (`ddinstagram.com`, `/share/reel/`), while cleanly stripping tracking parameters (`?utm_*`, `?si=`, `?igsh=`, `?mibextid=`, `?t=`, `?s=`).
* **Batch Auto-Deduplicator & Cleaner (`🧹`)**: Instantly strips blank lines, removes duplicate URLs (preserving order), normalizes each link, and reports cleaned counts directly on Batch Video and Batch Audio tabs.
* **1-Click Download Presets Bar**: One-click quick profile buttons (`🎬 4K Max`, `📱 1080p MP4`, `⚡ 720p Fast`, `🎵 320k MP3`, `🎧 Studio FLAC`, `📻 128k Light`, `🍎 M4A Apple`) on Single and Batch tabs for instant configuration without manually setting dropdowns.
* **Live Network Monitor & Bandwidth Graph**: Real-time bandwidth gauge and animated speed graph in the Queue tab tracking active download throughput, session peak rate, active workers, and completed job statistics.
* **Informative Diagnostic Error Handling**: Clear guidance in the status bar and info boxes when platforms like Instagram require browser cookies/login, directly advising how to configure it in Settings.
* **Multi-Format Subtitles (MP4, MKV & Sidecar .SRT / .VTT)**: Subtitles can now be embedded directly into MP4 (as soft-subs) and MKV videos, or saved as separate `.srt` / `.vtt` sidecar files in the output directory.
* **Drag and Drop (DnD) File & Link Import**: Drag `.txt` link lists directly into Batch tabs or drop links/files onto Single tabs to auto-populate and analyze immediately.
* **Desktop Toast Notifications & Audio Chimes**: Dispatches native Windows 10/11 desktop notifications and subtle audio chimes when downloads or queues complete.
* **Direct Media Playback & Explorer Location in History**: History tab includes **▶ Play** (opens media in default player like VLC) and **📁 Folder** (highlights the file in Windows Explorer).
* **Audio Quality Options**: Best (256 kbps), High (~192 kbps), Medium (~128 kbps), Low (64 kbps).

## 📂 Folder Structure
```text
a:\Downloader\V19\
│
├── Hedra Downloader PRO.pyw    # Main Python script containing all UI and logic
├── ffmpeg.exe                  # Standalone FFmpeg binary for media processing
├── ffprobe.exe                 # Standalone FFprobe binary for media inspection
└── README.md                   # Project documentation (this file)
```
*Note: At runtime, the app creates `~/Downloads/YT Downloader/Video/` and `~/Downloads/YT Downloader/Audio/` for downloaded media, but securely stores configuration and history data (like `history.json` and `downloaded_archive.txt`) in a hidden user directory at `~/.hedra_downloader/` to prevent accidental deletion.*

## ⚙️ How Each Component Works
* **UI (`customtkinter`)**: The graphical interface is built with CustomTkinter, providing a modern, dark-themed look with tabs for different functionalities (Single Video, Single Audio, Batch Video, Batch Audio, Playlist Video, Playlist Audio, Queue, History, Settings).
* **Job Queue (`JobQueue`)**: A thread-safe background queue manager that handles concurrent downloading of multiple jobs (up to the user-defined max). It supports independent pause, resume, and cancel operations for each job, using per-job `threading.Event` cancel tokens to safely interrupt downloads without affecting others. A `queue_cancel` master event is also available.
* **Downloader (`yt-dlp`)**: The core engine configured via dynamic dictionaries (`ydl_opts`). It handles URL parsing, metadata extraction, and streaming.
* **Media Processing (`ffmpeg.exe` & `ffprobe.exe`)**: Used internally by `yt-dlp` as post-processors to merge separate video and audio streams, embed subtitles (MP4 mov_text / MKV subrip), and convert audio into target formats (MP3, FLAC, WAV, M4A).
* **Threading**: All downloads and metadata fetching functions are executed in background threads (`threading.Thread`) to ensure the main UI loop remains responsive. It features a cancel event (`threading.Event`) to stop downloads gracefully.
* **Image Processing (`PIL`)**: Fetches thumbnails from URLs in the background and resizes/crops them into `CTkImage` objects for previewing. Falls back gracefully with a text placeholder if Pillow is not installed.

## ⚠️ Important Notes About the Codebase
* **Source of Truth**: This `README.md` is the source of truth for the project. Always read it before making changes and update it after any modifications.
* **Aria2c Abandoned**: Multi-threaded external downloaders like `aria2c` were previously implemented but removed due to fatal process-spawning bugs that caused downloads to continue silently in the background when users cancelled the python thread. Ultimate speeds are achieved via `yt-dlp`'s concurrent fragment settings.
* **File Naming vs Variables**: The folder is `V19` and the `APP_VERSION` variable inside `Hedra Downloader PRO.pyw` has been updated to match `"V19"`. 
* **Custom Paste Binding**: There is a global event listener for `Ctrl+V` (`_global_paste_handler`) to fix paste bugs with foreign language keyboard layouts. It intercepts keycode `86` on `<Control-KeyPress>` and explicitly suppresses `<Control-KeyPress-v>` and `<Control-KeyPress-V>` to prevent double-paste.
* **Error Handling & Stale States**: The UI implements intelligent traces (`attach_auto_check` and `bind_url_change_clear`) that automatically recalculate sizes upon option changes and clear out outdated analysis information the instant a user starts editing an input field. `attach_stale_traces` handles the amber warning banners on Playlist and Batch tabs.
* **Footer Build Order**: The footer (progress bar, status label, session counter, VIEW QUEUE button) is packed with `side="bottom"` **before** the tabview is packed, which is critical — reversing this order breaks the layout.
* **Per-Job Cancel Events**: Each active queue job gets its own `threading.Event` in `JobQueue.cancel_events[jid]`. This allows cancelling one job without stopping others. The global `cancel_event` is separate and used only for non-queue (legacy) operations.
* **Silent Dependency Installations**: Missing dependencies (such as `mutagen`, `windnd`, etc.) are silently installed via `pip` in a background daemon thread on startup using `creationflags=0x08000000` (no console window on Windows).
* **Pillow Optional**: PIL/Pillow is fully optional. The `PIL_AVAILABLE` flag gates all thumbnail code, and a graceful fallback text is shown if it's missing.
* **Settings Tab Scrollable**: The Settings tab wraps all content in a `CTkScrollableFrame` so all sections and controls are visible even at minimum window size (800×600).
* **Palette Persistence & App Restart**: Themes are read from `settings.json` early during startup before any UI components are created. Switching themes in Settings prompts the user and executes a safe instant app restart (`os.execv`) to reload all widget tokens cleanly.
* **Batch Layout Design**: To prevent widgets from being pushed off-screen or stacked incorrectly on resize, the batch tabs pack the bottom controls frame first with `side="bottom"`, the top configuration panel next with `fill="both", expand=True`, and the check button last to sit cleanly in the remaining space.

