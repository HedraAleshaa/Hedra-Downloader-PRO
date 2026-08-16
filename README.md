<div align="center">

# 🚀 Hedra Downloader PRO `2.0`
**The Ultimate, Modern, and High-Performance Media Downloader for Windows**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![yt--dlp](https://img.shields.io/badge/Engine-yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://github.com/yt-dlp/yt-dlp)
[![FFmpeg](https://img.shields.io/badge/Processing-FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white)](https://ffmpeg.org/)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-1f538d?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>A sleek, user-friendly desktop application crafted to download videos, audios, clips, batches, and playlists with maximum quality and zero friction.</b>
</p>

---

</div>

## ✨ Why Hedra Downloader PRO?

Hedra Downloader PRO combines the industry-leading extraction power of `yt-dlp` and `ffmpeg` with a handcrafted, modern desktop experience built from the ground up for simplicity and speed.

<table>
  <tr>
    <td width="50%">
      <h3>🔊 Audio Volume Booster & Silence Trimmer</h3>
      Boost quiet dialogues and audio tracks up to +12 dB with built-in DSP loudness normalization and smart silence trimming for both video and audio streams.
    </td>
    <td width="50%">
      <h3>🔍 Search & Filter in Queue & History</h3>
      Instantly search downloads and history by title, URL, or format with real-time status filtering (All, Downloading, Paused, Pending, Failed).
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📊 Live Bandwidth & Queue Monitor</h3>
      Track real-time network throughput with an animated speed graph, session peak monitor, and concurrent worker queue with pause, resume, and priority controls.
    </td>
    <td width="50%">
      <h3>💬 Smart Multilingual Subtitles</h3>
      Choose your preferred language (English, Arabic, Spanish, French, German, Japanese, etc.) — the downloader automatically searches for official captions and seamlessly falls back to auto-generated transcripts.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🖼️ Rich History with Instant Play</h3>
      View past downloads with automatic video frame thumbnails, file size tags, and 1-click <code>▶ Play</code> (opens in your default media player) and <code>📁 Folder</code> location buttons.
    </td>
    <td width="50%">
      <h3>🧹 Smart Batch Cleaner & Expander</h3>
      Paste raw link lists — the built-in cleaner automatically strips tracking parameters (<code>?utm_*</code>, <code>?si=</code>, <code>?igsh=</code>), removes duplicates, and normalizes mobile share links.
    </td>
  </tr>
</table>

---

## 🎯 Features at a Glance

| Feature | Description |
| :--- | :--- |
| **🎬 Single Video & Audio** | Download from 480p up to 8K Ultra HD or extract pristine MP3, FLAC, AAC, WAV, and M4A audio. |
| **📦 Batch Downloader** | Queue dozens of links simultaneously with one-click paste and auto-deduplication. |
| **📑 Playlist Studio** | Fetch full YouTube / SoundCloud playlists, selectively check/uncheck items, and organize into subfolders. |
| **🎯 Drag & Drop** | Drag `.txt` link lists or media URLs directly onto any tab for instant analysis. |
| **🎨 3 Curated Themes** | Switch between *Default Navy*, *OLED Pure Dark*, and *Clean Light* palettes in Settings. |
| **🔒 Universal Paste** | Cross-layout keyboard fix ensures `Ctrl + V` works reliably across Arabic, French, and all language layouts. |
| **🏷️ Metadata & Artwork** | Automatically embeds chapters, track descriptions, and cover artwork into media files. |
| **🚫 SponsorBlock** | Optional integration to automatically strip sponsored segments, intros, and outros. |
| **🍪 Cookie Integration** | Load `cookies.txt` or browser sessions (Chrome, Firefox, Edge, Brave) to bypass age gates and login checkpoints. |

---

## 🌐 Supported Websites (1,000+ Platforms)

Hedra Downloader PRO natively supports over 1,000 video and audio streaming sites, including:

<div align="center">

| YouTube | Facebook | Twitter / X | Instagram | TikTok | Twitch | Reddit | Vimeo | SoundCloud | Dailymotion |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🔴 | 🔵 | ⚫ | 🟣 | ⬛ | 🟣 | 🟠 | 🔷 | 🔶 | 🔵 |

*...and virtually every platform supported by the yt-dlp ecosystem.*

</div>

---

## ⌨️ Keyboard Shortcuts & Gestures

| Shortcut / Gesture | Action | Description |
| :--- | :--- | :--- |
| <kbd>Ctrl + V</kbd> | **Universal Paste** | Paste URL reliably on any keyboard layout (Arabic, French, etc.) |
| <kbd>Ctrl + S</kbd> | **Instant Download** | Start download directly from any single URL entry field |
| <kbd>Escape</kbd> | **Emergency Stop** | Instantly abort and cleanly stop all active downloads |
| <kbd>Enter</kbd> | **Quick Check** | Analyze link size, duration, and thumbnail preview |
| **Drag & Drop** | **Direct Import** | Drop `.txt` link lists or URLs directly onto the window |
| `🧹` **Button** | **Batch Deduplicator** | Clean blank lines, normalize shortlinks, and remove duplicates |

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10 / 11**
- **Python 3.10+** (Ensure *"Add Python to PATH"* is checked during install)

### 1. Clone the Repository
```bash
git clone https://github.com/HedraAleshaa/Hedra-Downloader-PRO.git
cd Hedra-Downloader-PRO
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch Application
```bash
python "Hedra Downloader PRO.pyw"
```
*(Or simply double-click `Hedra Downloader PRO.pyw` in Windows Explorer)*

---

## 📂 Project Structure

```text
Hedra-Downloader-PRO/
├── Hedra Downloader PRO.pyw    # Main application (UI, Queue Engine & Downloader)
├── ffmpeg.exe                  # Local high-performance FFmpeg binary
├── ffprobe.exe                 # Local FFprobe media inspection binary
├── requirements.txt            # Python dependencies (customtkinter, yt-dlp, pillow, mutagen)
├── README.md                   # Documentation & Feature showcase
└── LICENSE                     # Open Source MIT License
```

---

<div align="center">

**Developed with ❤️ by [Hedra Aleshaa](https://github.com/HedraAleshaa)**  
*If you find this project useful, feel free to give it a ⭐ on GitHub!*

</div>
