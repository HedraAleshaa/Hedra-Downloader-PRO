import customtkinter as ctk
import yt_dlp
import threading
import os
import subprocess
import sys
import platform
import time
import json
import urllib.request
import io
import re
from tkinter import messagebox
import webbrowser

# Optional PIL for thumbnail preview
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Optional windnd for Drag and Drop
try:
    import windnd
    WINDND_AVAILABLE = True
except ImportError:
    WINDND_AVAILABLE = False

def check_deps():
    def _install_background():
        to_install = []
        try:
            import mutagen
        except ImportError:
            to_install.append("mutagen")
        try:
            import windnd
        except ImportError:
            to_install.append("windnd")
        if to_install:
            subprocess.run([sys.executable, "-m", "pip", "install"] + to_install,
                           capture_output=True,
                           creationflags=0x08000000 if os.name == 'nt' else 0)
    threading.Thread(target=_install_background, daemon=True).start()
check_deps()

# ==========================================
#  SYSTEM SETUP & BUNDLING
# ==========================================
def get_ffmpeg_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

APP_VERSION  = "V19"
APP_AUTHOR   = "Hedra Aleshaa"
FFMPEG_DIR   = get_ffmpeg_path()
BASE_DIR     = os.path.join(os.path.expanduser("~"), "Downloads", "YT Downloader")
VID_DIR      = os.path.join(BASE_DIR, "Video")
AUD_DIR      = os.path.join(BASE_DIR, "Audio")
DATA_DIR     = os.path.join(os.path.expanduser("~"), ".hedra_downloader")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
ARCHIVE_FILE = os.path.join(DATA_DIR, "downloaded_archive.txt")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
QUEUE_FILE = os.path.join(DATA_DIR, "queue.json")
os.makedirs(VID_DIR, exist_ok=True)
os.makedirs(AUD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

try:
    old_hist = os.path.join(BASE_DIR, "history.json")
    if os.path.exists(old_hist) and not os.path.exists(HISTORY_FILE):
        import shutil; shutil.move(old_hist, HISTORY_FILE)
    old_arch = os.path.join(BASE_DIR, "downloaded_archive.txt")
    if os.path.exists(old_arch) and not os.path.exists(ARCHIVE_FILE):
        import shutil; shutil.move(old_arch, ARCHIVE_FILE)
except Exception:
    pass

# ==========================================
#  CONSTANTS
# ==========================================
VIDEO_QUALITY_MAP = {
    "Max 8K (4320p)": "bestvideo[height<=4320]+bestaudio/best",
    "Max 4K (2160p)": "bestvideo[height<=2160]+bestaudio/best",
    "Max 1440p":      "bestvideo[height<=1440]+bestaudio/best",
    "Best Available": "bestvideo+bestaudio/best",
    "Max 1080p":      "bestvideo[height<=1080]+bestaudio/best",
    "Max 720p":       "bestvideo[height<=720]+bestaudio/best",
    "Max 480p":       "bestvideo[height<=480]+bestaudio/best",
    "Max 360p":       "bestvideo[height<=360]+bestaudio/best",
}
AUDIO_BITRATE_MAP = {
    "Best — Highest bitrate": 256,
    "High — ~192 kbps":       192,
    "Medium — ~128 kbps":     128,
    "Low — Smallest file":     64,
}
AUDIO_QUALITY_MAP = {
    "Best — Highest bitrate": "0",
    "High — ~192 kbps":       "2",
    "Medium — ~128 kbps":     "5",
    "Low — Smallest file":    "9",
}
SUBTITLE_LANG_MAP = {
    "English subtitles":             ("en.*",    False),
    "Auto-generated (if available)": ("en.*",    True),
    "Arabic  (ar)":                  ("ar",      False),
    "French  (fr)":                  ("fr",      False),
    "Spanish (es)":                  ("es",      False),
    "German  (de)":                  ("de",      False),
    "Japanese (ja)":                 ("ja",      False),
    "Chinese S. (zh-Hans)":          ("zh-Hans", False),
    "Portuguese (pt)":               ("pt",      False),
    "Korean  (ko)":                  ("ko",      False),
}
SUBTITLE_MODES = [
    "Embed in Video",
    "Separate .srt file",
    "Separate .vtt file",
    "Embed + .srt file"
]
COOKIE_BROWSERS = ["None", "chrome", "firefox", "edge", "brave", "safari"]

SUPPORTED_SITES = [
    ("YouTube",     "youtube.com",    "#FF0000"),
    ("Facebook",    "facebook.com",   "#1877F2"),
    ("Twitter / X", "x.com",          "#000000"),
    ("Instagram",   "instagram.com",  "#E1306C"),
    ("TikTok",      "tiktok.com",     "#010101"),
    ("Twitch",      "twitch.tv",      "#9146FF"),
    ("Reddit",      "reddit.com",     "#FF4500"),
    ("Vimeo",       "vimeo.com",      "#1AB7EA"),
    ("SoundCloud",  "soundcloud.com", "#FF5500"),
    ("Dailymotion", "dailymotion.com","#0066DC"),
]

TAB_NAMES = [
    "Single Video", "Single Audio",
    "Batch Video",  "Batch Audio",
    "Playlist Video", "Playlist Audio",
    "Queue", "History", "Settings",
]

# ==========================================
#  COLOR PALETTES
# ==========================================
PALETTES = {
    "Default": {
        "appearance": "dark",
        "COL_CHECK":   "#1E293B",
        "COL_CHECKH":  "#0F172A",
        "COL_DL":      "#2563EB",
        "COL_DLH":     "#1D4ED8",
        "COL_DARK":    "#0B0F19",
        "COL_PANEL":   "#151B2B",
        "COL_TEXT":    "#E2E8F0",
        "COL_MUTED":   "#94A3B8",
        "COL_ACCENT":  "#38BDF8",
        "COL_SUCCESS": "#34D399",
        "COL_WARN":    "#FBBF24",
        "COL_ERR":     "#F87171",
        "COL_FOOTER":  "#020617",
    },
    "Pure Dark": {
        "appearance": "dark",
        "COL_CHECK":   "#111111",
        "COL_CHECKH":  "#000000",
        "COL_DL":      "#7C3AED",
        "COL_DLH":     "#6D28D9",
        "COL_DARK":    "#000000",
        "COL_PANEL":   "#0D0D0D",
        "COL_TEXT":    "#FFFFFF",
        "COL_MUTED":   "#6B7280",
        "COL_ACCENT":  "#A78BFA",
        "COL_SUCCESS": "#34D399",
        "COL_WARN":    "#FBBF24",
        "COL_ERR":     "#F87171",
        "COL_FOOTER":  "#000000",
    },
    "Light": {
        "appearance": "light",
        "COL_CHECK":   "#CBD5E1",
        "COL_CHECKH":  "#94A3B8",
        "COL_DL":      "#2563EB",
        "COL_DLH":     "#1D4ED8",
        "COL_DARK":    "#F1F5F9",
        "COL_PANEL":   "#E2E8F0",
        "COL_TEXT":    "#0F172A",
        "COL_MUTED":   "#475569",
        "COL_ACCENT":  "#2563EB",
        "COL_SUCCESS": "#059669",
        "COL_WARN":    "#D97706",
        "COL_ERR":     "#DC2626",
        "COL_FOOTER":  "#CBD5E1",
    },
}
_ACTIVE_PALETTE = "Default"

def _load_palette_tokens(name):
    """Push palette values into global color vars (called before UI is built)."""
    global COL_CHECK, COL_CHECKH, COL_DL, COL_DLH, COL_DARK, COL_PANEL
    global COL_TEXT, COL_MUTED, COL_ACCENT, COL_SUCCESS, COL_WARN, COL_ERR
    global COL_FOOTER, _ACTIVE_PALETTE
    p = PALETTES.get(name, PALETTES["Default"])
    _ACTIVE_PALETTE = name
    COL_CHECK   = p["COL_CHECK"]
    COL_CHECKH  = p["COL_CHECKH"]
    COL_DL      = p["COL_DL"]
    COL_DLH     = p["COL_DLH"]
    COL_DARK    = p["COL_DARK"]
    COL_PANEL   = p["COL_PANEL"]
    COL_TEXT    = p["COL_TEXT"]
    COL_MUTED   = p["COL_MUTED"]
    COL_ACCENT  = p["COL_ACCENT"]
    COL_SUCCESS = p["COL_SUCCESS"]
    COL_WARN    = p["COL_WARN"]
    COL_ERR     = p["COL_ERR"]
    COL_FOOTER  = p["COL_FOOTER"]
    ctk.set_appearance_mode(p["appearance"])

# Apply default palette tokens at startup (overridden below if saved)
_load_palette_tokens("Default")

# ── Load saved palette BEFORE any UI is built ──────────────────────
try:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as _f:
            _early = json.load(_f)
        if _early.get("palette") in PALETTES:
            _load_palette_tokens(_early["palette"])
except Exception:
    pass

# ==========================================
#  THEME & WINDOW
# ==========================================
ctk.set_default_color_theme("blue")

# ==========================================
#  FONT TOKENS  (palette-independent)
# ==========================================
LABEL_FONT  = ("Segoe UI", 13, "bold")
ENTRY_FONT  = ("Segoe UI", 14)
BTN_MAIN    = ("Segoe UI", 15, "bold")
BTN_SUB     = ("Segoe UI", 13)
MONO_FONT   = ("Consolas", 12)

app = ctk.CTk()
app.geometry("950x700")
app.minsize(800, 600)
app.title(f"Hedra Downloader ULTIMATE {APP_VERSION}")

# ==========================================
#  GLOBAL STATE
# ==========================================
cancel_event        = threading.Event()
MANAGED_BUTTONS     = []
_tab_status         = {name: ("Ready.", COL_MUTED) for name in TAB_NAMES}
_session_dl_count   = 0
_pulse_running      = False   # indeterminate progress animation flag

# ==========================================
#  ARABIC / ANY-LAYOUT PASTE FIX
# ==========================================
def _global_paste_handler(event):
    if event.keycode != 86:
        return
    widget = event.widget
    try:
        text = app.clipboard_get()
        if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            try:
                idx = widget.index("insert")
                widget.insert(idx, text)
            except Exception:
                widget.insert("end", text)
            return "break"
    except Exception:
        pass

def _install_paste_fix():
    app.bind_all("<Control-KeyPress>", _global_paste_handler, add="+")
    app.bind_all("<Control-KeyPress-v>", lambda e: None)
    app.bind_all("<Control-KeyPress-V>", lambda e: None)

# ==========================================
#  INDETERMINATE PROGRESS PULSE
#  Shows animated bar while fetching metadata
# ==========================================
def _start_pulse():
    global _pulse_running
    _pulse_running = True
    _pulse_step(0, 1)

def _pulse_step(val, direction):
    if not _pulse_running:
        return
    progress_bar.set(val)
    new_val = val + direction * 0.015
    if new_val >= 1.0:
        new_val, direction = 1.0, -1
    elif new_val <= 0.0:
        new_val, direction = 0.0, 1
    app.after(16, lambda: _pulse_step(new_val, direction))

def _stop_pulse():
    global _pulse_running
    _pulse_running = False
    progress_bar.set(0)
    pct_label.configure(text=" 0% ")

# ==========================================
#  DOWNLOAD HISTORY
# ==========================================
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_history_entry(title, url, mode, size_str, quality="—", file_type="—", file_path=""):
    history = load_history()
    history.insert(0, {
        "time":      time.strftime("%Y-%m-%d %H:%M"),
        "title":     title,
        "url":       url,
        "mode":      mode,
        "size":      size_str,
        "quality":   quality,
        "file_type": file_type,
        "file_path": file_path or "",
    })
    history = history[:200]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ==========================================
#  PERSISTENT SETTINGS
# ==========================================
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_settings():
    """Serialize all Settings-tab controls to disk."""
    try:
        data = {
            "cookie_browser": global_cookie_var.get(),
            "cookie_file":    global_cookie_file_var.get(),
            "max_downloads":  global_max_downloads_var.get(),
            "ratelimit":      global_ratelimit_entry.get(),
            "retries":        global_retries_var.get(),
            "concurrent":     global_concurrent_var.get(),
            "archive":        global_archive_var.get(),
            "sponsorblock":   global_sponsorblock_var.get(),
            "embed_metadata": global_metadata_var.get(),
            "subtitle_mode":  global_sub_mode_var.get(),
            "notify_toast":   global_notify_toast_var.get(),
            "notify_sound":   global_notify_sound_var.get(),
            "proxy":          global_proxy_entry.get(),
            "palette":        _ACTIVE_PALETTE,
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ==========================================
#  CROSS-PLATFORM LAUNCHERS & NOTIFIERS
# ==========================================
def open_folder(path):
    os.makedirs(path, exist_ok=True)
    system = platform.system()
    if system == "Windows":
        os.startfile(path)
    elif system == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

def open_file_direct(path):
    """Launch file directly in user's default OS media player."""
    if not path or not os.path.exists(path): return False
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.run(["open", path])
        else:
            subprocess.run(["xdg-open", path])
        return True
    except Exception:
        return False

def show_in_explorer(path):
    """Select and highlight the file inside Windows Explorer."""
    if not path or not os.path.exists(path): return False
    try:
        system = platform.system()
        if system == "Windows":
            subprocess.run(f'explorer /select,"{os.path.normpath(path)}"', shell=True)
        elif system == "Darwin":
            subprocess.run(["open", "-R", path])
        else:
            open_folder(os.path.dirname(path))
        return True
    except Exception:
        return False

def find_downloaded_file(title, mode=""):
    """Fallback locator to find downloaded file in target folders if path was modified."""
    if not title or title in ("—", "Unknown"): return None
    search_dirs = [AUD_DIR if "Audio" in mode else VID_DIR, VID_DIR, AUD_DIR]
    clean_title = re.sub(r'[^\w\s-]', '', title).lower()
    for sdir in search_dirs:
        if not os.path.exists(sdir): continue
        for root, _, files in os.walk(sdir):
            for f in files:
                f_clean = re.sub(r'[^\w\s-]', '', f).lower()
                if clean_title and (clean_title in f_clean or f_clean.startswith(clean_title[:18])):
                    return os.path.join(root, f)
    return None

def send_notification(title, message):
    """Dispatch subtle sound chime and native Windows desktop toast notification."""
    # 1. Chime
    try:
        if 'global_notify_sound_var' in globals() and global_notify_sound_var.get():
            import winsound
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass
    # 2. Toast
    try:
        if 'global_notify_toast_var' in globals() and global_notify_toast_var.get():
            def _toast():
                try:
                    clean_t = str(title).replace("'", "''").replace('"', '')
                    clean_m = str(message).replace("'", "''").replace('"', '')
                    ps_cmd = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName('text')
$textNodes.Item(0).AppendChild($template.CreateTextNode('{clean_t}')) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode('{clean_m}')) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Hedra Downloader')
$notifier.Show($toast)
"""
                    subprocess.run(['powershell', '-WindowStyle', 'Hidden', '-Command', ps_cmd], capture_output=True, creationflags=0x08000000 if os.name == 'nt' else 0)
                except Exception:
                    pass
            threading.Thread(target=_toast, daemon=True).start()
    except Exception:
        pass

# ==========================================
#  HELPERS
# ==========================================
def format_size(bytes_size):
    if not bytes_size:
        return "Unknown"
    size = float(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def format_seconds_to_time(seconds):
    """Convert float/int seconds into clean mm:ss or hh:mm:ss string."""
    if seconds is None or seconds < 0:
        return "00:00"
    sec = int(round(seconds))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_audio_bitrate(q_var):
    return AUDIO_BITRATE_MAP.get(q_var.get(), 256)

def extract_size_from_info(info, is_audio=False, audio_bitrate=None, seg_start=None, seg_end=None):
    sz = 0
    if 'entries' in info:
        total = 0
        for entry in info['entries']:
            if entry:
                total += extract_size_from_info(entry, is_audio, audio_bitrate, seg_start, seg_end)
        return total
    if is_audio and audio_bitrate and info.get('duration'):
        sz = int((audio_bitrate * 1000 * info['duration']) / 8)
    elif 'requested_formats' in info:
        sz = sum(f.get('filesize', 0) or f.get('filesize_approx', 0)
                 for f in info['requested_formats'])
        if sz <= 0:
            sz = info.get('filesize', 0) or info.get('filesize_approx', 0)
    else:
        sz = info.get('filesize', 0) or info.get('filesize_approx', 0)
        
    if sz and (seg_start is not None) and info.get('duration'):
        duration = info.get('duration')
        start = seg_start
        end = seg_end if seg_end is not None else duration
        if end > duration: end = duration
        if end > start:
            sz = int(sz * (end - start) / duration)
    return sz

def normalize_media_url(url):
    """Normalize and clean various site URLs (TikTok, Twitter/X, Instagram, Facebook, Reddit, Pinterest, YouTube Music)."""
    if not url or not isinstance(url, str):
        return ""
    u = url.strip()
    
    # ── 1. Instagram ──────────────────────────────────────────
    u = re.sub(r'https?://(?:www\.)?(?:dd|kk|ee)?instagram(?:ez)?\.com', 'https://www.instagram.com', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?instagram\.com)/share/(?:video|reel|reels)/([^/?#&]+)/?', r'\1/reel/\2', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?instagram\.com)/share/p/([^/?#&]+)/?', r'\1/p/\2', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?instagram\.com)/share/tv/([^/?#&]+)/?', r'\1/tv/\2', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?instagram\.com)/share/([^/?#&]+)/?', r'\1/p/\2', u, flags=re.IGNORECASE)

    # ── 2. Twitter / X ─────────────────────────────────────────
    u = re.sub(r'https?://(?:www\.)?(?:vx|fx)?twitter\.com', 'https://twitter.com', u, flags=re.IGNORECASE)
    u = re.sub(r'https?://(?:www\.)?(?:fixupx|twittpr|x)\.com', 'https://twitter.com', u, flags=re.IGNORECASE)

    # ── 3. TikTok ──────────────────────────────────────────────
    u = re.sub(r'https?://(?:www\.)?(?:vx-?tiktok|tiktxk|vxtik)\.com', 'https://www.tiktok.com', u, flags=re.IGNORECASE)
    u = re.sub(r'https?://m\.tiktok\.com/v/([^/?#&]+)/?', r'https://www.tiktok.com/@user/video/\1', u, flags=re.IGNORECASE)

    # ── 4. Facebook ────────────────────────────────────────────
    u = re.sub(r'https?://m\.facebook\.com', 'https://www.facebook.com', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?facebook\.com)/share/r/([^/?#&]+)/?', r'\1/reel/\2', u, flags=re.IGNORECASE)
    u = re.sub(r'(https?://(?:www\.)?facebook\.com)/share/v/([^/?#&]+)/?', r'\1/watch/?v=\2', u, flags=re.IGNORECASE)

    # ── 5. YouTube & YouTube Music ─────────────────────────────
    u = re.sub(r'https?://music\.youtube\.com/watch\?v=([^&#]+)', r'https://www.youtube.com/watch?v=\1', u, flags=re.IGNORECASE)

    # ── 6. Reddit ──────────────────────────────────────────────
    u = re.sub(r'https?://(?:www\.)?redd\.it/([^/?#&]+)/?', r'https://www.reddit.com/comments/\1', u, flags=re.IGNORECASE)

    # ── 7. Universal Query Tracking Cleaner ────────────────────
    track_pattern = r'[?&](utm_[a-zA-Z_]+|igsh|ig_mid|ig_rid|mibextid|rdid|si|fbclid|gclid|feature|ref|ref_src|source|is_from_webapp|sender_device|_r|_t|share_item_id|t|s)=[^&#]*'
    while re.search(track_pattern, u, flags=re.IGNORECASE):
        u = re.sub(track_pattern, '', u, flags=re.IGNORECASE)
        u = re.sub(r'\?&+', '?', u)
        u = re.sub(r'[?&]$', '', u)
        
    return u

def detect_url_type(url):
    if not url:
        return "unknown"
    u = normalize_media_url(url).lower()
    if "list=" in u:
        return "playlist"
    if any(x in u for x in ["youtu.be/", "watch?v=", "youtube.com/shorts/", "tiktok.com/", "twitter.com/", "x.com/", "fb.watch/", "facebook.com/reel/", "facebook.com/watch", "vimeo.com/", "reddit.com/", "pin.it/"]):
        return "video"
    if any(x in u for x in ["instagram.com/p/", "instagram.com/reel/", "instagram.com/reels/", "instagram.com/tv/", "instagram.com/stories/"]):
        return "video"
    return "unknown"

def extract_better_metadata(info, default_title="Unknown"):
    title = info.get('title') or info.get('id')
    thumb = info.get('thumbnail')
    
    if not thumb and info.get('thumbnails'):
        thumb = info['thumbnails'][-1].get('url')
        
    if not title and 'entries' in info and info['entries']:
        first = info['entries'][0]
        if first:
            title = first.get('title') or first.get('id')
            if not thumb:
                thumb = first.get('thumbnail')
                if not thumb and first.get('thumbnails'):
                    thumb = first['thumbnails'][-1].get('url')
                    
    return title or default_title, thumb

def parse_rate_limit(text):
    text = text.strip().upper()
    if not text:
        return None
    try:
        if text.endswith('M'):
            return int(float(text[:-1]) * 1024 * 1024)
        if text.endswith('K'):
            return int(float(text[:-1]) * 1024)
        return int(text)
    except ValueError:
        return None

def parse_timestamp(text):
    """Convert hh:mm:ss, mm:ss, raw seconds, or '2m 30s' string to float seconds."""
    if text is None:
        return None
    text = str(text).strip().lower()
    if not text:
        return None
    
    if re.search(r'[hms]', text):
        total = 0.0
        h = re.search(r'(\d+)\s*h', text)
        m = re.search(r'(\d+)\s*m', text)
        s = re.search(r'(\d+(?:\.\d+)?)\s*s', text)
        if h: total += int(h.group(1)) * 3600
        if m: total += int(m.group(1)) * 60
        if s: total += float(s.group(1))
        return float(total)

    parts = text.split(":")
    try:
        if len(parts) == 3:
            return float(int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2]))
        elif len(parts) == 2:
            return float(int(parts[0]) * 60 + float(parts[1]))
        return float(text)
    except (ValueError, IndexError):
        return None

# ==========================================
#  CLIPBOARD PASTE HELPERS
# ==========================================
def bind_url_change_clear(entry, info_box, stale_banner=None):
    def on_change(event):
        if event.keysym in ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Up", "Down", "Left", "Right", "Tab"]: return
        text = info_box.get("1.0", "end").strip()
        if text and text not in ["—", "Analyzing…  please wait."]:
            update_info_box(info_box, "—", COL_MUTED)
            if stale_banner: stale_banner.configure(text="")
    entry.bind("<KeyRelease>", on_change)

def bind_text_change_clear(textbox, info_box, stale_banner=None):
    def on_change(event):
        if event.keysym in ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Up", "Down", "Left", "Right", "Tab"]: return
        text = info_box.get("1.0", "end").strip()
        if text and text not in ["—", "Analyzing…  please wait."]:
            update_info_box(info_box, "—", COL_MUTED)
            if stale_banner: stale_banner.configure(text="")
    textbox.bind("<KeyRelease>", on_change)

def attach_auto_check(vars_list, entry_widget, check_action):
    def _on_change(*_):
        try:
            val = entry_widget.get().strip()
        except TypeError:
            val = entry_widget.get("1.0", "end").strip()
        if val:
            app.after(100, check_action)
    for v in vars_list:
        v.trace_add("write", _on_change)

def get_info_details(info_box, fallback_hint):
    text = info_box.get("1.0", "end").strip()
    title = fallback_hint
    size = "Unknown"
    if text and text not in ["—", "Analyzing…  please wait."]:
        for line in text.split("\n"):
            if line.startswith("Title:"):
                title = line.replace("Title:", "").strip()
            elif line.startswith("Size:"):
                size = line.replace("Size:", "").strip()
            elif line.startswith("Total:"):
                size = line.split("   (")[0].replace("Total:", "").strip()
    return title, size

def paste_from_clipboard(entry_widget):
    try:
        text = app.clipboard_get()
        entry_widget.delete(0, "end")
        entry_widget.insert(0, text.strip())
    except Exception:
        pass

def paste_to_textbox(textbox_widget):
    try:
        text = app.clipboard_get()
        textbox_widget.configure(state="normal")
        textbox_widget.delete("1.0", "end")
        textbox_widget.insert("1.0", text.strip())
    except Exception:
        pass

# ==========================================
#  STATUS BAR  (per-tab aware)
# ==========================================
def set_status(text, color=COL_MUTED, tab=None):
    status_label.configure(text=text, text_color=color)
    if tab:
        _tab_status[tab] = (text, color)

def on_tab_change():
    current = tabview.get()
    txt, col = _tab_status.get(current, ("Ready.", COL_MUTED))
    status_label.configure(text=txt, text_color=col)

def toggle_ui(state="normal"):
    for btn in MANAGED_BUTTONS:
        btn.configure(state=state)

def trigger_stop():
    cancel_event.set()
    current = tabview.get()
    app.after(0, lambda: set_status("⏹  Aborting… cleaning up.", COL_ERR, current))

def update_info_box(widget, text, color=COL_ACCENT):
    widget.configure(state="normal")
    widget.delete("1.0", "end")
    widget.configure(text_color=color)
    widget.insert("1.0", text)
    widget.see("end")
    widget.configure(state="disabled")

def _increment_session_counter():
    global _session_dl_count
    _session_dl_count += 1
    dl_counter_label.configure(text=f"↓  {_session_dl_count} completed this session")

# ==========================================
#  STALE-SIZE WARNING
# ==========================================
def make_stale_callback(info_box_widget, stale_banner_widget=None):
    def _on_change(*_):
        try:
            info_box_widget.configure(state="normal")
            current_text = info_box_widget.get("1.0", "end").strip()
            info_box_widget.configure(state="disabled")
        except Exception:
            current_text = ""
        ignore = {"—", "", "Analyzing…  please wait."}
        if current_text and current_text not in ignore:
            if stale_banner_widget:
                # Playlist tabs: show the amber banner panel
                try:
                    stale_banner_widget.configure(
                        text="⚠  Quality / format changed — re-fetch checklist for accurate sizes.")
                except Exception:
                    pass
            else:
                # Single / batch tabs: overwrite info box with amber warning
                update_info_box(
                    info_box_widget,
                    "⚠  Quality / format changed — re-check size before downloading.",
                    COL_WARN)
    return _on_change

def attach_stale_traces(vars_list, info_box, stale_banner=None):
    cb = make_stale_callback(info_box, stale_banner)
    for v in vars_list:
        v.trace_add("write", cb)

# ==========================================
#  SITE LOGO LOADER  (Settings → Supported Websites)
# ==========================================
def _load_site_logo(domain, label_widget, accent_color):
    """Fetch a 32×32 favicon from Google's service and update the badge label."""
    if not PIL_AVAILABLE:
        return
    try:
        url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
        req = urllib.request.Request(
            url, headers={"User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((28, 28), Image.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(28, 28))
        label_widget._logo_ref = ctk_img   # prevent GC
        app.after(0, lambda: label_widget.configure(
            image=ctk_img, text="", compound="left", width=28))
    except Exception:
        pass   # keep the emoji fallback

# ==========================================
#  THUMBNAIL HELPER
#  Works for all tabs — shared function.
# ==========================================
def show_thumbnail(thumb_url, label_widget):
    """Fetch and display a thumbnail. Falls back gracefully if PIL absent."""
    if not PIL_AVAILABLE or not thumb_url:
        app.after(0, lambda: label_widget.configure(
            text="Install Pillow\nfor previews", text_color=COL_MUTED))
        return
    def _fetch():
        try:
            req = urllib.request.Request(
                thumb_url,
                headers={"User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                )}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            img = Image.open(io.BytesIO(data)).convert("RGB")
            w, h   = img.size
            target = (w, int(w * 9 / 16))
            if h > target[1]:
                top = (h - target[1]) // 2
                img = img.crop((0, top, w, top + target[1]))
            img     = img.resize((264, 148), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(264, 148))
            label_widget._thumb_ref = ctk_img
            app.after(0, lambda: label_widget.configure(image=ctk_img, text=""))
        except Exception:
            app.after(0, lambda: label_widget.configure(
                text="Preview\nunavailable", text_color=COL_MUTED))
    threading.Thread(target=_fetch, daemon=True).start()

def make_thumb_panel(parent, placeholder="Thumbnail\nappears here"):
    """Creates a 284×172 thumbnail panel and returns the CTkLabel inside it."""
    frame = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=8,
                          width=284, height=172)
    frame.pack(side="right", padx=(14, 0), pady=(18, 0))
    frame.pack_propagate(False)
    lbl = ctk.CTkLabel(frame, text=placeholder,
                        text_color=COL_MUTED,
                        font=("Segoe UI", 10), width=264, height=148)
    lbl.pack(expand=True)
    return lbl

# ==========================================
#  PROGRESS HOOK
# ==========================================
_last_finished_info = {}
_last_downloading_size = "Unknown"

def progress_hook(d):
    global _last_finished_info, _last_downloading_size
    if cancel_event.is_set() or global_queue.queue_cancel.is_set():
        raise ValueError("PROCESS_CANCELLED")

    def strip_ansi(text):
        if not isinstance(text, str): return text
        return re.sub(r'\x1b\[[0-9;]*m', '', text)

    if d['status'] == 'downloading':
        percent_str = strip_ansi(d.get('_percent_str', '0%')).strip()
        speed       = strip_ansi(d.get('_speed_str', 'N/A')).strip()
        eta         = strip_ansi(d.get('_eta_str', 'N/A')).strip()
        total       = strip_ansi(d.get('_total_bytes_str') or
                                 d.get('_total_bytes_estimate_str') or 'Unknown').strip()
        _last_downloading_size = total
        try:
            percent_float = float(percent_str.replace('%', '')) / 100.0
        except ValueError:
            percent_float = 0.0

        playlist_idx   = d.get('info_dict', {}).get('playlist_index')
        playlist_count = d.get('info_dict', {}).get('playlist_count')
        prefix = f"[{playlist_idx}/{playlist_count}]  " if playlist_idx and playlist_count else ""
        status_text = f"{prefix}↓  {percent_str}  ({total})   Speed: {speed}   ETA: {eta}"
        title_pct   = percent_str.replace(' ', '')

        app.after(0, lambda pf=percent_float, st=status_text, tp=title_pct: (
            progress_bar.set(pf),
            pct_label.configure(text=f" {tp} "),
            status_label.configure(text=st, text_color=COL_SUCCESS),
            app.title(f"[{tp}] Hedra Downloader ULTIMATE {APP_VERSION}"),
        ))

    elif d['status'] == 'finished':
        title = d.get('info_dict', {}).get('title', 'Unknown')
        
        final_bytes = d.get('total_bytes') or d.get('downloaded_bytes')
        if final_bytes:
            total = format_size(final_bytes)
        else:
            total = _last_downloading_size
            
        if total and isinstance(total, str):
            total = strip_ansi(total).strip()
            
        _last_finished_info = {'title': title, 'size': total}
        
        app.after(0, lambda: (
            progress_bar.set(1.0),
            pct_label.configure(text=" 100% "),
            status_label.configure(
                text="✔  Download finished — FFmpeg is processing…",
                text_color=COL_ACCENT),
        ))

# ==========================================
#  GLOBAL OPTIONS READER
# ==========================================
def get_global_opts():
    opts = {}
    try:
        cookie_file = global_cookie_file_var.get().strip()
        if cookie_file and os.path.isfile(cookie_file):
            opts['cookiefile'] = cookie_file
        else:
            browser = global_cookie_var.get()
            if browser and browser != "None":
                opts['cookiesfrombrowser'] = (browser,)
    except Exception:
        pass
    rl = parse_rate_limit(global_ratelimit_entry.get())
    if rl:
        opts['ratelimit'] = rl
    try:
        opts['retries'] = int(global_retries_var.get())
    except ValueError:
        opts['retries'] = 3
    try:
        opts['concurrent_fragment_downloads'] = int(global_concurrent_var.get())
    except ValueError:
        opts['concurrent_fragment_downloads'] = 1
    if global_archive_var.get():
        opts['download_archive'] = ARCHIVE_FILE
    try:
        proxy = global_proxy_entry.get().strip()
        if proxy:
            opts['proxy'] = proxy
    except Exception:
        pass
    return opts

# ==========================================
#  OPTION BUILDERS
# ==========================================
def get_video_opts(q_var, sub_var, fmt_var, target_dir,
                   for_analysis=False, items_list=None,
                   seg_start=None, seg_end=None):
    fmt        = VIDEO_QUALITY_MAP.get(q_var.get(), "bestvideo+bestaudio/best")
    fmt_choice = fmt_var.get()

    opts = {
        'format':          fmt,
        'noplaylist':      items_list is None,
        'ffmpeg_location': FFMPEG_DIR,
        'nocolor':         True,
        'ignoreerrors':    False,
    }
    # Always include global options (cookies, proxy, retries) for analysis & downloads
    opts.update(get_global_opts())

    if items_list:
        opts['playlist_items'] = items_list
        opts['outtmpl'] = os.path.join(
            target_dir, '%(playlist_title)s',
            '%(playlist_index)02d - %(title)s.%(ext)s')
    else:
        opts['outtmpl'] = os.path.join(target_dir, '%(title)s.%(ext)s')

    if not for_analysis:
        opts['progress_hooks'] = [progress_hook]

        # ── Segment / clip download ────────────────────────────────
        if seg_start is not None or seg_end is not None:
            s_val = seg_start if seg_start is not None else 0.0
            e_val = seg_end if seg_end is not None else float('inf')
            opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(s_val, e_val)])
            opts['force_keyframes_at_cuts'] = False
            opts['postprocessor_args'] = {'ffmpeg': ['-avoid_negative_ts', 'make_zero']}
        
        postprocessors = []
        
        sub_choice = sub_var.get() if sub_var else "None"
        if sub_choice not in ("None", "[MKV Required]"):
            lang_info = SUBTITLE_LANG_MAP.get(sub_choice)
            if lang_info:
                lang_code, is_auto = lang_info
                if is_auto:
                    opts['writeautomaticsub'] = True
                else:
                    opts['writesubtitles'] = True
                opts['subtitleslangs'] = [lang_code]
                
            sub_mode = global_sub_mode_var.get() if 'global_sub_mode_var' in globals() else "Embed in Video"
            
            if "Separate .srt" in sub_mode:
                opts['subtitlesformat'] = 'srt'
                postprocessors.append({'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'})
            elif "Separate .vtt" in sub_mode:
                opts['subtitlesformat'] = 'vtt'
            elif "Embed + .srt" in sub_mode:
                opts['subtitlesformat'] = 'srt'
                postprocessors.append({'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'})
                postprocessors.append({'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': True})
                if fmt_choice == "mkv":
                    opts['merge_output_format'] = 'mkv'
                elif fmt_choice == "mp4":
                    opts['merge_output_format'] = 'mp4'
            else:  # "Embed in Video"
                postprocessors.append({'key': 'FFmpegEmbedSubtitle'})
                if fmt_choice == "mkv":
                    opts['merge_output_format'] = 'mkv'
                elif fmt_choice == "mp4":
                    opts['merge_output_format'] = 'mp4'
        elif fmt_choice != "Default":
            opts['merge_output_format'] = fmt_choice
            
        if global_sponsorblock_var.get():
            postprocessors.append({'key': 'SponsorBlock', 'categories': ['sponsor', 'intro', 'outro']})
        if global_metadata_var.get():
            opts['writethumbnail'] = True
            postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True, 'add_metadata': True})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            
        if postprocessors:
            opts['postprocessors'] = postprocessors

    return opts

def get_audio_opts(q_var, fmt_var, target_dir,
                   for_analysis=False, items_list=None,
                   seg_start=None, seg_end=None):
    aq_label   = q_var.get()
    aq         = AUDIO_QUALITY_MAP.get(aq_label, "0")
    fmt_choice = fmt_var.get()

    opts = {
        'format':          'bestaudio/best',
        'noplaylist':      items_list is None,
        'ffmpeg_location': FFMPEG_DIR,
        'nocolor':         True,
        'ignoreerrors':    False,
    }
    # Always include global options (cookies, proxy, retries) for analysis & downloads
    opts.update(get_global_opts())

    if items_list:
        opts['playlist_items'] = items_list
        opts['outtmpl'] = os.path.join(
            target_dir, '%(playlist_title)s',
            '%(playlist_index)02d - %(title)s.%(ext)s')
    else:
        opts['outtmpl'] = os.path.join(target_dir, '%(title)s.%(ext)s')

    if not for_analysis:
        opts['progress_hooks'] = [progress_hook]
        opts['writethumbnail'] = True

        # ── Segment / clip download ────────────────────────────────
        if seg_start is not None or seg_end is not None:
            s_val = seg_start if seg_start is not None else 0.0
            e_val = seg_end if seg_end is not None else float('inf')
            opts['download_ranges'] = yt_dlp.utils.download_range_func(None, [(s_val, e_val)])
            opts['force_keyframes_at_cuts'] = False
            opts['postprocessor_args'] = {'ffmpeg': ['-avoid_negative_ts', 'make_zero']}
        
        postprocessors = [
            {'key': 'FFmpegExtractAudio',
             'preferredcodec': fmt_choice, 'preferredquality': aq},
            {'key': 'EmbedThumbnail', 'already_have_thumbnail': False},
        ]
        
        if global_sponsorblock_var.get():
            postprocessors.append({'key': 'SponsorBlock', 'categories': ['sponsor', 'intro', 'outro']})
        if global_metadata_var.get():
            opts['writethumbnail'] = True
            postprocessors.append({'key': 'FFmpegMetadata', 'add_chapters': True, 'add_metadata': True})
            postprocessors.append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            
        opts['postprocessors'] = postprocessors

    return opts

queue_box_ref = None
_speed_history = [0.0] * 40
_peak_session_speed = 0.0
speed_canvas_ref = None
lbl_q_speed_ref = None
lbl_q_peak_ref = None
lbl_q_active_ref = None
lbl_q_total_ref = None

def _draw_speed_graph():
    if speed_canvas_ref is None or not speed_canvas_ref.winfo_exists(): return
    cv = speed_canvas_ref
    w = cv.winfo_width()
    h = cv.winfo_height()
    if w <= 10: w = 450
    if h <= 10: h = 65
    cv.delete("all")
    
    # Grid lines
    for frac in [0.33, 0.66]:
        gy = int(h * frac)
        cv.create_line(0, gy, w, gy, fill="#151E30", dash=(2, 4))
        
    max_val = max(max(_speed_history), 512 * 1024)
    points = []
    n = len(_speed_history)
    step = w / max(1, n - 1)
    
    for i, s in enumerate(_speed_history):
        x = int(i * step)
        y = int(h - (s / max_val) * (h - 12) - 6)
        points.extend([x, y])
        
    if len(points) >= 4:
        poly_pts = [0, h] + points + [w, h]
        cv.create_polygon(poly_pts, fill="#082038", outline="")
        cv.create_line(points, fill=COL_ACCENT, width=2, smooth=True)
        lx, ly = points[-2], points[-1]
        cv.create_oval(lx - 3, ly - 3, lx + 3, ly + 3, fill=COL_SUCCESS, outline="")
        
    cv.create_text(w - 6, 8, text=f"{format_size(max_val)}/s", fill=COL_MUTED, font=("Segoe UI", 9), anchor="ne")

def update_queue_ui_periodic():
    global _peak_session_speed
    if queue_box_ref is None or not queue_box_ref.winfo_exists(): return
    
    current_speed = 0.0
    for job in global_queue.jobs:
        if "ui_status_label" in job and job["ui_status_label"].winfo_exists():
            c = COL_ACCENT if job['status'] == "Downloading" else COL_MUTED
            if job['status'] == "Completed": c = COL_SUCCESS
            if job['status'] in ["Error", "Cancelled"]: c = COL_ERR
            if job['status'] == "Paused": c = COL_WARN
            job["ui_status_label"].configure(text=f"{job['status']}  |  {job.get('progress_text', '')}", text_color=c)
            
            if "ui_progress_bar" in job and job["ui_progress_bar"].winfo_exists():
                pct = job.get('progress_pct', 0.0)
                job["ui_progress_bar"].set(pct)
                if job['status'] == "Downloading":
                    job["ui_progress_bar"].configure(progress_color=COL_ACCENT)
                elif job['status'] == "Paused":
                    job["ui_progress_bar"].configure(progress_color=COL_WARN)
                elif job['status'] == "Completed":
                    job["ui_progress_bar"].configure(progress_color=COL_SUCCESS)
                else:
                    job["ui_progress_bar"].configure(progress_color=COL_ERR)
                    
        if job['status'] == "Downloading":
            current_speed += float(job.get('speed_bytes', 0.0))
            
    # Update global progress bar
    active_jobs = [j for j in global_queue.jobs if j['status'] == 'Downloading']
    if active_jobs:
        avg_pct = sum(j.get('progress_pct', 0.0) for j in active_jobs) / len(active_jobs)
        progress_bar.set(avg_pct)
        pct_label.configure(text=f" {int(avg_pct*100)}% ")
    elif not any(j['status'] in ['Pending', 'Paused'] for j in global_queue.jobs) and any(j['status'] == 'Completed' for j in global_queue.jobs):
        progress_bar.set(1.0)
        pct_label.configure(text=" 100% ")

    # ── Update network graph & metrics ──
    _speed_history.pop(0)
    _speed_history.append(current_speed)
    if current_speed > _peak_session_speed:
        _peak_session_speed = current_speed
        
    if lbl_q_speed_ref and lbl_q_speed_ref.winfo_exists():
        lbl_q_speed_ref.configure(text=f"⚡ Speed: {format_size(current_speed)}/s" if current_speed > 0 else "⚡ Speed: 0 B/s")
    if lbl_q_peak_ref and lbl_q_peak_ref.winfo_exists():
        lbl_q_peak_ref.configure(text=f"▲ Peak: {format_size(_peak_session_speed)}/s")
    if lbl_q_active_ref and lbl_q_active_ref.winfo_exists():
        lbl_q_active_ref.configure(text=f"⬇ Active: {len(active_jobs)}")
    if lbl_q_total_ref and lbl_q_total_ref.winfo_exists():
        lbl_q_total_ref.configure(text=f"📦 Session: {_session_dl_count} completed")

    _draw_speed_graph()
    app.after(500, update_queue_ui_periodic)

def refresh_queue_tab():
    if queue_box_ref is None: return
    for w in queue_box_ref.winfo_children(): w.destroy()
    if not global_queue.jobs:
        ctk.CTkLabel(queue_box_ref, text="Queue is empty.", text_color=COL_MUTED).pack(pady=20)
        return
    for job in global_queue.jobs:
        f = ctk.CTkFrame(queue_box_ref, fg_color=COL_PANEL, corner_radius=6)
        f.pack(fill="x", pady=4, padx=6)
        
        left = ctk.CTkFrame(f, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        title = job['hint']
        if len(title) > 65: title = title[:62] + "..."
        ctk.CTkLabel(left, text=title, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        
        info_str = f"Size: {job.get('size', 'Unknown')}  |  {job.get('quality', '—')}  |  {job.get('file_type', '—')}"
        ctk.CTkLabel(left, text=info_str, font=("Consolas", 10), text_color=COL_MUTED, anchor="w").pack(fill="x")
        
        status_lbl = ctk.CTkLabel(left, text=f"{job['status']}  |  {job.get('progress_text', '')}", font=("Segoe UI", 11), anchor="w")
        status_lbl.pack(fill="x")
        job["ui_status_label"] = status_lbl
        
        pb = ctk.CTkProgressBar(left, height=6)
        pb.pack(fill="x", pady=(4,0))
        pb.set(job.get('progress_pct', 0.0))
        job["ui_progress_bar"] = pb
        
        right = ctk.CTkFrame(f, fg_color="transparent")
        right.pack(side="right", padx=10)
        
        def make_cmds(jid=job['id']):
            return lambda: global_queue.pause(jid), lambda: global_queue.resume(jid), lambda: global_queue.cancel(jid)
        cmd_p, cmd_r, cmd_c = make_cmds()
        
        if job['status'] in ["Pending", "Downloading"]:
            ctk.CTkButton(right, text="Pause", width=60, height=28, command=cmd_p).pack(side="left", padx=2)
        elif job['status'] == "Paused":
            ctk.CTkButton(right, text="Resume", width=60, height=28, command=cmd_r).pack(side="left", padx=2)
            
        ctk.CTkButton(right, text="✖", width=28, height=28, fg_color=COL_ERR, hover_color="#450A0A", command=cmd_c).pack(side="left", padx=2)

class JobQueue:
    def __init__(self):
        self.jobs = []
        self.active_workers = 0
        self.cancel_events = {}
        self.worker_threads = {}
        self.queue_cancel = threading.Event()
        
    def add(self, opts, links, folder_name, mode, hint, tab, size="Unknown", quality="—", file_type="—", start_paused=False, seg_start=None, seg_end=None):
        cancel_event.clear()
        cleaned_links = [normalize_media_url(l) for l in links if l and str(l).strip()]
        job = {
            "id": str(time.time()),
            "opts": opts,
            "links": cleaned_links,
            "folder_name": folder_name,
            "mode": mode,
            "hint": hint or (cleaned_links[0] if cleaned_links else "Download"),
            "tab": tab,
            "size": size,
            "quality": quality,
            "file_type": file_type,
            "status": "Paused" if start_paused else "Pending",
            "progress_text": "Paused" if start_paused else "Waiting in queue...",
            "seg_start": seg_start,
            "seg_end": seg_end,
        }
        self.jobs.append(job)
        app.after(0, refresh_queue_tab)
        app.after(0, lambda: set_status("✔ Added to Queue.", COL_SUCCESS, tab))
        if not start_paused:
            self.pump()
        
    def pause(self, jid):
        j = next((x for x in self.jobs if x["id"]==jid), None)
        if not j: return
        if j["status"] == "Pending":
            j["status"] = "Paused"
            j["progress_text"] = "Paused."
        elif j["status"] == "Downloading":
            j["status"] = "Paused"
            if jid in self.cancel_events:
                self.cancel_events[jid].set()
        app.after(0, refresh_queue_tab)
        
    def resume(self, jid):
        j = next((x for x in self.jobs if x["id"]==jid), None)
        if not j: return
        if j["status"] == "Paused":
            j["status"] = "Pending"
            j["progress_text"] = "Waiting in queue..."
        cancel_event.clear()
        if jid in self.cancel_events:
            self.cancel_events[jid].clear()
        app.after(0, refresh_queue_tab)
        self.pump()
        
    def cancel(self, jid):
        j = next((x for x in self.jobs if x["id"]==jid), None)
        if not j: return
        if j["status"] == "Downloading":
            j["status"] = "Cancelled"
            if jid in self.cancel_events:
                self.cancel_events[jid].set()
        else:
            self.jobs.remove(j)
        app.after(0, refresh_queue_tab)
        
    def clear_finished(self):
        self.jobs = [j for j in self.jobs if j["status"] not in ["Completed", "Error", "Cancelled"]]
        app.after(0, refresh_queue_tab)
        
    def get_max_concurrent(self):
        try: return int(global_max_downloads_var.get())
        except: return 1

    def pump(self):
        max_c = self.get_max_concurrent()
        while self.active_workers < max_c:
            nxt = next((x for x in self.jobs if x["status"] == "Pending"), None)
            if not nxt: break
            
            jid = nxt["id"]
            nxt["status"] = "Downloading"
            self.active_workers += 1
            self.cancel_events[jid] = threading.Event()
            app.after(0, refresh_queue_tab)
            t = threading.Thread(target=self._worker, args=(nxt,), daemon=True)
            self.worker_threads[jid] = t
            t.start()
            
    def _worker(self, job):
        global _last_downloading_size
        _last_downloading_size = "Unknown"
        jid = job["id"]
        job_cancel = self.cancel_events.get(jid)
        
        def _job_progress_hook(d):
            if job_cancel and job_cancel.is_set():
                raise ValueError("PROCESS_CANCELLED")
            if cancel_event.is_set():
                raise ValueError("PROCESS_CANCELLED")
                
            def strip_ansi(text):
                if not isinstance(text, str): return text
                return re.sub(r'\x1b\[[0-9;]*m', '', text)
                
            if d['status'] == 'downloading':
                percent_str = strip_ansi(d.get('_percent_str', '0%')).strip()
                speed       = strip_ansi(d.get('_speed_str', 'N/A')).strip()
                eta         = strip_ansi(d.get('_eta_str', 'N/A')).strip()
                job['speed_bytes'] = d.get('speed') or 0
                try:
                    job['progress_pct'] = float(percent_str.replace('%', '')) / 100.0
                except:
                    pass
                job['progress_text'] = f"{percent_str}  |  {speed}  |  ETA: {eta}"
                
            elif d['status'] == 'finished':
                job['progress_pct'] = 1.0
                job['speed_bytes'] = 0
                job['progress_text'] = "Post-processing..."

        opts_copy = dict(job["opts"])
        hooks = opts_copy.get("progress_hooks", [])
        opts_copy["progress_hooks"] = [h for h in hooks if h != progress_hook] + [_job_progress_hook]

        app.after(0, lambda: progress_bar.set(0))
        app.after(0, lambda: set_status(f"Downloading: {job['hint']}", COL_ACCENT, job['tab']))
        
        try:
            with yt_dlp.YoutubeDL(opts_copy) as ydl:
                for link in job["links"]:
                    if job_cancel and job_cancel.is_set(): raise ValueError("PROCESS_CANCELLED")
                    info = ydl.extract_info(link, download=True)
                    if info:
                        t_hint = job["hint"] or link
                        title, _ = extract_better_metadata(info, t_hint)
                        sz = extract_size_from_info(info, "Audio" in job["mode"])
                        if sz: sz_str = format_size(sz)
                        elif _last_downloading_size != "Unknown": sz_str = _last_downloading_size
                        else: sz_str = job.get("size", "—")
                        
                        if job["hint"] == link or job["hint"] == "Link 1":
                            job["hint"] = title
                            
                        # Extract downloaded output file path on disk
                        fpath = info.get('_filename') or info.get('filename') or ""
                        if not fpath and 'requested_downloads' in info and info['requested_downloads']:
                            fpath = info['requested_downloads'][0].get('filepath') or ""
                        if not fpath:
                            try: fpath = ydl.prepare_filename(info)
                            except Exception: pass
                            
                        save_history_entry(title, link, job["mode"], sz_str, job.get("quality", "—"), job.get("file_type", "—"), file_path=fpath)
            
            app.after(0, _increment_session_counter)
            app.after(0, lambda: set_status(f"✔ Completed: {job['hint']}", COL_SUCCESS, job["tab"]))
            app.after(0, lambda: progress_bar.set(1.0))
            app.after(0, lambda: pct_label.configure(text=" 100% "))
            if history_box_ref: app.after(200, refresh_history_tab)
            job["status"] = "Completed"
            job["progress_text"] = "Done"
            send_notification("Download Complete! ✔", f"{job['hint']}")
            
        except Exception as e:
            err_str = str(e)
            if "PROCESS_CANCELLED" in err_str:
                if job["status"] == "Paused":
                    job["progress_text"] = "Paused."
                    job["progress_pct"] = job.get("progress_pct", 0.0)
                    app.after(0, lambda: set_status("⏸ Paused.", COL_WARN, job["tab"]))
                else:
                    job["status"] = "Cancelled"
                    job["progress_text"] = "Stopped."
                    job["progress_pct"] = 0.0
                    app.after(0, lambda: set_status("⏹ Stopped.", COL_ERR, job["tab"]))
            elif any(k in err_str.lower() for k in ["empty media response", "login required", "checkpoint", "rate-limit", "rate limited", "unauthorized", "http error 401", "401", "dpapi"]):
                job["status"] = "Error"
                job["progress_text"] = "Cookies/Login required"
                job["progress_pct"] = 0.0
                app.after(0, lambda: set_status("⚠ Failed: Cookies required (Settings → load cookies.txt or Firefox)", COL_WARN, job["tab"]))
            else:
                job["status"] = "Error"
                job["progress_text"] = "Failed."
                job["progress_pct"] = 0.0
                app.after(0, lambda: set_status("✘ Failed.", COL_ERR, job["tab"]))
        finally:
            self.active_workers -= 1
            if jid in self.cancel_events:
                del self.cancel_events[jid]
            if jid in self.worker_threads:
                del self.worker_threads[jid]
            app.after(0, progress_bar.stop)
            app.after(0, lambda: progress_bar.configure(mode="determinate"))
            app.after(0, refresh_queue_tab)
            app.after(0, self.pump)

global_queue = JobQueue()

def save_queue():
    jobs_data = []
    for j in global_queue.jobs:
        if j['status'] in ["Completed", "Error", "Cancelled"]: continue
        opts_copy = dict(j['opts'])
        opts_copy.pop('progress_hooks', None)
        opts_copy.pop('download_ranges', None)
        jobs_data.append({
            "id": j["id"],
            "opts": opts_copy,
            "links": j["links"],
            "folder_name": j["folder_name"],
            "mode": j["mode"],
            "hint": j["hint"],
            "tab": j["tab"],
            "size": j["size"],
            "quality": j["quality"],
            "file_type": j["file_type"],
            "seg_start": j.get("seg_start"),
            "seg_end": j.get("seg_end"),
            "status": "Paused"
        })
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(jobs_data, f, indent=2)
    except: pass

def load_queue():
    if not os.path.exists(QUEUE_FILE): return
    try:
        with open(QUEUE_FILE, "r", encoding="utf-8") as f:
            jobs_data = json.load(f)
        for jd in jobs_data:
            s = jd.get("seg_start")
            e = jd.get("seg_end")
            if s is not None:
                jd["opts"]["download_ranges"] = yt_dlp.utils.download_range_func(None, [(s, e if e is not None else float('inf'))])
            global_queue.add(jd["opts"], jd["links"], jd["folder_name"], jd["mode"], jd["hint"], jd["tab"], jd["size"], jd["quality"], jd["file_type"], start_paused=True, seg_start=s, seg_end=e)
        os.remove(QUEUE_FILE)
    except: pass



# ==========================================
#  DOWNLOAD RUNNER
# ==========================================
def run_download_thread(ydl_opts, links, folder_name,
                        mode="Video", title_hint="", tab=None, size="Unknown", quality="—", file_type="—", start_paused=False, seg_start=None, seg_end=None):
    if not links or not any(l.strip() for l in links):
        set_status("⚠  No links to download.", COL_WARN, tab)
        return
    global_queue.add(ydl_opts, [l.strip() for l in links if l.strip()], folder_name, mode, title_hint, tab, size, quality, file_type, start_paused, seg_start, seg_end)


# ==========================================
#  STANDARD ANALYZER
# ==========================================
def execute_standard_analysis(opts, links, info_box,
                               is_audio=False, audio_bitrate=None,
                               tab=None, thumb_label=None, stale_banner=None,
                               seg_start=None, seg_end=None):
    if not links:
        update_info_box(info_box, "⚠  Please paste link(s) first.", COL_WARN)
        return

    cleaned_links = [normalize_media_url(l) for l in links if l and str(l).strip()]
    if not cleaned_links:
        update_info_box(info_box, "⚠  Please paste valid link(s) first.", COL_WARN)
        return

    cancel_event.clear()
    if stale_banner:
        app.after(0, lambda: stale_banner.configure(text=""))
    app.after(0, lambda: toggle_ui("disabled"))
    app.after(0, _start_pulse)
    update_info_box(info_box, "Analyzing…  please wait.", COL_MUTED)

    def worker():
        total_bytes = 0
        successful  = 0
        details     = []
        title_str   = "Unknown"
        thumb_url   = None
        last_error  = ""
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                for i, link in enumerate(cleaned_links):
                    if cancel_event.is_set():
                        raise ValueError("PROCESS_CANCELLED")
                    try:
                        info       = ydl.extract_info(link, download=False)
                        size_bytes = extract_size_from_info(info, is_audio, audio_bitrate, seg_start, seg_end)
                        total_bytes += size_bytes
                        successful  += 1
                        best_title, best_thumb = extract_better_metadata(info, f'Link {i+1}')
                        title       = best_title
                        title_str   = title
                        if i == 0:
                            thumb_url = best_thumb
                            dur = info.get('duration')
                            if dur:
                                if tab == "Single Video" and 'vid_seg_start' in globals() and hasattr(vid_seg_start, "_set_duration"):
                                    app.after(0, lambda d=dur: vid_seg_start._set_duration(d))
                                elif tab == "Single Audio" and 'aud_seg_start' in globals() and hasattr(aud_seg_start, "_set_duration"):
                                    app.after(0, lambda d=dur: aud_seg_start._set_duration(d))
                                elif tab == "Batch Video" and 'bvid_seg_start' in globals() and hasattr(bvid_seg_start, "_set_duration"):
                                    app.after(0, lambda d=dur: bvid_seg_start._set_duration(d))
                                elif tab == "Batch Audio" and 'baud_seg_start' in globals() and hasattr(baud_seg_start, "_set_duration"):
                                    app.after(0, lambda d=dur: baud_seg_start._set_duration(d))
                        if len(title) > 65:
                            title = title[:62] + "…"
                        details.append(f"[{format_size(size_bytes):>12}]  {title}")
                    except Exception as ex_inner:
                        last_error = str(ex_inner)
                        if any(k in last_error.lower() for k in ["empty media response", "login required", "checkpoint", "rate-limit", "rate limited", "unauthorized", "http error 401", "401", "dpapi"]):
                            details.append(f"  [COOKIES/LOGIN REQ] Link {i+1}")
                        else:
                            details.append(f"  [ERROR]  Failed to fetch link {i+1}")

            if successful == 0:
                if any(k in last_error.lower() for k in ["empty media response", "login required", "checkpoint", "rate-limit", "rate limited", "unauthorized", "http error 401", "401", "dpapi"]):
                    result_text = "⚠  Cookies / Login Required\nInstagram/Site blocked unauthenticated access.\nIn Settings → Cookies, select a cookies.txt file or use Firefox."
                    col = COL_WARN
                else:
                    result_text = f"✘  Failed to fetch info.\n{last_error[:100]}" if last_error else "✘  Failed to fetch info."
                    col = COL_ERR
                app.after(0, lambda m=result_text, c=col: update_info_box(info_box, m, c))
            else:
                size_str = format_size(total_bytes)
                if len(cleaned_links) == 1:
                    result_text = f"Title:  {title_str}\nSize:   {size_str}"
                else:
                    header      = f"Total: {size_str}   ({successful}/{len(cleaned_links)} ok)\n{'─'*52}\n"
                    result_text = header + "\n".join(details)

                app.after(0, lambda: update_info_box(info_box, result_text, COL_ACCENT))
                if thumb_label and thumb_url:
                    show_thumbnail(thumb_url, thumb_label)

        except Exception as e:
            err_str = str(e)
            if "PROCESS_CANCELLED" in err_str:
                msg = "⏹  Analysis aborted."
                col = COL_ERR
            elif any(k in err_str.lower() for k in ["empty media response", "login required", "checkpoint", "rate-limit", "rate limited", "unauthorized", "http error 401", "401", "dpapi"]):
                msg = "⚠  Cookies / Login Required\nIn Settings → Cookies, select a cookies.txt file or use Firefox."
                col = COL_WARN
            else:
                msg = "✘  Failed to fetch info."
                col = COL_ERR
            app.after(0, lambda m=msg, c=col: update_info_box(info_box, m, c))
        finally:
            app.after(0, _stop_pulse)
            app.after(0, lambda: toggle_ui("normal"))

    threading.Thread(target=worker, daemon=True).start()

# ==========================================
#  PLAYLIST ANALYZER
# ==========================================
def analyze_playlist(opts, link, scroll_frame, checkbox_state_list,
                     dynamic_label, stale_banner,
                     is_audio=False, audio_bitrate=None, tab=None,
                     thumb_label=None, seg_start=None, seg_end=None):
    cleaned_link = normalize_media_url(link)
    if not cleaned_link:
        set_status("⚠  Paste a playlist link first.", COL_WARN, tab)
        return

    cancel_event.clear()
    
    previously_selected = [idx for idx, var, _, _ in checkbox_state_list if var.get() == 1]
    had_previous = len(checkbox_state_list) > 0
    
    for widget in scroll_frame.winfo_children():
        widget.destroy()
    checkbox_state_list.clear()
    stale_banner.configure(text="", text_color=COL_WARN)

    msg = ("⚡  Analyzing audio playlist…" if is_audio
           else "🔍  Analyzing video playlist — fetching entries…")
    app.after(0, lambda: set_status(msg, COL_ACCENT, tab))
    app.after(0, lambda: toggle_ui("disabled"))
    app.after(0, _start_pulse)

    def worker():
        local_opts = dict(opts)
        local_opts['extract_flat'] = 'in_playlist' if is_audio else False
        local_opts['noplaylist']   = False
        valid_count = 0

        try:
            with yt_dlp.YoutubeDL(local_opts) as ydl:
                info = ydl.extract_info(cleaned_link, download=False)

                if 'entries' not in info:
                    app.after(0, lambda: set_status(
                        "✘  Link is not a valid playlist.", COL_ERR, tab))
                    return

                entries = list(info['entries'])
                first_thumb_shown = False
                for i, entry in enumerate(entries):
                    if cancel_event.is_set():
                        raise ValueError("PROCESS_CANCELLED")
                    if not entry:
                        continue
                    if not first_thumb_shown and thumb_label:
                        _, best_thumb = extract_better_metadata(entry)
                        thumb_url = best_thumb or info.get('thumbnail')
                        if thumb_url:
                            show_thumbnail(thumb_url, thumb_label)
                        first_thumb_shown = True
                    title, _ = extract_better_metadata(entry, f"Video {i+1}")
                    size_bytes = extract_size_from_info(entry, is_audio, audio_bitrate, seg_start, seg_end)
                    valid_count += 1
                    idx          = i + 1
                    # Live counter update in status bar while entries load
                    app.after(0, lambda n=valid_count: set_status(
                        f"{'🎵' if is_audio else '🎬'}  Loading… {n} entries fetched so far",
                        COL_ACCENT, tab))
                    display_text = f"  {idx:>3}.  [{format_size(size_bytes):>10}]   {title}"
                    
                    default_check = 1
                    if had_previous and idx not in previously_selected:
                        default_check = 0
                        
                    app.after(0, create_checkbox_ui,
                              scroll_frame, checkbox_state_list, idx,
                              display_text, size_bytes, dynamic_label, default_check)

            app.after(150, lambda: update_dynamic_size(checkbox_state_list, dynamic_label))
            done_msg = f"✔  Fetched {valid_count} items — select and click Download."
            app.after(0, lambda: set_status(done_msg, COL_SUCCESS, tab))

        except Exception as e:
            err_str = str(e)
            if "PROCESS_CANCELLED" in err_str:
                msg = "⏹  Analysis aborted."
            elif any(k in err_str.lower() for k in ["login required", "checkpoint", "rate-limit", "rate limited", "unauthorized", "http error 401", "401"]):
                msg = "⚠  Login/Cookies required (Settings → Cookies)."
            else:
                msg = "✘  Failed to fetch playlist."
            app.after(0, lambda m=msg: set_status(m, COL_ERR, tab))
        finally:
            app.after(0, _stop_pulse)
            app.after(0, lambda: toggle_ui("normal"))

    threading.Thread(target=worker, daemon=True).start()

# ==========================================
#  PLAYLIST DOWNLOAD STARTER
# ==========================================
def start_playlist_download(q_var, sub_var, fmt_var, target_dir,
                             link, checkbox_state_list, is_video, tab=None, start_paused=False):
    cleaned_link = normalize_media_url(link)
    selected = [str(idx) for idx, var, _, _ in checkbox_state_list if var.get() == 1]
    if not selected:
        set_status("⚠  No items selected.", COL_WARN, tab)
        return
    items_str = ",".join(selected)
    opts = (get_video_opts(q_var, sub_var, fmt_var, target_dir, False, items_str)
            if is_video
            else get_audio_opts(q_var, fmt_var, target_dir, False, items_str))
    set_status("Initializing playlist download…", COL_ACCENT, tab)
    
    try:
        lbl_text = pvid_dynamic_lbl.cget("text") if is_video else paud_dynamic_lbl.cget("text")
        size = lbl_text.split("Est. total size: ")[1].strip()
    except Exception:
        size = "Unknown"
        
    job_hint = f"Playlist ({len(selected)} items)"
        
    run_download_thread(opts, [cleaned_link], "Playlists",
                        "Playlist-Video" if is_video else "Playlist-Audio",
                        job_hint, tab, size, q_var.get(), fmt_var.get(), start_paused)

# ==========================================
#  DYNAMIC PLAYLIST SIZE ENGINE
# ==========================================
def update_dynamic_size(state_list, label_widget):
    total_bytes    = sum(sb for _, var, _, sb in state_list if var.get() == 1)
    selected_count = sum(1  for _, var, _, _  in state_list if var.get() == 1)
    label_widget.configure(
        text=f"Selected: {selected_count} / {len(state_list)}"
             f"   |   Est. total size: {format_size(total_bytes)}")

def toggle_all_checkboxes(checkbox_list, state, label_widget):
    for _, var, _, _ in checkbox_list:
        var.set(state)
    update_dynamic_size(checkbox_list, label_widget)

def create_checkbox_ui(parent, state_list, index, text, size_bytes, label_widget, default_val=1):
    var = ctk.IntVar(value=default_val)
    cb  = ctk.CTkCheckBox(
        parent, text=text, variable=var,
        font=("Consolas", 12),
        command=lambda: update_dynamic_size(state_list, label_widget))
    cb.pack(anchor="w", pady=3, padx=8)
    state_list.append((index, var, cb, size_bytes))

# ==========================================
#  yt-dlp UPDATER
# ==========================================
def act_update_cli():
    set_status("Checking for yt-dlp updates…", COL_ACCENT, "Settings")
    toggle_ui("disabled")

    def worker():
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'nocolor': True}) as ydl:
                result = yt_dlp.update.Updater(ydl).update()
            msg = ("✔  yt-dlp updated! Restart to apply." if result
                   else "✔  yt-dlp is already up to date.")
            app.after(0, lambda: set_status(msg, COL_SUCCESS, "Settings"))
        except Exception:
            try:
                flags  = 0x08000000 if os.name == 'nt' else 0
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-U", "yt-dlp"],
                    capture_output=True, text=True, creationflags=flags)
                out = (result.stdout + result.stderr).lower()
                msg = ("✔  yt-dlp updated via pip. Restart to apply."
                       if "successfully installed" in out else
                       "✔  yt-dlp is already up to date."
                       if "already satisfied" in out else
                       "⚠  Update ran — check console if issues persist.")
                col = COL_SUCCESS if "✔" in msg else COL_WARN
                app.after(0, lambda: set_status(msg, col, "Settings"))
            except Exception as e2:
                app.after(0, lambda: set_status(f"✘  Update failed: {e2}", COL_ERR, "Settings"))
        finally:
            app.after(0, lambda: toggle_ui("normal"))

    threading.Thread(target=worker, daemon=True).start()

# ==========================================
#  HISTORY TAB
# ==========================================
history_box_ref = None

def delete_history_entry(idx):
    history = load_history()
    if 0 <= idx < len(history):
        history.pop(idx)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
        refresh_history_tab()

def refresh_history_tab():
    if history_box_ref is None:
        return
    for widget in history_box_ref.winfo_children():
        widget.destroy()
        
    history = load_history()
    if not history:
        ctk.CTkLabel(history_box_ref, text="No downloads recorded yet.", text_color=COL_MUTED).pack(pady=20)
        return
        
    start_idx = max(0, len(history) - 200)
    display_history = history[start_idx:]
    
    for i, h in enumerate(display_history):
        real_idx = start_idx + i
        
        frame = ctk.CTkFrame(history_box_ref, fg_color=COL_PANEL, corner_radius=6)
        frame.pack(fill="x", pady=2, padx=6)
        
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=4)
        
        left = ctk.CTkFrame(row, fg_color="transparent", width=100, height=40)
        left.pack(side="left")
        left.pack_propagate(False)
        ctk.CTkLabel(left, text=h.get('time', '—')[:10], font=("Segoe UI", 10), text_color=COL_MUTED).pack(anchor="w", pady=(0, 0))
        ctk.CTkLabel(left, text=h.get('mode', '—').replace("-", " "), font=("Segoe UI", 11, "bold"), text_color=COL_ACCENT).pack(anchor="w")
        
        center = ctk.CTkFrame(row, fg_color="transparent")
        center.pack(side="left", fill="x", expand=True, padx=10)
        title = h.get('title', '—')
        if len(title) > 65: title = title[:62] + "..."
        ctk.CTkLabel(center, text=title, font=("Segoe UI", 12), anchor="w").pack(fill="x")
        
        info_str = f"{h.get('quality', '—')}  |  {h.get('file_type', '—')}"
        ctk.CTkLabel(center, text=info_str, font=("Consolas", 10), text_color=COL_MUTED, anchor="w").pack(fill="x", pady=(2, 0))
        
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right")
        
        ctk.CTkLabel(right, text=h.get('size', '—'), font=("Consolas", 11), text_color=COL_MUTED).pack(side="left", padx=(0, 10))
        
        file_path = h.get('file_path', '')
        
        def make_play_fn(fp=file_path, t=h.get('title', ''), m=h.get('mode', '')):
            def _play():
                if fp and os.path.exists(fp):
                    open_file_direct(fp)
                else:
                    found = find_downloaded_file(t, m)
                    if found and os.path.exists(found):
                        open_file_direct(found)
                    else:
                        messagebox.showinfo("File Not Found", f"Could not find downloaded file:\n\n{t}\n\nIt may have been moved, renamed, or deleted.")
            return _play
            
        def make_folder_fn(fp=file_path, t=h.get('title', ''), m=h.get('mode', '')):
            def _folder():
                if fp and os.path.exists(fp):
                    show_in_explorer(fp)
                else:
                    found = find_downloaded_file(t, m)
                    if found and os.path.exists(found):
                        show_in_explorer(found)
                    else:
                        open_folder(AUD_DIR if "Audio" in m else VID_DIR)
            return _folder
            
        def make_open_fn(url=h.get('url', '')):
            return lambda: webbrowser.open(url)
            
        def make_del_fn(idx=real_idx):
            return lambda: delete_history_entry(idx)
            
        ctk.CTkButton(right, text="▶ Play", width=55, height=28, font=("Segoe UI", 11, "bold"), fg_color="#0F766E", hover_color="#115E59", command=make_play_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="📁 Folder", width=60, height=28, font=("Segoe UI", 11), fg_color="#1E293B", hover_color="#0F172A", command=make_folder_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="Link", width=42, height=28, font=("Segoe UI", 11), command=make_open_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="✖", width=28, height=28, font=("Segoe UI", 11), fg_color="#7F1D1D", hover_color="#450A0A", command=make_del_fn()).pack(side="left")

# ==========================================
#  UI COMPONENT BUILDERS
# ==========================================
def make_section_label(parent, text):
    ctk.CTkLabel(parent, text=text, font=("Segoe UI", 13, "bold"),
                 text_color=COL_MUTED).pack(anchor="w", padx=22, pady=(14, 2))

def make_divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=COL_CHECK).pack(fill="x", padx=20, pady=4)

def make_info_box(parent, height=55):
    box = ctk.CTkTextbox(parent, height=height, state="disabled",
                         text_color=COL_ACCENT, fg_color=COL_DARK,
                         font=MONO_FONT, wrap="none")
    box.pack(fill="x", padx=20, pady=4)
    return box

def make_check_btn(parent, text, cmd):
    b = ctk.CTkButton(parent, text=text, font=BTN_SUB,
                      fg_color=COL_CHECK, hover_color=COL_CHECKH,
                      height=34, command=cmd)
    b.pack(fill="x", padx=40, pady=(8, 2))
    MANAGED_BUTTONS.append(b)
    return b

def make_dl_btn_group(parent, text, dl_cmd, queue_cmd):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=40, pady=(6, 10))
    b1 = ctk.CTkButton(frame, text=text, font=BTN_MAIN,
                      fg_color=COL_DL, hover_color=COL_DLH,
                      height=48, command=dl_cmd)
    b1.pack(side="left", fill="x", expand=True, padx=(0, 5))
    MANAGED_BUTTONS.append(b1)
    b2 = ctk.CTkButton(frame, text="➕ Add to Queue", font=BTN_MAIN,
                      fg_color="#0F766E", hover_color="#115E59",
                      height=48, command=queue_cmd)
    b2.pack(side="right", fill="x", expand=True, padx=(5, 0))
    MANAGED_BUTTONS.append(b2)
    return b1, b2

def make_playlist_dl_btn_group(parent, text, dl_cmd, queue_cmd):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=(8, 14))
    b1 = ctk.CTkButton(frame, text=text, font=BTN_MAIN,
                      fg_color=COL_DL, hover_color=COL_DLH,
                      height=58, command=dl_cmd)
    b1.pack(side="left", fill="x", expand=True, padx=(0, 5))
    MANAGED_BUTTONS.append(b1)
    b2 = ctk.CTkButton(frame, text="➕ Add to Queue", font=BTN_MAIN,
                      fg_color="#0F766E", hover_color="#115E59",
                      height=58, command=queue_cmd)
    b2.pack(side="right", fill="x", expand=True, padx=(5, 0))
    MANAGED_BUTTONS.append(b2)
    return b1, b2

def make_entry_row(parent, placeholder):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=(2, 4))
    entry = ctk.CTkEntry(frame, placeholder_text=placeholder,
                         font=ENTRY_FONT, height=38)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
    ctk.CTkButton(
        frame, text="📋", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH,
        command=lambda: paste_from_clipboard(entry)
    ).pack(side="right")
    return entry

def make_textbox_row(parent):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=20, pady=(2, 4))
    textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), fg_color=COL_DARK,
                              height=130)
    textbox.pack(side="left", fill="both", expand=True, padx=(0, 6))
    side = ctk.CTkFrame(frame, fg_color="transparent", width=38)
    side.pack(side="right", fill="y")
    side.pack_propagate(False)
    ctk.CTkButton(
        side, text="📋", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH,
        command=lambda: paste_to_textbox(textbox)
    ).pack(pady=(0, 4))
    ctk.CTkButton(
        side, text="✕", width=38, height=38, font=("Segoe UI", 14, "bold"),
        fg_color="#7F1D1D", hover_color="#450A0A",
        command=lambda: textbox.delete("1.0", "end")
    ).pack(pady=(4, 4))
    def _import_urls():
        try:
            path = ctk.filedialog.askopenfilename(
                title="Import URLs from .txt file",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if not path: return
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", content.strip())
        except Exception:
            pass
    ctk.CTkButton(
        side, text="📂", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH,
        command=_import_urls
    ).pack(pady=(4, 4))

    def _clean_and_dedupe():
        try:
            raw_text = textbox.get("1.0", "end")
            lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
            if not lines: return
            cleaned = []
            seen = set()
            for l in lines:
                norm = normalize_media_url(l)
                if norm and norm not in seen:
                    seen.add(norm)
                    cleaned.append(norm)
            removed = len(lines) - len(cleaned)
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", "\n".join(cleaned))
            curr_tab = tabview.get()
            set_status(f"✔ Cleaned: {len(cleaned)} unique links ({removed} duplicates removed)", COL_SUCCESS, curr_tab)
        except Exception:
            pass

    ctk.CTkButton(
        side, text="🧹", width=38, height=38, font=("Segoe UI", 14),
        fg_color="#0F766E", hover_color="#115E59",
        command=_clean_and_dedupe
    ).pack(pady=(4, 0))
    return textbox

def create_path_selector(parent, default_path):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(frame, text="Save to:", font=LABEL_FONT).pack(side="left", padx=(0, 6))
    path_var = ctk.StringVar(value=default_path)
    ctk.CTkEntry(frame, textvariable=path_var, font=ENTRY_FONT).pack(
        side="left", fill="x", expand=True, padx=5)
    def browse():
        d = ctk.filedialog.askdirectory(initialdir=path_var.get())
        if d:
            path_var.set(d)
    ctk.CTkButton(frame, text="Browse", width=75, font=BTN_SUB,
                  command=browse).pack(side="right", padx=(5, 0))
    return path_var

def create_vid_options(parent):
    frame = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=8)
    frame.pack(fill="x", padx=20, pady=6)

    # ── Preset Pill Bar ──
    p_row = ctk.CTkFrame(frame, fg_color="transparent")
    p_row.pack(fill="x", padx=12, pady=(6, 2))
    ctk.CTkLabel(p_row, text="Presets:", font=("Segoe UI", 10, "bold"), text_color=COL_MUTED).pack(side="left", padx=(0, 6))

    q_var = ctk.StringVar(value="Best Available")
    fmt_var = ctk.StringVar(value="Default")
    s_var = ctk.StringVar(value="None")

    def _set_vid_preset(q_val, f_val):
        q_var.set(q_val)
        fmt_var.set(f_val)

    vid_presets = [
        ("🎬 4K Max", "Max 4K (2160p)", "Default"),
        ("📱 1080p MP4", "Max 1080p", "mp4"),
        ("⚡ 720p Fast", "Max 720p", "mp4"),
        ("💎 Best Quality", "Best Available", "Default"),
    ]
    for label, q_target, f_target in vid_presets:
        ctk.CTkButton(
            p_row, text=label, width=88, height=22, font=("Segoe UI", 10, "bold"),
            fg_color=COL_CHECK, hover_color=COL_CHECKH,
            command=lambda q=q_target, f=f_target: _set_vid_preset(q, f)
        ).pack(side="left", padx=2)

    # Row 1: Quality | File Type | Subtitles
    row1 = ctk.CTkFrame(frame, fg_color="transparent")
    row1.pack(fill="x", padx=12, pady=(4, 8))

    ctk.CTkLabel(row1, text="Quality:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    ctk.CTkOptionMenu(row1, variable=q_var, width=135,
                      values=list(VIDEO_QUALITY_MAP.keys())).pack(side="left", padx=(0, 12))

    ctk.CTkLabel(row1, text="File Type:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    fmt_menu = ctk.CTkOptionMenu(row1, variable=fmt_var, width=80,
                                 values=["Default", "mp4", "mkv"])
    fmt_menu.pack(side="left", padx=(0, 12))

    ctk.CTkLabel(row1, text="Subtitles:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    s_menu = ctk.CTkOptionMenu(
        row1, variable=s_var, width=200,
        values=["None"] + list(SUBTITLE_LANG_MAP.keys()))
    s_menu.pack(side="left")

    return q_var, s_var, fmt_var

def create_aud_options(parent):
    frame = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=8)
    frame.pack(fill="x", padx=20, pady=6)

    # ── Preset Pill Bar ──
    p_row = ctk.CTkFrame(frame, fg_color="transparent")
    p_row.pack(fill="x", padx=12, pady=(6, 2))
    ctk.CTkLabel(p_row, text="Presets:", font=("Segoe UI", 10, "bold"), text_color=COL_MUTED).pack(side="left", padx=(0, 6))

    q_var = ctk.StringVar(value="Best — Highest bitrate")
    fmt_var = ctk.StringVar(value="mp3")

    def _set_aud_preset(q_val, f_val):
        q_var.set(q_val)
        fmt_var.set(f_val)

    aud_presets = [
        ("🎵 320k MP3", "Best — Highest bitrate", "mp3"),
        ("🎧 Studio FLAC", "Best — Highest bitrate", "flac"),
        ("📻 128k Light", "Medium — ~128 kbps", "mp3"),
        ("🍎 M4A Apple", "Best — Highest bitrate", "m4a"),
    ]
    for label, q_target, f_target in aud_presets:
        ctk.CTkButton(
            p_row, text=label, width=88, height=22, font=("Segoe UI", 10, "bold"),
            fg_color=COL_CHECK, hover_color=COL_CHECKH,
            command=lambda q=q_target, f=f_target: _set_aud_preset(q, f)
        ).pack(side="left", padx=2)

    row = ctk.CTkFrame(frame, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(4, 8))
    ctk.CTkLabel(row, text="Quality:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    ctk.CTkOptionMenu(row, variable=q_var, width=200,
                      values=list(AUDIO_BITRATE_MAP.keys())).pack(side="left", padx=(0, 18))
    ctk.CTkLabel(row, text="Format:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
    ctk.CTkOptionMenu(row, variable=fmt_var, width=90,
                      values=["mp3", "flac", "wav", "m4a"]).pack(side="left")
    return q_var, fmt_var

def make_stale_banner(parent):
    """Full-width amber warning panel — impossible to miss."""
    outer = ctk.CTkFrame(parent, fg_color="#451A03", corner_radius=8)
    outer.pack(fill="x", padx=20, pady=(2, 4))
    lbl = ctk.CTkLabel(outer, text="",
                        font=("Segoe UI", 12, "bold"),
                        text_color=COL_WARN, anchor="center")
    lbl.pack(fill="x", padx=14, pady=7)
    # Expose configure on the label but hide the outer frame when empty
    _orig_configure = lbl.configure
    def _smart_configure(**kwargs):
        if "text" in kwargs:
            if kwargs["text"]:
                outer.pack(fill="x", padx=20, pady=(2, 4))
            else:
                outer.pack_forget()
        _orig_configure(**kwargs)
    lbl.configure = _smart_configure
    outer.pack_forget()   # hidden by default
    return lbl

def bind_url_hint(entry, tab_name, suggestion_tab):
    def _check(*_):
        url  = entry.get().strip()
        kind = detect_url_type(url)
        if not url:
            return
        if kind == "playlist" and "Single" in tab_name:
            set_status(
                f"ℹ  This looks like a playlist URL — consider using '{suggestion_tab}'.",
                COL_MUTED, tab_name)
        elif kind == "video" and "Playlist" in tab_name:
            set_status(
                "ℹ  This looks like a single video URL — consider using a Single tab.",
                COL_MUTED, tab_name)
    entry.bind("<FocusOut>", _check)
    entry.bind("<Return>",   _check)

def bind_keyboard_shortcuts(entry, dl_cmd):
    entry.bind("<Control-s>", lambda e: dl_cmd())
    entry.bind("<Control-S>", lambda e: dl_cmd())

def make_segment_row(parent, check_cmd=None):
    """Creates an interactive Visual Clip / Segment Studio.
    Returns (enabled_var, start_entry, end_entry)."""
    outer = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=10)
    outer.pack(fill="x", padx=20, pady=(0, 6))

    header = ctk.CTkFrame(outer, fg_color="transparent")
    header.pack(fill="x", padx=12, pady=(8, 4))

    enabled_var = ctk.BooleanVar(value=False)
    chk = ctk.CTkCheckBox(
        header, text="✂  Clip / Segment Studio  (download portion)",
        variable=enabled_var,
        font=("Segoe UI", 12, "bold"), text_color=COL_TEXT
    )
    chk.pack(side="left")

    badge_lbl = ctk.CTkLabel(
        header, text="",
        font=("Consolas", 11, "bold"), text_color=COL_ACCENT
    )
    badge_lbl.pack(side="right", padx=(0, 4))

    body = ctk.CTkFrame(outer, fg_color="transparent")

    # State
    state = {
        "max_duration": 300.0,
        "is_syncing": False,
        "debounce_id": None,
    }

    # ── Sliders Frame ──────────────────────────────────────
    studio_box = ctk.CTkFrame(body, fg_color=COL_DARK, corner_radius=8)
    studio_box.pack(fill="x", padx=12, pady=(2, 6))

    # Row 1: Start Slider & Controls
    row_start = ctk.CTkFrame(studio_box, fg_color="transparent")
    row_start.pack(fill="x", padx=10, pady=(8, 4))

    ctk.CTkLabel(row_start, text="Start:", width=45, font=LABEL_FONT, anchor="w").pack(side="left")
    start_entry = ctk.CTkEntry(row_start, width=80, font=ENTRY_FONT, placeholder_text="00:00")
    start_entry.insert(0, "00:00")
    start_entry.pack(side="left", padx=(0, 8))

    slider_start = ctk.CTkSlider(row_start, from_=0, to=state["max_duration"],
                                 progress_color=COL_ACCENT, fg_color="#1E293B",
                                 height=18)
    slider_start.set(0)
    slider_start.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def _apply_start(val):
        if state["is_syncing"]: return
        state["is_syncing"] = True
        val = max(0.0, min(float(val), slider_end.get()))
        slider_start.set(val)
        start_entry.delete(0, "end")
        start_entry.insert(0, format_seconds_to_time(val))
        state["is_syncing"] = False
        _update_badge()
        _trigger_check_debounced()

    def _apply_end(val):
        if state["is_syncing"]: return
        state["is_syncing"] = True
        val = max(slider_start.get(), min(float(val), state["max_duration"]))
        slider_end.set(val)
        end_entry.delete(0, "end")
        end_entry.insert(0, format_seconds_to_time(val))
        state["is_syncing"] = False
        _update_badge()
        _trigger_check_debounced()

    def _nudge_start(delta):
        s_val = parse_timestamp(start_entry.get()) or 0.0
        new_val = max(0.0, min(s_val + delta, slider_end.get()))
        _apply_start(new_val)

    ctk.CTkButton(row_start, text="⏮", width=28, height=26, font=("Segoe UI", 11, "bold"),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _apply_start(0.0)).pack(side="left", padx=2)
    ctk.CTkButton(row_start, text="−5s", width=34, height=26, font=("Segoe UI", 10),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _nudge_start(-5.0)).pack(side="left", padx=2)
    ctk.CTkButton(row_start, text="+5s", width=34, height=26, font=("Segoe UI", 10),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _nudge_start(5.0)).pack(side="left", padx=2)

    # Row 2: End Slider & Controls
    row_end = ctk.CTkFrame(studio_box, fg_color="transparent")
    row_end.pack(fill="x", padx=10, pady=(4, 8))

    ctk.CTkLabel(row_end, text="End:", width=45, font=LABEL_FONT, anchor="w").pack(side="left")
    end_entry = ctk.CTkEntry(row_end, width=80, font=ENTRY_FONT, placeholder_text="End")
    end_entry.pack(side="left", padx=(0, 8))

    slider_end = ctk.CTkSlider(row_end, from_=0, to=state["max_duration"],
                               progress_color=COL_ACCENT, fg_color="#1E293B",
                               height=18)
    slider_end.set(state["max_duration"])
    slider_end.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def _nudge_end(delta):
        e_val = parse_timestamp(end_entry.get())
        if e_val is None: e_val = state["max_duration"]
        new_val = max(slider_start.get(), min(e_val + delta, state["max_duration"]))
        _apply_end(new_val)

    ctk.CTkButton(row_end, text="−5s", width=34, height=26, font=("Segoe UI", 10),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _nudge_end(-5.0)).pack(side="left", padx=2)
    ctk.CTkButton(row_end, text="+5s", width=34, height=26, font=("Segoe UI", 10),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _nudge_end(5.0)).pack(side="left", padx=2)
    ctk.CTkButton(row_end, text="⏭", width=28, height=26, font=("Segoe UI", 11, "bold"),
                  fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=lambda: _apply_end(state["max_duration"])).pack(side="left", padx=2)

    # ── Summary & Presets Bar ──
    info_row = ctk.CTkFrame(body, fg_color="transparent")
    info_row.pack(fill="x", padx=12, pady=(0, 8))

    summary_lbl = ctk.CTkLabel(info_row, text="Selected: Full Video",
                              font=("Segoe UI", 11, "bold"), text_color=COL_ACCENT)
    summary_lbl.pack(side="left")

    def _reset_full():
        _apply_start(0.0)
        _apply_end(state["max_duration"])
        end_entry.delete(0, "end")

    ctk.CTkButton(info_row, text="🎯 Full Video (Reset)", width=130, height=24,
                  font=("Segoe UI", 10, "bold"), fg_color=COL_CHECK, hover_color=COL_CHECKH,
                  command=_reset_full).pack(side="right")

    # ── Synchronization Logic ──────────────────────────────
    def _update_badge():
        s_val = slider_start.get()
        e_val = slider_end.get()
        max_d = state["max_duration"]
        clip_len = max(0.0, e_val - s_val)
        txt = f"⏱ {format_seconds_to_time(s_val)} → {format_seconds_to_time(e_val)} ({format_seconds_to_time(clip_len)})"
        badge_lbl.configure(text=txt if enabled_var.get() else "")
        summary_lbl.configure(text=f"Clip Length: {format_seconds_to_time(clip_len)}  |  Total: {format_seconds_to_time(max_d)}")

    def _trigger_check_debounced():
        if check_cmd:
            if state["debounce_id"]:
                try: app.after_cancel(state["debounce_id"])
                except Exception: pass
            state["debounce_id"] = app.after(350, check_cmd)

    def _on_slider_start_drag(val):
        if state["is_syncing"]: return
        fval = float(val)
        if fval > slider_end.get():
            slider_end.set(fval)
            end_entry.delete(0, "end")
            end_entry.insert(0, format_seconds_to_time(fval))
        start_entry.delete(0, "end")
        start_entry.insert(0, format_seconds_to_time(fval))
        _update_badge()
        _trigger_check_debounced()

    def _on_slider_end_drag(val):
        if state["is_syncing"]: return
        fval = float(val)
        if fval < slider_start.get():
            slider_start.set(fval)
            start_entry.delete(0, "end")
            start_entry.insert(0, format_seconds_to_time(fval))
        end_entry.delete(0, "end")
        end_entry.insert(0, format_seconds_to_time(fval))
        _update_badge()
        _trigger_check_debounced()

    slider_start.configure(command=_on_slider_start_drag)
    slider_end.configure(command=_on_slider_end_drag)

    def _on_entry_start_change(*_):
        val = parse_timestamp(start_entry.get())
        if val is not None:
            _apply_start(val)

    def _on_entry_end_change(*_):
        txt = end_entry.get().strip()
        if not txt:
            _apply_end(state["max_duration"])
            end_entry.delete(0, "end")
            return
        val = parse_timestamp(txt)
        if val is not None:
            _apply_end(val)

    start_entry.bind("<FocusOut>", _on_entry_start_change)
    start_entry.bind("<Return>", _on_entry_start_change)
    end_entry.bind("<FocusOut>", _on_entry_end_change)
    end_entry.bind("<Return>", _on_entry_end_change)

    def set_duration(dur):
        if not dur or dur <= 0: return
        dur = float(dur)
        state["max_duration"] = dur
        slider_start.configure(to=dur)
        slider_end.configure(to=dur)
        current_e = parse_timestamp(end_entry.get())
        if current_e is None or current_e >= dur or current_e == 300.0:
            slider_end.set(dur)
            if end_entry.get().strip():
                end_entry.delete(0, "end")
                end_entry.insert(0, format_seconds_to_time(dur))
        _update_badge()

    start_entry._set_duration = set_duration

    def _toggle(*_):
        if enabled_var.get():
            body.pack(fill="x", after=header)
            _update_badge()
        else:
            body.pack_forget()
            badge_lbl.configure(text="")
        _trigger_check_debounced()

    enabled_var.trace_add("write", _toggle)
    body.pack_forget()   # hidden by default

    return enabled_var, start_entry, end_entry

def _get_seg_params(enabled_var, start_entry, end_entry):
    """Read segment UI vars and return (seg_start, seg_end, label_suffix)."""
    if not enabled_var.get():
        return None, None, ""
    s = parse_timestamp(start_entry.get())
    e = parse_timestamp(end_entry.get())
    if s is None and e is None:
        return None, None, ""
    if s is not None and s == 0.0 and e is None:
        return None, None, ""
    # Validate: end must be > start
    if s is not None and e is not None and e <= s:
        return None, None, ""
    def _fmt(sec):
        if sec is None: return "start" if s is None else "end"
        return format_seconds_to_time(sec)
    label = f" [{_fmt(s)}→{_fmt(e)}]"
    return s, e, label

# ==========================================
#  FOOTER — built FIRST so side="bottom" works
#  CRITICAL: footer must be packed before tabview
# ==========================================
footer = ctk.CTkFrame(app, corner_radius=0, fg_color=COL_FOOTER)
footer.pack(side="bottom", fill="x", padx=0, pady=0)

# Row 1: progress bar + % label
prog_row = ctk.CTkFrame(footer, fg_color="transparent")
prog_row.pack(fill="x", padx=0, pady=0)

progress_bar = ctk.CTkProgressBar(prog_row, height=14,
                                   fg_color=COL_PANEL, progress_color=COL_ACCENT,
                                   corner_radius=0)
progress_bar.set(0)
progress_bar.pack(side="left", fill="x", expand=True, padx=0, pady=0)

pct_label = ctk.CTkLabel(prog_row, text=" 0% ", width=46,
                          font=("Consolas", 11, "bold"),
                          text_color=COL_ACCENT, fg_color=COL_FOOTER,
                          anchor="center")
pct_label.pack(side="right", padx=0, pady=0)

# Row 2: status message — full width
status_label = ctk.CTkLabel(footer,
                             text="Ready.",
                             font=("Segoe UI", 13), text_color=COL_MUTED,
                             anchor="w")
status_label.pack(fill="x", padx=16, pady=(6, 2))

# Row 3: session counter + STOP button
bottom_row = ctk.CTkFrame(footer, fg_color="transparent")
bottom_row.pack(fill="x", padx=14, pady=(2, 10))

dl_counter_label = ctk.CTkLabel(bottom_row,
                                  text="↓  0 completed this session",
                                  font=("Segoe UI", 11), text_color=COL_MUTED,
                                  anchor="w")
dl_counter_label.pack(side="left")

btn_queue = ctk.CTkButton(
    bottom_row, text="📋  VIEW QUEUE", width=180, height=36,
    fg_color=COL_ACCENT,
    font=("Segoe UI", 13, "bold"),
    command=lambda: tabview.set("Queue"))
btn_queue.pack(side="right")

# ==========================================
#  MAIN TAB VIEW — packed AFTER footer
# ==========================================
tabview = ctk.CTkTabview(app, width=920, anchor="nw",
                          command=on_tab_change)
tabview.pack(fill="both", expand=True, pady=(6, 0), padx=10)
for tab in TAB_NAMES:
    tabview.add(tab)

# ==========================================
#  ACTION WRAPPERS
# ==========================================
def act_svid_check():
    link = vid_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Video"); return
    s, e, _ = _get_seg_params(vid_seg_var, vid_seg_start, vid_seg_end)
    execute_standard_analysis(
        get_video_opts(vid_q_var, vid_s_var, vid_fmt_var, vid_path_var.get(), True),
        [link], vid_info_box, is_audio=False, tab="Single Video",
        thumb_label=vid_thumb_label, stale_banner=vid_stale_banner,
        seg_start=s, seg_end=e)

def act_svid_dl(start_paused=False):
    link = vid_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Video"); return
    title, size = get_info_details(vid_info_box, link)
    s, e, lbl = _get_seg_params(vid_seg_var, vid_seg_start, vid_seg_end)
    run_download_thread(
        get_video_opts(vid_q_var, vid_s_var, vid_fmt_var, vid_path_var.get(),
                       seg_start=s, seg_end=e),
        [link], vid_path_var.get(), f"Single-Video{lbl}", title, "Single Video",
        size, vid_q_var.get(), vid_fmt_var.get(), start_paused, s, e)

def act_saud_check():
    link = aud_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Audio"); return
    s, e, _ = _get_seg_params(aud_seg_var, aud_seg_start, aud_seg_end)
    execute_standard_analysis(
        get_audio_opts(aud_q_var, aud_fmt_var, aud_path_var.get(), True),
        [link], aud_info_box, is_audio=True,
        audio_bitrate=get_audio_bitrate(aud_q_var), tab="Single Audio",
        thumb_label=aud_thumb_label, stale_banner=aud_stale_banner,
        seg_start=s, seg_end=e)

def act_saud_dl(start_paused=False):
    link = aud_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Audio"); return
    title, size = get_info_details(aud_info_box, link)
    s, e, lbl = _get_seg_params(aud_seg_var, aud_seg_start, aud_seg_end)
    run_download_thread(
        get_audio_opts(aud_q_var, aud_fmt_var, aud_path_var.get(),
                       seg_start=s, seg_end=e),
        [link], aud_path_var.get(), f"Single-Audio{lbl}", title, "Single Audio",
        size, aud_q_var.get(), aud_fmt_var.get(), start_paused, s, e)

def act_bvid_check():
    links = [l for l in bvid_text.get("1.0", "end").splitlines() if l.strip()]
    s, e, _ = _get_seg_params(bvid_seg_var, bvid_seg_start, bvid_seg_end)
    execute_standard_analysis(
        get_video_opts(bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_path_var.get(), True),
        links, bvid_info_box, is_audio=False, tab="Batch Video",
        thumb_label=bvid_thumb_label, stale_banner=bvid_stale_banner,
        seg_start=s, seg_end=e)

def act_bvid_dl(start_paused=False):
    links = [l for l in bvid_text.get("1.0", "end").splitlines() if l.strip()]
    if not links:
        set_status("⚠  No links in the box.", COL_WARN, "Batch Video"); return
    title, size = get_info_details(bvid_info_box, "Batch Video")
    s, e, lbl = _get_seg_params(bvid_seg_var, bvid_seg_start, bvid_seg_end)
    run_download_thread(
        get_video_opts(bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_path_var.get(),
                       seg_start=s, seg_end=e),
        links, bvid_path_var.get(), f"Batch-Video{lbl}", title, "Batch Video",
        size, bvid_q_var.get(), bvid_fmt_var.get(), start_paused, s, e)

def act_baud_check():
    links = [l for l in baud_text.get("1.0", "end").splitlines() if l.strip()]
    s, e, _ = _get_seg_params(baud_seg_var, baud_seg_start, baud_seg_end)
    execute_standard_analysis(
        get_audio_opts(baud_q_var, baud_fmt_var, baud_path_var.get(), True),
        links, baud_info_box, is_audio=True,
        audio_bitrate=get_audio_bitrate(baud_q_var), tab="Batch Audio",
        thumb_label=baud_thumb_label, stale_banner=baud_stale_banner,
        seg_start=s, seg_end=e)

def act_baud_dl(start_paused=False):
    links = [l for l in baud_text.get("1.0", "end").splitlines() if l.strip()]
    if not links:
        set_status("⚠  No links in the box.", COL_WARN, "Batch Audio"); return
    title, size = get_info_details(baud_info_box, "Batch Audio")
    s, e, lbl = _get_seg_params(baud_seg_var, baud_seg_start, baud_seg_end)
    run_download_thread(
        get_audio_opts(baud_q_var, baud_fmt_var, baud_path_var.get(),
                       seg_start=s, seg_end=e),
        links, baud_path_var.get(), f"Batch-Audio{lbl}", title, "Batch Audio",
        size, baud_q_var.get(), baud_fmt_var.get(), start_paused, s, e)

def act_pvid_check():
    analyze_playlist(
        get_video_opts(pvid_q_var, pvid_s_var, pvid_fmt_var, pvid_path_var.get(), True),
        pvid_entry.get().strip(), pvid_scroll, pvid_checkboxes,
        pvid_dynamic_lbl, pvid_stale_banner, is_audio=False, tab="Playlist Video",
        thumb_label=pvid_thumb_label)

def act_pvid_dl(start_paused=False):
    start_playlist_download(pvid_q_var, pvid_s_var, pvid_fmt_var,
                             pvid_path_var.get(), pvid_entry.get().strip(),
                             pvid_checkboxes, True, "Playlist Video", start_paused)

def act_paud_check():
    analyze_playlist(
        get_audio_opts(paud_q_var, paud_fmt_var, paud_path_var.get(), True),
        paud_entry.get().strip(), paud_scroll, paud_checkboxes,
        paud_dynamic_lbl, paud_stale_banner, is_audio=True,
        audio_bitrate=get_audio_bitrate(paud_q_var), tab="Playlist Audio",
        thumb_label=paud_thumb_label)

def act_paud_dl(start_paused=False):
    start_playlist_download(paud_q_var, None, paud_fmt_var,
                             paud_path_var.get(), paud_entry.get().strip(),
                             paud_checkboxes, False, "Playlist Audio", start_paused)

# ==========================================
#  TAB 1 — SINGLE VIDEO
# ==========================================
t1 = tabview.tab("Single Video")
t1_top = ctk.CTkFrame(t1, fg_color="transparent")
t1_top.pack(fill="x", padx=20, pady=(8, 0))
t1_left = ctk.CTkFrame(t1_top, fg_color="transparent")
t1_left.pack(side="left", fill="both", expand=True)
make_section_label(t1_left, "Video link")
vid_entry = make_entry_row(t1_left, "Paste YouTube / any site URL here…")
bind_url_hint(vid_entry, "Single Video", "Playlist Video")
make_section_label(t1_left, "Options")
vid_q_var, vid_s_var, vid_fmt_var = create_vid_options(t1_left)
vid_path_var   = create_path_selector(t1_left, VID_DIR)
vid_seg_var, vid_seg_start, vid_seg_end = make_segment_row(t1_left, act_svid_check)
vid_thumb_label = make_thumb_panel(t1_top)
make_divider(t1)
btn_check_vid  = make_check_btn(t1, "Step 1 — Check size & preview", act_svid_check)
vid_stale_banner = make_stale_banner(t1)
vid_info_box   = make_info_box(t1, height=55)
btn_dl_vid, btn_q_vid = make_dl_btn_group(t1, "⬇  Download Video", act_svid_dl, lambda: act_svid_dl(start_paused=True))
bind_keyboard_shortcuts(vid_entry, act_svid_dl)
attach_auto_check([vid_q_var, vid_s_var, vid_fmt_var], vid_entry, act_svid_check)
bind_url_change_clear(vid_entry, vid_info_box, vid_stale_banner)

# ==========================================
#  TAB 2 — SINGLE AUDIO
# ==========================================
t2 = tabview.tab("Single Audio")
t2_top = ctk.CTkFrame(t2, fg_color="transparent")
t2_top.pack(fill="x", padx=20, pady=(8, 0))
t2_left = ctk.CTkFrame(t2_top, fg_color="transparent")
t2_left.pack(side="left", fill="both", expand=True)
make_section_label(t2_left, "Audio link")
aud_entry = make_entry_row(t2_left, "Paste YouTube / any site URL here…")
bind_url_hint(aud_entry, "Single Audio", "Playlist Audio")
make_section_label(t2_left, "Options")
aud_q_var, aud_fmt_var = create_aud_options(t2_left)
aud_path_var   = create_path_selector(t2_left, AUD_DIR)
aud_seg_var, aud_seg_start, aud_seg_end = make_segment_row(t2_left, act_saud_check)
aud_thumb_label = make_thumb_panel(t2_top, "Thumbnail\nappears here")
make_divider(t2)
btn_check_aud  = make_check_btn(t2, "Step 1 — Check size & preview", act_saud_check)
aud_stale_banner = make_stale_banner(t2)
aud_info_box   = make_info_box(t2, height=55)
btn_dl_aud, btn_q_aud = make_dl_btn_group(t2, "⬇  Download Audio", act_saud_dl, lambda: act_saud_dl(start_paused=True))
bind_keyboard_shortcuts(aud_entry, act_saud_dl)
attach_auto_check([aud_q_var, aud_fmt_var], aud_entry, act_saud_check)
bind_url_change_clear(aud_entry, aud_info_box, aud_stale_banner)

# ==========================================
# ==========================================
#  TAB 3 — BATCH VIDEO
# ==========================================
t3 = tabview.tab("Batch Video")

# ── Bottom section packed FIRST so buttons are always visible ──
bvid_bottom = ctk.CTkFrame(t3, fg_color="transparent")
bvid_bottom.pack(side="bottom", fill="x", pady=(0, 10))

bvid_stale_banner = make_stale_banner(bvid_bottom)
bvid_info_box   = make_info_box(bvid_bottom, height=55)
btn_dl_bvid, btn_q_bvid = make_dl_btn_group(bvid_bottom, "⬇  Download Batch", act_bvid_dl, lambda: act_bvid_dl(start_paused=True))

# ── Top section fills remaining space ──
t3_top = ctk.CTkFrame(t3, fg_color="transparent")
t3_top.pack(fill="both", expand=True, padx=20, pady=(8, 0))
t3_left = ctk.CTkFrame(t3_top, fg_color="transparent")
t3_left.pack(side="left", fill="both", expand=True)
make_section_label(t3_left, "Video links  (one per line)")
bvid_text = make_textbox_row(t3_left)
make_section_label(t3_left, "Options")
bvid_q_var, bvid_s_var, bvid_fmt_var = create_vid_options(t3_left)
bvid_path_var   = create_path_selector(t3_left, VID_DIR)
bvid_seg_var, bvid_seg_start, bvid_seg_end = make_segment_row(t3_left, act_bvid_check)
bvid_thumb_label = make_thumb_panel(t3_top, "First link\npreview")

btn_check_bvid  = make_check_btn(t3, "Step 1 — Analyze links", act_bvid_check)

attach_auto_check([bvid_q_var, bvid_s_var, bvid_fmt_var], bvid_text, act_bvid_check)
bind_text_change_clear(bvid_text, bvid_info_box, bvid_stale_banner)

# ==========================================
#  TAB 4 — BATCH AUDIO
# ==========================================
t4 = tabview.tab("Batch Audio")

# ── Bottom section packed FIRST so buttons are always visible ──
baud_bottom = ctk.CTkFrame(t4, fg_color="transparent")
baud_bottom.pack(side="bottom", fill="x", pady=(0, 10))

baud_stale_banner = make_stale_banner(baud_bottom)
baud_info_box     = make_info_box(baud_bottom, height=55)
btn_dl_baud, btn_q_baud = make_dl_btn_group(baud_bottom, "⬇  Download Batch", act_baud_dl, lambda: act_baud_dl(start_paused=True))

# ── Top section fills remaining space ──
t4_top = ctk.CTkFrame(t4, fg_color="transparent")
t4_top.pack(fill="both", expand=True, padx=20, pady=(8, 0))
t4_left = ctk.CTkFrame(t4_top, fg_color="transparent")
t4_left.pack(side="left", fill="both", expand=True)
make_section_label(t4_left, "Audio links  (one per line)")
baud_text = make_textbox_row(t4_left)
make_section_label(t4_left, "Options")
baud_q_var, baud_fmt_var = create_aud_options(t4_left)
baud_path_var   = create_path_selector(t4_left, AUD_DIR)
baud_seg_var, baud_seg_start, baud_seg_end = make_segment_row(t4_left, act_baud_check)
baud_thumb_label = make_thumb_panel(t4_top, "First link\npreview")

btn_check_baud    = make_check_btn(t4, "Step 1 — Analyze links", act_baud_check)

attach_auto_check([baud_q_var, baud_fmt_var], baud_text, act_baud_check)
bind_text_change_clear(baud_text, baud_info_box, baud_stale_banner)

# ==========================================
#  TAB 5 — PLAYLIST VIDEO
# ==========================================
t5 = tabview.tab("Playlist Video")
t5_top = ctk.CTkFrame(t5, fg_color="transparent")
t5_top.pack(fill="x", padx=20, pady=(8, 0))
t5_left = ctk.CTkFrame(t5_top, fg_color="transparent")
t5_left.pack(side="left", fill="both", expand=True)
make_section_label(t5_left, "Playlist link")
pvid_entry = make_entry_row(t5_left, "Paste YouTube playlist URL here…")
bind_url_hint(pvid_entry, "Playlist Video", "Single Video")
make_section_label(t5_left, "Options")
pvid_q_var, pvid_s_var, pvid_fmt_var = create_vid_options(t5_left)
pvid_path_var    = create_path_selector(t5_left, VID_DIR)
pvid_thumb_label  = make_thumb_panel(t5_top, "Playlist cover\nappears here")

pvid_stale_banner = make_stale_banner(t5)
btn_check_pvid    = make_check_btn(t5, "Step 1 — Fetch checklist", act_pvid_check)

pvid_ctrl = ctk.CTkFrame(t5, fg_color="transparent")
pvid_ctrl.pack(fill="x", padx=20, pady=(4, 2))
for txt, st in [("Select all", 1), ("Deselect all", 0)]:
    col = COL_ACCENT if st == 1 else COL_CHECK
    b   = ctk.CTkButton(pvid_ctrl, text=txt, width=100, font=BTN_SUB,
                        fg_color=col,
                        command=lambda s=st: toggle_all_checkboxes(
                            pvid_checkboxes, s, pvid_dynamic_lbl))
    b.pack(side="left", padx=(0, 6) if st == 1 else 0)
    MANAGED_BUTTONS.append(b)

# Range selector row
_pvid_range_frame = ctk.CTkFrame(t5, fg_color="transparent")
_pvid_range_frame.pack(fill="x", padx=20, pady=(2, 0))
ctk.CTkLabel(_pvid_range_frame, text="Range:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
pvid_range_entry = ctk.CTkEntry(_pvid_range_frame, width=110, font=ENTRY_FONT,
                                 placeholder_text="e.g. 3-10")
pvid_range_entry.pack(side="left", padx=(0, 6))
def _apply_pvid_range():
    txt = pvid_range_entry.get().strip()
    if not txt or not pvid_checkboxes: return
    try:
        if "-" in txt:
            a, b = txt.split("-", 1)
            sel = set(range(int(a.strip()), int(b.strip()) + 1))
        elif "," in txt:
            sel = {int(x.strip()) for x in txt.split(",")}
        else:
            sel = {int(txt)}
        for idx, var, _, _ in pvid_checkboxes:
            var.set(1 if idx in sel else 0)
        update_dynamic_size(pvid_checkboxes, pvid_dynamic_lbl)
    except Exception:
        pass
ctk.CTkButton(_pvid_range_frame, text="Apply", width=80, height=28, font=BTN_SUB,
              fg_color=COL_CHECK, hover_color=COL_CHECKH,
              command=_apply_pvid_range).pack(side="left")
ctk.CTkLabel(_pvid_range_frame, text="Select by range or comma list",
             font=("Segoe UI", 10), text_color=COL_MUTED).pack(side="left", padx=(8, 0))

pvid_checkboxes = []
pvid_scroll = ctk.CTkScrollableFrame(t5, fg_color=COL_DARK, height=160)
pvid_bottom = ctk.CTkFrame(t5, fg_color="transparent")

pvid_bottom.pack(side="bottom", fill="x", pady=(0, 10))
pvid_scroll.pack(side="top", fill="both", expand=True, padx=20, pady=(4, 0))

pvid_summary = ctk.CTkFrame(pvid_bottom, fg_color=COL_DARK, corner_radius=8)
pvid_summary.pack(fill="x", padx=20, pady=(6, 4))
pvid_dynamic_lbl = ctk.CTkLabel(pvid_summary,
    text="Selected: 0 / 0   |   Est. total size: —",
    text_color=COL_ACCENT, font=("Segoe UI", 14, "bold"), anchor="center")
pvid_dynamic_lbl.pack(fill="x", padx=16, pady=8)

btn_dl_pvid, btn_q_pvid = make_playlist_dl_btn_group(pvid_bottom, "⬇  Download Selected", act_pvid_dl, lambda: act_pvid_dl(start_paused=True))
pvid_info_box = make_info_box(pvid_bottom, height=1)
attach_auto_check([pvid_q_var, pvid_s_var, pvid_fmt_var], pvid_entry, act_pvid_check)
bind_url_change_clear(pvid_entry, pvid_info_box, pvid_stale_banner)
pvid_info_box.pack_forget()

# ==========================================
#  TAB 6 — PLAYLIST AUDIO
# ==========================================
t6 = tabview.tab("Playlist Audio")
t6_top = ctk.CTkFrame(t6, fg_color="transparent")
t6_top.pack(fill="x", padx=20, pady=(8, 0))
t6_left = ctk.CTkFrame(t6_top, fg_color="transparent")
t6_left.pack(side="left", fill="both", expand=True)
make_section_label(t6_left, "Playlist link")
paud_entry = make_entry_row(t6_left, "Paste YouTube playlist URL here…")
bind_url_hint(paud_entry, "Playlist Audio", "Single Audio")
make_section_label(t6_left, "Options")
paud_q_var, paud_fmt_var = create_aud_options(t6_left)
paud_path_var    = create_path_selector(t6_left, AUD_DIR)
paud_thumb_label  = make_thumb_panel(t6_top, "Playlist cover\nappears here")
paud_stale_banner = make_stale_banner(t6)
btn_check_paud    = make_check_btn(t6, "Step 1 — Fetch checklist", act_paud_check)

paud_ctrl = ctk.CTkFrame(t6, fg_color="transparent")
paud_ctrl.pack(fill="x", padx=20, pady=(4, 2))
for txt, st in [("Select all", 1), ("Deselect all", 0)]:
    col = COL_ACCENT if st == 1 else COL_CHECK
    b   = ctk.CTkButton(paud_ctrl, text=txt, width=100, font=BTN_SUB,
                        fg_color=col,
                        command=lambda s=st: toggle_all_checkboxes(
                            paud_checkboxes, s, paud_dynamic_lbl))
    b.pack(side="left", padx=(0, 6) if st == 1 else 0)
    MANAGED_BUTTONS.append(b)

# Range selector row
_paud_range_frame = ctk.CTkFrame(t6, fg_color="transparent")
_paud_range_frame.pack(fill="x", padx=20, pady=(2, 0))
ctk.CTkLabel(_paud_range_frame, text="Range:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
paud_range_entry = ctk.CTkEntry(_paud_range_frame, width=110, font=ENTRY_FONT,
                                 placeholder_text="e.g. 3-10")
paud_range_entry.pack(side="left", padx=(0, 6))
def _apply_paud_range():
    txt = paud_range_entry.get().strip()
    if not txt or not paud_checkboxes: return
    try:
        if "-" in txt:
            a, b = txt.split("-", 1)
            sel = set(range(int(a.strip()), int(b.strip()) + 1))
        elif "," in txt:
            sel = {int(x.strip()) for x in txt.split(",")}
        else:
            sel = {int(txt)}
        for idx, var, _, _ in paud_checkboxes:
            var.set(1 if idx in sel else 0)
        update_dynamic_size(paud_checkboxes, paud_dynamic_lbl)
    except Exception:
        pass
ctk.CTkButton(_paud_range_frame, text="Apply", width=80, height=28, font=BTN_SUB,
              fg_color=COL_CHECK, hover_color=COL_CHECKH,
              command=_apply_paud_range).pack(side="left")
ctk.CTkLabel(_paud_range_frame, text="Select by range or comma list",
             font=("Segoe UI", 10), text_color=COL_MUTED).pack(side="left", padx=(8, 0))

paud_checkboxes = []
paud_scroll = ctk.CTkScrollableFrame(t6, fg_color=COL_DARK, height=160)
paud_bottom = ctk.CTkFrame(t6, fg_color="transparent")

paud_bottom.pack(side="bottom", fill="x", pady=(0, 10))
paud_scroll.pack(side="top", fill="both", expand=True, padx=20, pady=(4, 0))

paud_summary = ctk.CTkFrame(paud_bottom, fg_color=COL_DARK, corner_radius=8)
paud_summary.pack(fill="x", padx=20, pady=(6, 4))
paud_dynamic_lbl = ctk.CTkLabel(paud_summary,
    text="Selected: 0 / 0   |   Est. total size: —",
    text_color=COL_ACCENT, font=("Segoe UI", 14, "bold"), anchor="center")
paud_dynamic_lbl.pack(fill="x", padx=16, pady=8)

btn_dl_paud, btn_q_paud = make_playlist_dl_btn_group(paud_bottom, "⬇  Download Selected", act_paud_dl, lambda: act_paud_dl(start_paused=True))
paud_info_box = make_info_box(paud_bottom, height=1)
attach_auto_check([paud_q_var, paud_fmt_var], paud_entry, act_paud_check)
bind_url_change_clear(paud_entry, paud_info_box, paud_stale_banner)
paud_info_box.pack_forget()

# ==========================================
#  TAB QUEUE
# ==========================================
t_queue = tabview.tab("Queue")
make_section_label(t_queue, "Download Queue")

# ── Live Network Monitor & Throughput Graph ──
net_frame = ctk.CTkFrame(t_queue, fg_color=COL_PANEL, corner_radius=10)
net_frame.pack(fill="x", padx=20, pady=(2, 6))

net_top = ctk.CTkFrame(net_frame, fg_color="transparent")
net_top.pack(fill="x", padx=12, pady=(8, 4))

lbl_q_speed = ctk.CTkLabel(net_top, text="⚡ Speed: 0 B/s", font=("Segoe UI", 12, "bold"), text_color=COL_ACCENT)
lbl_q_speed.pack(side="left", padx=(0, 18))
lbl_q_speed_ref = lbl_q_speed

lbl_q_peak = ctk.CTkLabel(net_top, text="▲ Peak: 0 B/s", font=("Segoe UI", 11), text_color=COL_MUTED)
lbl_q_peak.pack(side="left", padx=(0, 18))
lbl_q_peak_ref = lbl_q_peak

lbl_q_active = ctk.CTkLabel(net_top, text="⬇ Active: 0", font=("Segoe UI", 11), text_color=COL_MUTED)
lbl_q_active.pack(side="left", padx=(0, 18))
lbl_q_active_ref = lbl_q_active

lbl_q_total = ctk.CTkLabel(net_top, text="📦 Session: 0 completed", font=("Segoe UI", 11), text_color=COL_MUTED)
lbl_q_total.pack(side="right")
lbl_q_total_ref = lbl_q_total

# Graph canvas
speed_canvas = ctk.CTkCanvas(net_frame, height=65, bg="#080C14", highlightthickness=0)
speed_canvas.pack(fill="x", padx=12, pady=(0, 8))
speed_canvas_ref = speed_canvas

queue_ctrl = ctk.CTkFrame(t_queue, fg_color="transparent")
queue_ctrl.pack(fill="x", padx=20, pady=(2, 2))
ctk.CTkButton(queue_ctrl, text="Clear Finished", width=110, font=BTN_SUB,
              command=global_queue.clear_finished).pack(side="left")
queue_box = ctk.CTkScrollableFrame(t_queue, fg_color=COL_DARK)
queue_box.pack(fill="both", expand=True, padx=20, pady=(4, 14))
queue_box_ref = queue_box
refresh_queue_tab()

# ==========================================
#  TAB 7 — HISTORY
# ==========================================
t7 = tabview.tab("History")
make_section_label(t7, "Recent downloads  (last 200)")
hist_ctrl = ctk.CTkFrame(t7, fg_color="transparent")
hist_ctrl.pack(fill="x", padx=20, pady=(4, 2))

def clear_history():
    if messagebox.askyesno("Clear history", "Delete all download history?"):
        try:
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
        except Exception:
            pass
        refresh_history_tab()

ctk.CTkButton(hist_ctrl, text="Refresh",       width=90,  font=BTN_SUB,
              command=refresh_history_tab).pack(side="left", padx=(0, 6))
ctk.CTkButton(hist_ctrl, text="Clear history", width=110, font=BTN_SUB,
              fg_color="#7F1D1D", hover_color="#450A0A",
              command=clear_history).pack(side="left")

history_box = ctk.CTkScrollableFrame(t7, fg_color=COL_DARK)
history_box.pack(fill="both", expand=True, padx=20, pady=(4, 14))
history_box_ref = history_box

# ==========================================
#  TAB 8 — SETTINGS
# ==========================================
t8 = tabview.tab("Settings")
# Scrollable wrapper — ensures About section is never cut off
t8_scroll = ctk.CTkScrollableFrame(t8, fg_color="transparent")
t8_scroll.pack(fill="both", expand=True, padx=0, pady=0)

make_section_label(t8_scroll, "About")
about_frame = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=10)
about_frame.pack(fill="x", padx=20, pady=(4, 8))
ctk.CTkLabel(about_frame,
    text=f"Hedra Downloader ULTIMATE  {APP_VERSION}",
    font=("Segoe UI", 15, "bold"), text_color=COL_TEXT
).pack(pady=(14, 2))
ctk.CTkLabel(about_frame,
    text=f"Made by  {APP_AUTHOR}",
    font=("Segoe UI", 12, "bold"), text_color=COL_ACCENT
).pack(pady=(0, 4))
ctk.CTkLabel(about_frame,
    text="Powered by yt-dlp  •  FFmpeg  •  customtkinter",
    font=("Segoe UI", 11), text_color=COL_MUTED
).pack(pady=(0, 4))
ctk.CTkLabel(about_frame,
    text=f"Downloads → {BASE_DIR}",
    font=("Consolas", 10), text_color=COL_MUTED
).pack(pady=(0, 12))

make_divider(t8_scroll)

# ── Appearance section ────────────────────────────────────
make_section_label(t8_scroll, "Appearance")
_pal_outer = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
_pal_outer.pack(fill="x", padx=20, pady=6)
_pal_row = ctk.CTkFrame(_pal_outer, fg_color="transparent")
_pal_row.pack(fill="x", padx=12, pady=10)

def apply_palette(name):
    """Save palette choice and restart the app for a clean re-render."""
    global _ACTIVE_PALETTE
    _ACTIVE_PALETTE = name
    try:
        save_settings()
        save_queue()
    except Exception:
        pass
    python = sys.executable
    subprocess.Popen([python] + sys.argv)
    os._exit(0)

_PAL_PREVIEWS = {
    "Default":   ("#38BDF8", "#0B0F19", "Sky blue / Midnight"),
    "Pure Dark": ("#A78BFA", "#000000", "Violet / OLED black"),
    "Light":     ("#2563EB", "#F1F5F9", "Royal blue / Light"),
}
for _pname, (_pacc, _pbg, _pdesc) in _PAL_PREVIEWS.items():
    _card = ctk.CTkFrame(_pal_row, fg_color=_pbg, corner_radius=10,
                         border_width=2 if _pname == _ACTIVE_PALETTE else 0,
                         border_color=_pacc)
    _card.pack(side="left", padx=8, pady=6, ipadx=10, ipady=8)
    ctk.CTkLabel(_card, text=_pname, font=("Segoe UI", 12, "bold"),
                 text_color="#FFFFFF" if _pbg != "#F1F5F9" else "#0F172A").pack(padx=12, pady=(6, 2))
    ctk.CTkLabel(_card, text=_pdesc, font=("Segoe UI", 9),
                 text_color="#94A3B8" if _pbg != "#F1F5F9" else "#475569").pack(padx=12, pady=(0, 4))
    _dot = ctk.CTkFrame(_card, width=28, height=28, corner_radius=14, fg_color=_pacc)
    _dot.pack(pady=(0, 6))
    ctk.CTkButton(_card, text="Apply & Restart", width=120, height=28, font=BTN_SUB,
                  fg_color=_pacc if _pbg != "#F1F5F9" else "#2563EB",
                  hover_color="#555",
                  command=lambda n=_pname: apply_palette(n)
                  ).pack(pady=(0, 8), padx=12)

ctk.CTkLabel(_pal_outer, text="* Theme changes require an instant restart to apply completely",
             font=("Segoe UI", 11, "italic"), text_color=COL_MUTED).pack(pady=(0, 10))

make_divider(t8_scroll)
make_section_label(t8_scroll, "Supported Websites")
websites_frame = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
websites_frame.pack(fill="x", padx=20, pady=6)

# ── Logo badge grid ──────────────────────────────────────────────
_sites_grid = ctk.CTkFrame(websites_frame, fg_color="transparent")
_sites_grid.pack(fill="x", padx=12, pady=(10, 4))
COLS = 5
for _si, (_sname, _sdomain, _scolor) in enumerate(SUPPORTED_SITES):
    _scol = _si % COLS
    _srow = _si // COLS
    _sites_grid.columnconfigure(_scol, weight=1)
    _badge = ctk.CTkFrame(_sites_grid, fg_color=COL_DARK, corner_radius=10)
    _badge.grid(row=_srow, column=_scol, padx=5, pady=5, sticky="ew")
    # Logo label — starts as emoji globe, replaced async with real favicon
    _logo_lbl = ctk.CTkLabel(
        _badge, text="🌐",
        font=("Segoe UI", 18), width=28, height=28,
        text_color=_scolor if _scolor != "#000000" else COL_MUTED)
    _logo_lbl.pack(side="left", padx=(10, 6), pady=10)
    ctk.CTkLabel(
        _badge, text=_sname,
        font=("Segoe UI", 11, "bold"),
        text_color=COL_TEXT, anchor="w"
    ).pack(side="left", padx=(0, 10), pady=10)
    # Kick off async logo fetch
    threading.Thread(
        target=_load_site_logo,
        args=(_sdomain, _logo_lbl, _scolor),
        daemon=True
    ).start()
ctk.CTkLabel(
    websites_frame,
    text="...and 1,000+ more sites supported via yt-dlp",
    font=("Segoe UI", 10), text_color=COL_MUTED
).pack(pady=(2, 10))

make_divider(t8_scroll)
make_section_label(t8_scroll, "Tab guide")
tab_guide_frame = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
tab_guide_frame.pack(fill="x", padx=20, pady=6)

TAB_DESCRIPTIONS = [
    ("Single Video",   "Download one video from any URL. Check size and preview thumbnail first."),
    ("Single Audio",   "Extract audio from one URL and save as MP3, FLAC, WAV, or M4A."),
    ("Batch Video",    "Download multiple videos at once — paste one URL per line."),
    ("Batch Audio",    "Extract audio from multiple URLs at once — paste one URL per line."),
    ("Playlist Video", "Fetch a full playlist, check/uncheck individual videos, then download."),
    ("Playlist Audio", "Fetch a full playlist and extract all (or selected) tracks as audio."),
    ("Queue",          "Manage background downloads. Pause, resume, or cancel jobs sequentially."),
    ("History",        "View and manage your recent download history (last 200 entries)."),
    ("Settings",       "Global options that apply to every tab: cookies, speed limit, connections, and more."),
]

for i, (tab_name, desc) in enumerate(TAB_DESCRIPTIONS):
    row = ctk.CTkFrame(tab_guide_frame, fg_color="transparent")
    row.pack(fill="x", padx=12, pady=(8 if i == 0 else 4, 4 if i < len(TAB_DESCRIPTIONS)-1 else 10))
    ctk.CTkLabel(row, text=f"{tab_name}:", font=("Segoe UI", 12, "bold"),
                 text_color=COL_MUTED, width=130, anchor="w").pack(side="left", padx=(0, 8))
    ctk.CTkLabel(row, text=desc, font=("Segoe UI", 11),
                 text_color=COL_MUTED, anchor="w", wraplength=540,
                 justify="left").pack(side="left", fill="x", expand=True)

make_divider(t8_scroll)
make_section_label(t8_scroll, "Global download settings")
gset = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
gset.pack(fill="x", padx=20, pady=6)

gr1 = ctk.CTkFrame(gset, fg_color="transparent")
gr1.pack(fill="x", padx=12, pady=(10, 4))
ctk.CTkLabel(gr1, text="Cookies from:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_cookie_var = ctk.StringVar(value="None")
ctk.CTkOptionMenu(gr1, variable=global_cookie_var, width=110,
                  values=COOKIE_BROWSERS).pack(side="left", padx=(0, 20))

ctk.CTkLabel(gr1, text="Max Downloads:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_max_downloads_var = ctk.StringVar(value="1")
ctk.CTkOptionMenu(gr1, variable=global_max_downloads_var, width=70,
                  values=["1", "2", "3", "4", "5"]).pack(side="left", padx=(0, 20))
ctk.CTkLabel(gr1, text="Speed limit:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_ratelimit_entry = ctk.CTkEntry(gr1, width=90, font=ENTRY_FONT,
                                       placeholder_text="e.g. 5M")
global_ratelimit_entry.pack(side="left", padx=(0, 20))
ctk.CTkLabel(gr1, text="Retries:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_retries_var = ctk.StringVar(value="3")
ctk.CTkOptionMenu(gr1, variable=global_retries_var, width=70,
                  values=[str(i) for i in range(1, 11)]).pack(side="left")

# ── Cookies .txt file selector (bypasses Windows Chrome/Edge DPAPI lock) ──
gr1b = ctk.CTkFrame(gset, fg_color="transparent")
gr1b.pack(fill="x", padx=12, pady=(2, 4))
ctk.CTkLabel(gr1b, text="Cookies File:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_cookie_file_var = ctk.StringVar(value="")
cookie_file_entry = ctk.CTkEntry(gr1b, textvariable=global_cookie_file_var, font=ENTRY_FONT, placeholder_text="Select cookies.txt file (optional)")
cookie_file_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))

def _browse_cookie_file():
    f = ctk.filedialog.askopenfilename(
        title="Select cookies.txt file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if f:
        global_cookie_file_var.set(f)

def _paste_cookie_clipboard():
    try:
        text = app.clipboard_get().strip()
        if not text:
            messagebox.showwarning("Clipboard Empty", "Clipboard does not contain any cookie text.")
            return
        target_path = os.path.join(DATA_DIR, "cookies.txt")
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(text)
        global_cookie_file_var.set(target_path)
        save_settings()
        messagebox.showinfo("Cookies Saved", "✔ Cookies saved successfully! Instagram and restricted downloads are now enabled.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save cookies: {e}")

def _clear_cookie_file():
    global_cookie_file_var.set("")

ctk.CTkButton(gr1b, text="Browse", width=65, font=BTN_SUB, command=_browse_cookie_file).pack(side="left", padx=(0, 4))
ctk.CTkButton(gr1b, text="📋 Paste", width=65, font=BTN_SUB, fg_color="#0F766E", hover_color="#115E59", command=_paste_cookie_clipboard).pack(side="left", padx=(0, 4))
ctk.CTkButton(gr1b, text="✕", width=28, font=("Segoe UI", 12, "bold"), fg_color="#7F1D1D", hover_color="#450A0A", command=_clear_cookie_file).pack(side="left", padx=(0, 10))
ctk.CTkLabel(gr1b, text="💡 Export via 'Get cookies.txt' extension to bypass Windows Chrome DPAPI lock", font=("Segoe UI", 10), text_color=COL_MUTED).pack(side="left")

gr2 = ctk.CTkFrame(gset, fg_color="transparent")
gr2.pack(fill="x", padx=12, pady=(4, 4))
ctk.CTkLabel(gr2, text="Connections:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_concurrent_var = ctk.StringVar(value="4")
ctk.CTkOptionMenu(gr2, variable=global_concurrent_var, width=70,
                  values=[str(i) for i in range(1, 9)]).pack(side="left", padx=(0, 20))
ctk.CTkLabel(gr2, text="(parallel fragment downloads — higher = faster for DASH/HLS)",
             font=("Segoe UI", 10), text_color=COL_MUTED).pack(side="left")

gr2b = ctk.CTkFrame(gset, fg_color="transparent")
gr2b.pack(fill="x", padx=12, pady=(0, 4))
ctk.CTkLabel(gr2b, text="Proxy:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_proxy_entry = ctk.CTkEntry(gr2b, width=220, font=ENTRY_FONT,
                                   placeholder_text="e.g. socks5://127.0.0.1:1080")
global_proxy_entry.pack(side="left", padx=(0, 14))
ctk.CTkLabel(gr2b, text="HTTP or SOCKS5 — leave blank for direct",
             font=("Segoe UI", 10), text_color=COL_MUTED).pack(side="left")

gr3 = ctk.CTkFrame(gset, fg_color="transparent")
gr3.pack(fill="x", padx=12, pady=(0, 6))
global_archive_var = ctk.BooleanVar(value=False)
ctk.CTkCheckBox(gr3, text="Skip already-downloaded  (maintains an archive file)",
                variable=global_archive_var, font=("Segoe UI", 12)).pack(side="left")

# ── Row 4: Subtitle mode & Notifications ──
gr4 = ctk.CTkFrame(gset, fg_color="transparent")
gr4.pack(fill="x", padx=12, pady=(0, 10))
ctk.CTkLabel(gr4, text="Subtitle Mode:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_sub_mode_var = ctk.StringVar(value="Embed in Video")
ctk.CTkOptionMenu(gr4, variable=global_sub_mode_var, width=150,
                  values=SUBTITLE_MODES).pack(side="left", padx=(0, 20))

global_notify_toast_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(gr4, text="Desktop Notifications", variable=global_notify_toast_var,
                font=("Segoe UI", 12)).pack(side="left", padx=(0, 16))

global_notify_sound_var = ctk.BooleanVar(value=True)
ctk.CTkCheckBox(gr4, text="Completion Sound", variable=global_notify_sound_var,
                font=("Segoe UI", 12)).pack(side="left")

make_divider(t8_scroll)
make_section_label(t8_scroll, "Advanced Integrations")
adv_set = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=14)
adv_set.pack(fill="x", padx=20, pady=6)

global_sponsorblock_var = ctk.BooleanVar(value=False)
global_metadata_var = ctk.BooleanVar(value=True)

ar1 = ctk.CTkFrame(adv_set, fg_color="transparent")
ar1.pack(fill="x", padx=12, pady=(10, 4))
ctk.CTkCheckBox(ar1, text="SponsorBlock: Automatically remove sponsor segments from YouTube",
                variable=global_sponsorblock_var, font=("Segoe UI", 12)).pack(side="left")

ar2 = ctk.CTkFrame(adv_set, fg_color="transparent")
ar2.pack(fill="x", padx=12, pady=(4, 10))
ctk.CTkCheckBox(ar2, text="Embed Metadata: Embed chapters, thumbnails, and descriptions",
                variable=global_metadata_var, font=("Segoe UI", 12)).pack(side="left")

make_divider(t8_scroll)
make_section_label(t8_scroll, "Folders")
frow = ctk.CTkFrame(t8_scroll, fg_color="transparent")
frow.pack(padx=20, pady=4)
ctk.CTkButton(frow, text="📂  Open Video folder", width=200, height=38, font=BTN_SUB,
              command=lambda: open_folder(VID_DIR)).pack(side="left", padx=(0, 10))
ctk.CTkButton(frow, text="📂  Open Audio folder", width=200, height=38, font=BTN_SUB,
              command=lambda: open_folder(AUD_DIR)).pack(side="left")

make_divider(t8_scroll)
make_section_label(t8_scroll, "Keyboard shortcuts")
shortcuts_box = ctk.CTkTextbox(t8_scroll, height=80, state="normal",
                                fg_color=COL_DARK, text_color=COL_MUTED,
                                font=MONO_FONT)
shortcuts_box.insert("1.0",
    "  Ctrl + V   /   📋 button  →  Paste link  (works on any keyboard layout)\n"
    "  Ctrl + S                  →  Start download  (from link entry fields)\n"
    "  Escape                    →  Stop current download\n"
    "  Drag & Drop               →  Drop .txt or link directly into any tab\n"
    "  📋 button on batch box    →  Paste links from clipboard\n"
    "  ✕  button on batch box    →  Clear all links")
shortcuts_box.configure(state="disabled")
shortcuts_box.pack(fill="x", padx=20, pady=4)
app.bind_all("<Escape>", lambda e: trigger_stop())

make_divider(t8_scroll)
make_section_label(t8_scroll, "Maintenance")
btn_update_cli = ctk.CTkButton(
    t8_scroll, text="⟳  Update yt-dlp", width=200, height=38, font=BTN_SUB,
    fg_color="#1D4ED8", hover_color="#1E3A8A", command=act_update_cli)
btn_update_cli.pack(pady=(6, 4))
MANAGED_BUTTONS.append(btn_update_cli)

# ==========================================
#  STARTUP & DRAG-AND-DROP
# ==========================================
_install_paste_fix()
refresh_history_tab()
app.after(500, update_queue_ui_periodic)

# ── Drag and Drop Handler ──────────────────────────────────────────
def _on_window_drop(files):
    if not files: return
    try:
        current_tab = tabview.get()
        first_item = files[0]
        decoded = first_item.decode('utf-8', errors='ignore') if isinstance(first_item, bytes) else str(first_item)
        decoded = decoded.strip()
        
        # If a .txt file is dropped
        if decoded.lower().endswith(".txt") and os.path.isfile(decoded):
            with open(decoded, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
            if current_tab == "Batch Video":
                bvid_text.configure(state="normal")
                bvid_text.delete("1.0", "end")
                bvid_text.insert("1.0", content)
                act_bvid_check()
            elif current_tab == "Batch Audio":
                baud_text.configure(state="normal")
                baud_text.delete("1.0", "end")
                baud_text.insert("1.0", content)
                act_baud_check()
            elif current_tab in ["Single Video", "Single Audio"]:
                urls = [l.strip() for l in content.splitlines() if l.strip()]
                if urls:
                    target_entry = vid_entry if current_tab == "Single Video" else aud_entry
                    target_entry.delete(0, "end")
                    target_entry.insert(0, urls[0])
                    if current_tab == "Single Video": act_svid_check()
                    else: act_saud_check()
            else:
                tabview.set("Batch Video")
                bvid_text.configure(state="normal")
                bvid_text.delete("1.0", "end")
                bvid_text.insert("1.0", content)
                act_bvid_check()
        else:
            # Dropped direct URL string or media file path
            if current_tab == "Single Video":
                vid_entry.delete(0, "end")
                vid_entry.insert(0, decoded)
                act_svid_check()
            elif current_tab == "Single Audio":
                aud_entry.delete(0, "end")
                aud_entry.insert(0, decoded)
                act_saud_check()
            elif current_tab == "Batch Video":
                bvid_text.configure(state="normal")
                bvid_text.insert("end", ("\n" if bvid_text.get("1.0", "end").strip() else "") + decoded)
                act_bvid_check()
            elif current_tab == "Batch Audio":
                baud_text.configure(state="normal")
                baud_text.insert("end", ("\n" if baud_text.get("1.0", "end").strip() else "") + decoded)
                act_baud_check()
            elif current_tab == "Playlist Video":
                pvid_entry.delete(0, "end")
                pvid_entry.insert(0, decoded)
                act_pvid_check()
            elif current_tab == "Playlist Audio":
                paud_entry.delete(0, "end")
                paud_entry.insert(0, decoded)
                act_paud_check()
    except Exception:
        pass

if WINDND_AVAILABLE:
    try:
        windnd.hook_dropfiles(app, func=_on_window_drop)
    except Exception:
        pass

# ── Load persisted settings and wire auto-save ───────────────────────
_saved = load_settings()
if _saved:
    if "cookie_browser" in _saved:  global_cookie_var.set(_saved["cookie_browser"])
    if "cookie_file" in _saved:     global_cookie_file_var.set(_saved["cookie_file"])
    if "max_downloads"  in _saved:  global_max_downloads_var.set(_saved["max_downloads"])
    if "retries"        in _saved:  global_retries_var.set(_saved["retries"])
    if "concurrent"     in _saved:  global_concurrent_var.set(_saved["concurrent"])
    if "archive"        in _saved:  global_archive_var.set(_saved["archive"])
    if "sponsorblock"   in _saved:  global_sponsorblock_var.set(_saved["sponsorblock"])
    if "embed_metadata" in _saved:  global_metadata_var.set(_saved["embed_metadata"])
    if "subtitle_mode"  in _saved:  global_sub_mode_var.set(_saved["subtitle_mode"])
    if "notify_toast"   in _saved:  global_notify_toast_var.set(_saved["notify_toast"])
    if "notify_sound"   in _saved:  global_notify_sound_var.set(_saved["notify_sound"])
    if _saved.get("ratelimit"):
        global_ratelimit_entry.delete(0, "end")
        global_ratelimit_entry.insert(0, _saved["ratelimit"])
    if _saved.get("proxy"):
        global_proxy_entry.delete(0, "end")
        global_proxy_entry.insert(0, _saved["proxy"])


def _autosave(*_):
    app.after(600, save_settings)
for _sv in [global_cookie_var, global_cookie_file_var, global_max_downloads_var, global_retries_var,
            global_concurrent_var, global_archive_var,
            global_sponsorblock_var, global_metadata_var,
            global_sub_mode_var, global_notify_toast_var, global_notify_sound_var]:
    _sv.trace_add("write", _autosave)
global_ratelimit_entry.bind("<FocusOut>", _autosave)
global_proxy_entry.bind("<FocusOut>", _autosave)

load_queue()
app.mainloop()
