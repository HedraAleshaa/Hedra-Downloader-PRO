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
import tkinter as tk
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
    bin_name = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    if hasattr(sys, '_MEIPASS') and os.path.isfile(os.path.join(sys._MEIPASS, bin_name)):
        return sys._MEIPASS
    exe_dir = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, 'frozen', False) else (os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd())
    if os.path.isfile(os.path.join(exe_dir, bin_name)):
        return exe_dir
    if os.path.isfile(os.path.join(os.getcwd(), bin_name)):
        return os.getcwd()
    for p in ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]:
        if os.path.isfile(os.path.join(p, "ffmpeg")):
            return p
    return exe_dir

if platform.system() != "Windows":
    for _extra in ["/opt/homebrew/bin", "/usr/local/bin"]:
        if _extra not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _extra + ":" + os.environ.get("PATH", "")

APP_VERSION  = "2.1"
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
THUMBS_DIR   = os.path.join(DATA_DIR, "thumbs")
ICONS_DIR    = os.path.join(DATA_DIR, "site_icons")
os.makedirs(VID_DIR, exist_ok=True)
os.makedirs(AUD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)

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
    "English":                ["en", "en-US", "en-GB"],
    "Arabic (العربية)":       ["ar"],
    "Spanish (Español)":      ["es"],
    "French (Français)":      ["fr"],
    "German (Deutsch)":       ["de"],
    "Japanese (日本語)":       ["ja"],
    "Chinese (中文)":         ["zh", "zh-Hans", "zh-Hant"],
    "Portuguese (Português)": ["pt", "pt-BR"],
    "Russian (Русский)":      ["ru"],
    "Korean (한국어)":         ["ko"],
    "Italian (Italiano)":     ["it"],
    "Turkish (Türkçe)":       ["tr"],
    "Hindi (हिन्दी)":          ["hi"],
    "All Available Languages": ["all"],
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
        "COL_CHECK":   "#18181B",
        "COL_CHECKH":  "#09090B",
        "COL_DL":      "#7C3AED",
        "COL_DLH":     "#6D28D9",
        "COL_DARK":    "#000000",
        "COL_PANEL":   "#0D0D0D",
        "COL_TEXT":    "#FFFFFF",
        "COL_MUTED":   "#9CA3AF",
        "COL_ACCENT":  "#A78BFA",
        "COL_SUCCESS": "#34D399",
        "COL_WARN":    "#FBBF24",
        "COL_ERR":     "#F87171",
        "COL_FOOTER":  "#000000",
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
        saved_p = _early.get("palette") or _early.get("theme_mode")
        if saved_p == "light": saved_p = "Light"
        if saved_p == "dark": saved_p = "Default"
        if saved_p in PALETTES:
            _load_palette_tokens(saved_p)
except Exception:
    pass

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
app.title(f"Hedra Downloader PRO {APP_VERSION}")

# Window Icon
_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), "icon.ico")
if hasattr(sys, '_MEIPASS'):
    _meipass_ico = os.path.join(sys._MEIPASS, "icon.ico")
    if os.path.isfile(_meipass_ico):
        _icon_path = _meipass_ico
if os.path.isfile(_icon_path):
    try:
        app.iconbitmap(_icon_path)
    except Exception:
        pass

# ==========================================
#  GLOBAL STATE
# ==========================================
cancel_event        = threading.Event()
MANAGED_BUTTONS     = []
_tab_status         = {name: ("Ready.", COL_MUTED) for name in TAB_NAMES}
_session_dl_count   = 0
_pulse_running      = False   # indeterminate progress animation flag
_pal_cards_dict     = {}

# ==========================================
#  THEME REGISTRY & LIVE RECOLOR ENGINE
# ==========================================
THEME_REGISTRY = {
    "panels": [],           # CTkFrame cards & options
    "dark_containers": [],  # CTkScrollableFrame containers
    "text_labels": [],      # Primary text labels
    "muted_labels": [],     # Secondary text labels & section labels
    "accent_labels": [],    # Accent colored labels
    "check_btns": [],       # Utility & preset buttons
    "dl_btns": [],          # Main download action buttons
    "dividers": [],         # Divider lines
    "textboxes": [],        # Batch URL textboxes
    "info_textboxes": [],   # Info & metadata textboxes
    "entries": [],          # Entry rows
}

def reg_widget(widget, category):
    """Register widget for instantaneous live recoloring."""
    if category in THEME_REGISTRY:
        THEME_REGISTRY[category].append(widget)
    return widget

def recolor_ui_live(name):
    """Recolor every widget in-memory across the entire application instantly."""
    _load_palette_tokens(name)

    # 1. Update Core Navigation & Footers
    try:
        tabview._segmented_button.configure(
            text_color=COL_TEXT,
            unselected_color=COL_PANEL,
            unselected_hover_color=COL_CHECK,
            selected_color=COL_DL,
            selected_hover_color=COL_DLH
        )
    except Exception:
        pass

    try:
        footer.configure(fg_color=COL_FOOTER)
        progress_bar.configure(fg_color=COL_PANEL, progress_color=COL_ACCENT)
        pct_label.configure(fg_color=COL_FOOTER, text_color=COL_ACCENT)
        status_label.configure(text_color=COL_MUTED)
        dl_counter_label.configure(text_color=COL_MUTED)
        btn_queue.configure(fg_color=COL_ACCENT)
    except Exception:
        pass

    # 2. Update Registered UI Components
    for w in list(THEME_REGISTRY["panels"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_PANEL)
        except Exception: pass

    for w in list(THEME_REGISTRY["dark_containers"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_DARK)
        except Exception: pass

    for w in list(THEME_REGISTRY["text_labels"]):
        try:
            if w.winfo_exists(): w.configure(text_color=COL_TEXT)
        except Exception: pass

    for w in list(THEME_REGISTRY["muted_labels"]):
        try:
            if w.winfo_exists(): w.configure(text_color=COL_MUTED)
        except Exception: pass

    for w in list(THEME_REGISTRY["accent_labels"]):
        try:
            if w.winfo_exists(): w.configure(text_color=COL_ACCENT)
        except Exception: pass

    for w in list(THEME_REGISTRY["check_btns"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT)
        except Exception: pass

    for w in list(THEME_REGISTRY["dl_btns"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_DL, hover_color=COL_DLH)
        except Exception: pass

    for w in list(THEME_REGISTRY["dividers"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_CHECK)
        except Exception: pass

    for w in list(THEME_REGISTRY["textboxes"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_DARK, text_color=COL_TEXT)
        except Exception: pass

    for w in list(THEME_REGISTRY["info_textboxes"]):
        try:
            if w.winfo_exists(): w.configure(fg_color=COL_DARK, text_color=COL_ACCENT)
        except Exception: pass

    for w in list(THEME_REGISTRY["entries"]):
        try:
            if w.winfo_exists(): w.configure(text_color=COL_TEXT)
        except Exception: pass

    # 3. Dynamic Lists / Cards Refresh
    try:
        refresh_history_tab()
    except Exception:
        pass
    try:
        refresh_queue_tab()
    except Exception:
        pass

    # 4. Update Settings Tab Theme Card Highlights
    for pname, pcard in _pal_cards_dict.items():
        try:
            pcard.configure(border_width=2 if pname == name else 0)
        except Exception:
            pass

    set_status(f"✔ Theme switched to {name} live.", COL_SUCCESS, "Settings")

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

def save_history_entry(title, url, mode, size_str, quality="—", file_type="—", file_path="", thumbnail=""):
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
        "thumbnail": thumbnail or "",
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

def extract_size_from_info(info, is_audio=False, audio_bitrate=None):
    sz = 0
    if 'entries' in info:
        total = 0
        for entry in info['entries']:
            if entry:
                total += extract_size_from_info(entry, is_audio, audio_bitrate)
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
    u = re.sub(r'https?://(?:web|touch|mbasic)\.facebook\.com', 'https://www.facebook.com', u, flags=re.IGNORECASE)

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
    if any(x in u for x in ["youtu.be/", "watch?v=", "youtube.com/shorts/", "tiktok.com/", "twitter.com/", "x.com/", "fb.watch/", "facebook.com/reel/", "facebook.com/watch", "facebook.com/share/", "facebook.com/story.php", "facebook.com/video.php", "vimeo.com/", "reddit.com/", "pin.it/"]):
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
    global_queue.queue_cancel.set()
    for jid, ev in list(global_queue.cancel_events.items()):
        try: ev.set()
        except: pass
    current = tabview.get()
    app.after(0, lambda: set_status("⏹  Aborting… cleaning up.", COL_ERR, current))
    app.after(100, global_queue.pump)

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
_site_logo_cache = {}

def _load_site_logo(domain, label_widget, accent_color):
    """Load or fetch a 28×28 site icon with local caching."""
    if not PIL_AVAILABLE:
        return
    local_icon = os.path.join(ICONS_DIR, f"{domain}.png")
    
    def _apply_image(img_obj):
        try:
            if img_obj.size != (28, 28):
                img_obj = img_obj.resize((28, 28), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img_obj, dark_image=img_obj, size=(28, 28))
            _site_logo_cache[domain] = ctk_img
            if label_widget.winfo_exists():
                label_widget._logo_ref = ctk_img
                label_widget.configure(image=ctk_img, text="", width=28)
        except Exception:
            pass

    # 1. Check memory cache
    if domain in _site_logo_cache:
        ctk_img = _site_logo_cache[domain]
        label_widget._logo_ref = ctk_img
        label_widget.configure(image=ctk_img, text="", width=28)
        return

    # 2. Check disk cache
    if os.path.isfile(local_icon):
        try:
            with Image.open(local_icon) as orig:
                img = orig.convert("RGBA").copy()
            _apply_image(img)
            return
        except Exception:
            pass

    # 3. Fallback to network download
    def _fetch_remote():
        try:
            url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = resp.read()
            with Image.open(io.BytesIO(data)) as orig:
                img = orig.convert("RGBA").copy()
            try:
                img.save(local_icon, format="PNG")
            except Exception:
                pass
            app.after(0, lambda: _apply_image(img))
        except Exception:
            pass

    threading.Thread(target=_fetch_remote, daemon=True).start()

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
    opts['extractor_args'] = {
        'youtube': {
            'player_client': ['android_vr', 'android', 'web', 'mweb']
        }
    }
    return opts

# ==========================================
#  OPTION BUILDERS
# ==========================================
def get_video_opts(q_var, sub_var, fmt_var, target_dir,
                   for_analysis=False, items_list=None):
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
        
        postprocessors = []
        
        sub_choice = sub_var.get() if sub_var else "None"
        if sub_choice not in ("None", "[MKV Required]"):
            lang_codes = SUBTITLE_LANG_MAP.get(sub_choice, ["en"])
            opts['writesubtitles'] = True
            opts['writeautomaticsub'] = True
            opts['subtitleslangs'] = lang_codes
            opts['ignoreerrors'] = 'only_download'
                
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
                postprocessors.append({'key': 'FFmpegSubtitlesConvertor', 'format': 'srt'})
                postprocessors.append({'key': 'FFmpegEmbedSubtitle', 'already_have_subtitle': False})
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
                   for_analysis=False, items_list=None):
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

queue_search_var = None
queue_filter_var = None

def refresh_queue_tab():
    if queue_box_ref is None: return
    for w in queue_box_ref.winfo_children(): w.destroy()
    if not global_queue.jobs:
        ctk.CTkLabel(queue_box_ref, text="Queue is empty.", text_color=COL_MUTED).pack(pady=20)
        return
        
    s_term = queue_search_var.get().strip().lower() if queue_search_var else ""
    s_filter = queue_filter_var.get() if queue_filter_var else "All"
    
    filtered_jobs = []
    for j in global_queue.jobs:
        if s_filter == "Active" and j.get("status") not in ["Pending", "Downloading"]:
            continue
        elif s_filter == "Paused" and j.get("status") != "Paused":
            continue
        elif s_filter == "Done" and j.get("status") != "Completed":
            continue
        elif s_filter == "Error" and j.get("status") not in ["Error", "Cancelled"]:
            continue
            
        if s_term:
            combined = f"{j.get('hint','')} {j.get('mode','')} {j.get('quality','')} {j.get('file_type','')} {j.get('status','')}".lower()
            if s_term not in combined:
                continue
        filtered_jobs.append(j)
        
    if not filtered_jobs:
        ctk.CTkLabel(queue_box_ref, text="No jobs matching your filter.", text_color=COL_MUTED).pack(pady=20)
        return
        
    for job in filtered_jobs:
        f = ctk.CTkFrame(queue_box_ref, fg_color=COL_PANEL, corner_radius=6)
        f.pack(fill="x", pady=4, padx=6)
        
        left = ctk.CTkFrame(f, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        title = job['hint']
        if len(title) > 65: title = title[:62] + "..."
        ctk.CTkLabel(left, text=title, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        
        info_parts = [f"Size: {job.get('size', 'Unknown')}", job.get('quality', '—'), job.get('file_type', '—')]
        if job.get('volume_boost') and "+" in job.get('volume_boost'):
            info_parts.append(f"🔊 {job.get('volume_boost')}")
        if job.get('trim_silence'):
            info_parts.append("✂ Trimmed")
        info_str = "  |  ".join(info_parts)
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
        
    def add(self, opts, links, folder_name, mode, hint, tab, size="Unknown", quality="—", file_type="—", start_paused=False, volume_boost="Normal (0 dB)", trim_silence=False):
        cancel_event.clear()
        self.queue_cancel.clear()
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
            "volume_boost": volume_boost,
            "trim_silence": trim_silence,
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
        self.queue_cancel.clear()
        if jid in self.cancel_events:
            self.cancel_events[jid].clear()
        app.after(0, refresh_queue_tab)
        self.pump()
        
    def cancel(self, jid):
        j = next((x for x in self.jobs if x["id"]==jid), None)
        if not j: return
        if j["status"] == "Downloading":
            j["status"] = "Cancelled"
            j["progress_text"] = "Stopped."
            j["progress_pct"] = 0.0
            if jid in self.cancel_events:
                self.cancel_events[jid].set()
        else:
            self.jobs.remove(j)
        app.after(0, refresh_queue_tab)
        app.after(50, self.pump)
        
    def clear_finished(self):
        self.jobs = [j for j in self.jobs if j["status"] not in ["Completed", "Error", "Cancelled"]]
        app.after(0, refresh_queue_tab)
        
    def get_max_concurrent(self):
        try: return int(global_max_downloads_var.get())
        except: return 1

    def pump(self):
        # Always purge dead threads to prevent worker desynchronization
        self.worker_threads = {jid: t for jid, t in self.worker_threads.items() if t.is_alive()}
        self.active_workers = len(self.worker_threads)

        max_c = self.get_max_concurrent()
        while self.active_workers < max_c:
            nxt = next((x for x in self.jobs if x["status"] == "Pending"), None)
            if not nxt: break
            
            jid = nxt["id"]
            nxt["status"] = "Downloading"
            nxt["progress_text"] = "Starting..."
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
            if cancel_event.is_set() or self.queue_cancel.is_set():
                raise ValueError("PROCESS_CANCELLED")
                
            def strip_ansi(text):
                if not isinstance(text, str): return text
                return re.sub(r'\x1b\[[0-9;]*m', '', text)
                
            filename = d.get('filename', '') or ''
            is_sub = any(filename.lower().endswith(ext) for ext in ['.srt', '.vtt', '.ass', '.lrc'])
            is_thumb = any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])

            if d['status'] == 'downloading':
                percent_str = strip_ansi(d.get('_percent_str', '0%')).strip()
                speed       = strip_ansi(d.get('_speed_str', 'N/A')).strip()
                eta         = strip_ansi(d.get('_eta_str', 'N/A')).strip()
                job['speed_bytes'] = d.get('speed') or 0
                if not is_sub and not is_thumb:
                    try:
                        job['progress_pct'] = float(percent_str.replace('%', '')) / 100.0
                    except:
                        pass
                    job['progress_text'] = f"{percent_str}  |  {speed}  |  ETA: {eta}"
                else:
                    job['progress_text'] = f"Fetching subtitles/thumbnails... ({speed})"
                
            elif d['status'] == 'finished':
                if not is_sub and not is_thumb:
                    job['progress_pct'] = 1.0
                    job['speed_bytes'] = 0
                    job['progress_text'] = "Muxing & finalizing..."

        opts_copy = dict(job["opts"])
        hooks = opts_copy.get("progress_hooks", [])
        opts_copy["progress_hooks"] = [h for h in hooks if h != progress_hook] + [_job_progress_hook]

        app.after(0, lambda: progress_bar.set(0))
        app.after(0, lambda: set_status(f"Downloading: {job['hint']}", COL_ACCENT, job['tab']))
        
        try:
            with yt_dlp.YoutubeDL(opts_copy) as ydl:
                for link in job["links"]:
                    if job_cancel and job_cancel.is_set(): raise ValueError("PROCESS_CANCELLED")
                    
                    t_hint = job["hint"] or link
                    expected_fpath = ""
                    pre_info = None
                    try:
                        pre_info = ydl.extract_info(link, download=False)
                        if pre_info:
                            t_hint, _ = extract_better_metadata(pre_info, t_hint)
                            expected_fpath = ydl.prepare_filename(pre_info)
                    except Exception:
                        pass

                    info = None
                    try:
                        info = ydl.extract_info(link, download=True)
                    except Exception as dl_err:
                        found_file = ""
                        if expected_fpath and os.path.isfile(expected_fpath) and os.path.getsize(expected_fpath) > 1024:
                            found_file = expected_fpath
                        else:
                            tgt_dir = job.get("target_dir") or (AUD_DIR if "Audio" in job.get("mode", "") else VID_DIR)
                            if os.path.isdir(tgt_dir):
                                candidates = [os.path.join(tgt_dir, f) for f in os.listdir(tgt_dir)
                                              if not f.endswith(('.part', '.ytdl', '.vtt', '.srt', '.aria2', '.temp'))]
                                if candidates:
                                    latest = max(candidates, key=os.path.getmtime)
                                    if time.time() - os.path.getmtime(latest) < 180 and os.path.getsize(latest) > 1024:
                                        found_file = latest
                        
                        if found_file:
                            fpath = found_file
                            info = pre_info or {"title": t_hint, "_filename": fpath}
                        else:
                            raise dl_err
                            
                    if not info and pre_info:
                        info = pre_info
                    if not info:
                        info = {"title": t_hint}
                        
                    t_hint = job["hint"] or link
                    title, _ = extract_better_metadata(info, t_hint)
                    sz = extract_size_from_info(info, "Audio" in job["mode"])
                    if sz: sz_str = format_size(sz)
                    elif _last_downloading_size != "Unknown": sz_str = _last_downloading_size
                    else: sz_str = job.get("size", "—")
                    
                    if job["hint"] == link or job["hint"] == "Link 1":
                        job["hint"] = title
                        
                    # Extract downloaded output file path on disk
                    fpath = info.get('_filename') or info.get('filename') or expected_fpath or ""
                    if not fpath and 'requested_downloads' in info and info['requested_downloads']:
                        fpath = info['requested_downloads'][0].get('filepath') or ""
                    if not fpath:
                        try: fpath = ydl.prepare_filename(info)
                        except Exception: pass
                    if not fpath or not os.path.isfile(fpath):
                        tgt_dir = job.get("target_dir") or (AUD_DIR if "Audio" in job.get("mode", "") else VID_DIR)
                        if os.path.isdir(tgt_dir):
                            candidates = [os.path.join(tgt_dir, f) for f in os.listdir(tgt_dir)
                                          if not f.endswith(('.part', '.ytdl', '.vtt', '.srt', '.aria2', '.temp'))]
                            if candidates:
                                latest = max(candidates, key=os.path.getmtime)
                                if time.time() - os.path.getmtime(latest) < 180 and os.path.getsize(latest) > 1024:
                                    fpath = latest
                            
                    # Common FFmpeg environment
                    ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe") if os.path.isdir(FFMPEG_DIR) and os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe")) else "ffmpeg"
                    creationflags = 0x08000000 if os.name == 'nt' else 0

                    # 🔊 Audio Volume Booster & Silence Trimmer (Video & Audio)
                    vol_boost = job.get("volume_boost", "Normal (0 dB)")
                    trim_silence = job.get("trim_silence", False)
                    if fpath and os.path.isfile(fpath) and (("+" in vol_boost) or trim_silence):
                        try:
                            af_filters = []
                            if "+" in vol_boost:
                                db_val = vol_boost.split()[0].replace("+", "")
                                af_filters.append(f"volume={db_val}")
                            if trim_silence:
                                af_filters.append("silenceremove=start_periods=1:start_duration=0.3:start_threshold=-45dB:stop_periods=1:stop_duration=0.3:stop_threshold=-45dB")
                            
                            if af_filters:
                                app.after(0, lambda: set_status(f"🔊 Enhancing audio: {job['hint']}", COL_ACCENT, job["tab"]))
                                job["progress_text"] = "Enhancing audio..."
                                app.after(0, refresh_queue_tab)
                                
                                filter_str = ",".join(af_filters)
                                fdir, fname = os.path.split(fpath)
                                fbase, fext = os.path.splitext(fname)
                                temp_aud = os.path.join(fdir, f"{fbase}_temp_enhanced{fext}")
                                
                                is_aud = "Audio" in job.get("mode", "")
                                if is_aud:
                                    aud_cmd = [ffmpeg_exe, "-y", "-i", fpath, "-af", filter_str, temp_aud]
                                else:
                                    aud_cmd = [ffmpeg_exe, "-y", "-i", fpath, "-c:v", "copy", "-af", filter_str, "-c:a", "aac", "-b:a", "192k", "-avoid_negative_ts", "make_zero", "-movflags", "+faststart", temp_aud]
                                
                                a_proc = subprocess.run(aud_cmd, capture_output=True, creationflags=creationflags)
                                if a_proc.returncode == 0 and os.path.isfile(temp_aud) and os.path.getsize(temp_aud) > 0:
                                    os.remove(fpath)
                                    os.replace(temp_aud, fpath)
                                    sz_str = format_size(os.path.getsize(fpath))
                        except Exception:
                            pass

                    # Clean up any leftover subtitle files if mode was Embed in Video
                    try:
                        sub_m = global_sub_mode_var.get() if 'global_sub_mode_var' in globals() else "Embed in Video"
                        if "Embed in Video" in sub_m and fpath and os.path.isfile(fpath):
                            fdir, fname = os.path.split(fpath)
                            fbase, _ = os.path.splitext(fname)
                            for sub_f in os.listdir(fdir):
                                if sub_f.startswith(fbase) and (sub_f.endswith('.srt') or sub_f.endswith('.vtt') or sub_f.endswith('.ass')):
                                    try:
                                        os.remove(os.path.join(fdir, sub_f))
                                    except Exception:
                                        pass
                    except Exception:
                        pass
                        
                    best_thumb = info.get("thumbnail") if isinstance(info, dict) else ""
                    save_history_entry(title, link, job["mode"], sz_str, job.get("quality", "—"), job.get("file_type", "—"), file_path=fpath, thumbnail=best_thumb)
            
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
            global_queue.add(jd["opts"], jd["links"], jd["folder_name"], jd["mode"], jd["hint"], jd["tab"], jd["size"], jd["quality"], jd["file_type"], start_paused=True)
        os.remove(QUEUE_FILE)
    except: pass



# ==========================================
#  DOWNLOAD RUNNER
# ==========================================
def run_download_thread(ydl_opts, links, folder_name,
                        mode="Video", title_hint="", tab=None, size="Unknown", quality="—", file_type="—", start_paused=False, volume_boost="Normal (0 dB)", trim_silence=False):
    if not links or not any(l.strip() for l in links):
        set_status("⚠  No links to download.", COL_WARN, tab)
        return
    global_queue.add(ydl_opts, [l.strip() for l in links if l.strip()], folder_name, mode, title_hint, tab, size, quality, file_type, start_paused, volume_boost, trim_silence)


# ==========================================
#  STANDARD ANALYZER
# ==========================================
def execute_standard_analysis(opts, links, info_box,
                               is_audio=False, audio_bitrate=None,
                               tab=None, thumb_label=None, stale_banner=None):
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
                        size_bytes = extract_size_from_info(info, is_audio, audio_bitrate)
                        total_bytes += size_bytes
                        successful  += 1
                        best_title, best_thumb = extract_better_metadata(info, f'Link {i+1}')
                        title       = best_title
                        title_str   = title
                        if i == 0:
                            thumb_url = best_thumb
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
                     thumb_label=None):
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
                    size_bytes = extract_size_from_info(entry, is_audio, audio_bitrate)
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
                             link, checkbox_state_list, is_video, tab=None, start_paused=False,
                             volume_boost="Normal (0 dB)", trim_silence=False):
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
                        job_hint, tab, size, q_var.get(), fmt_var.get() if fmt_var else "—", start_paused,
                        volume_boost=volume_boost, trim_silence=trim_silence)

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

_history_thumb_cache = {}

def get_history_thumbnail(item_dict, label_widget):
    """
    Fetch and display a compact 64×36 thumbnail for History items with:
    1. Memory caching
    2. Local file frame extraction via FFmpeg (for past & offline files on disk)
    3. URL download & caching (for online artwork)
    4. Clean fallback icon
    """
    if not PIL_AVAILABLE:
        icon = "🎵" if "Audio" in item_dict.get("mode", "") else "🎬"
        label_widget.configure(text=icon, font=("Segoe UI", 14), text_color=COL_MUTED, image=None)
        return

    thumb_url = item_dict.get("thumbnail", "")
    file_path = item_dict.get("file_path", "")
    title = item_dict.get("title", "")
    mode = item_dict.get("mode", "Video")
    cache_key = thumb_url or file_path or title or "item"

    # 1. In-memory cache hit
    if cache_key in _history_thumb_cache:
        img = _history_thumb_cache[cache_key]
        label_widget._img_ref = img
        label_widget.configure(image=img, text="")
        return

    icon = "🎵" if "Audio" in mode else "🎬"
    label_widget.configure(text=icon, font=("Segoe UI", 14), text_color=COL_MUTED, image=None)

    def _async_process():
        img = None
        safe_key = "".join(c for c in cache_key if c.isalnum())[:32] or "thumb"
        disk_cache_file = os.path.join(THUMBS_DIR, f"{safe_key}.jpg")

        if os.path.isfile(disk_cache_file):
            try:
                with Image.open(disk_cache_file) as orig:
                    img = orig.convert("RGB").copy()
            except Exception:
                img = None

        # Try downloading remote URL
        if img is None and thumb_url and str(thumb_url).startswith("http"):
            try:
                req = urllib.request.Request(
                    thumb_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    data = resp.read()
                with Image.open(io.BytesIO(data)) as orig:
                    raw_img = orig.convert("RGB").copy()
                w, h = raw_img.size
                target = (w, int(w * 9 / 16))
                if h > target[1]:
                    top = (h - target[1]) // 2
                    raw_img = raw_img.crop((0, top, w, top + target[1]))
                img = raw_img.resize((64, 36), Image.LANCZOS)
                try:
                    img.save(disk_cache_file, format="JPEG", quality=85)
                except Exception:
                    pass
            except Exception:
                img = None

        # If still no image, try extracting frame from local video file on disk
        if img is None:
            actual_file = file_path if (file_path and os.path.isfile(file_path)) else find_downloaded_file(title, mode)
            if actual_file and os.path.isfile(actual_file) and not "Audio" in mode:
                ffmpeg_exe = os.path.join(FFMPEG_DIR, "ffmpeg.exe") if os.path.isdir(FFMPEG_DIR) and os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe")) else "ffmpeg"
                try:
                    creationflags = 0x08000000 if os.name == 'nt' else 0
                    cmd = [
                        ffmpeg_exe, "-y",
                        "-ss", "0.5",
                        "-i", actual_file,
                        "-vframes", "1",
                        "-vf", "scale=64:36:force_original_aspect_ratio=increase,crop=64:36",
                        "-q:v", "2",
                        disk_cache_file
                    ]
                    proc = subprocess.run(cmd, capture_output=True, creationflags=creationflags)
                    if proc.returncode == 0 and os.path.isfile(disk_cache_file):
                        with Image.open(disk_cache_file) as orig:
                            img = orig.convert("RGB").copy()
                except Exception:
                    img = None

        if img is not None:
            if img.size != (64, 36):
                img = img.resize((64, 36), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(64, 36))
            _history_thumb_cache[cache_key] = ctk_img
            
            def _apply():
                try:
                    if label_widget.winfo_exists():
                        label_widget._img_ref = ctk_img
                        label_widget.configure(image=ctk_img, text="")
                except Exception:
                    pass
            try:
                app.after(0, _apply)
            except Exception:
                pass

    threading.Thread(target=_async_process, daemon=True).start()

hist_search_var = None
hist_filter_var = None

def refresh_history_tab():
    if history_box_ref is None:
        return
    for widget in history_box_ref.winfo_children():
        widget.destroy()
        
    history = load_history()
    if not history:
        ctk.CTkLabel(history_box_ref, text="No downloads recorded yet.", text_color=COL_MUTED).pack(pady=20)
        return
        
    s_term = hist_search_var.get().strip().lower() if hist_search_var else ""
    s_filter = hist_filter_var.get() if hist_filter_var else "All"
    
    start_idx = max(0, len(history) - 200)
    display_history = history[start_idx:]
    
    filtered_items = []
    for i, h in enumerate(display_history):
        real_idx = start_idx + i
        if s_filter == "Video" and not ("Video" in h.get("mode", "")):
            continue
        if s_filter == "Audio" and not ("Audio" in h.get("mode", "")):
            continue
        if s_term:
            combined = f"{h.get('title','')} {h.get('url','')} {h.get('mode','')} {h.get('quality','')} {h.get('file_type','')} {h.get('size','')}".lower()
            if s_term not in combined:
                continue
        filtered_items.append((real_idx, h))
        
    if not filtered_items:
        ctk.CTkLabel(history_box_ref, text="No downloads matching your search.", text_color=COL_MUTED).pack(pady=20)
        return
        
    for real_idx, h in filtered_items:
        frame = ctk.CTkFrame(history_box_ref, fg_color=COL_PANEL, corner_radius=8)
        frame.pack(fill="x", pady=3, padx=6)
        
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=5)
        
        # 1. Thumbnail preview
        thumb_box = ctk.CTkFrame(row, fg_color=COL_DARK, width=68, height=40, corner_radius=6)
        thumb_box.pack(side="left", padx=(2, 10))
        thumb_box.pack_propagate(False)
        thumb_lbl = ctk.CTkLabel(thumb_box, text="🎬", font=("Segoe UI", 14), text_color=COL_MUTED)
        thumb_lbl.pack(expand=True)
        get_history_thumbnail(h, thumb_lbl)
        
        # 2. Date & Mode
        left = ctk.CTkFrame(row, fg_color="transparent", width=95, height=40)
        left.pack(side="left")
        left.pack_propagate(False)
        ctk.CTkLabel(left, text=h.get('time', '—')[:10], font=("Segoe UI", 10), text_color=COL_MUTED).pack(anchor="w")
        ctk.CTkLabel(left, text=h.get('mode', '—').replace("-", " "), font=("Segoe UI", 11, "bold"), text_color=COL_ACCENT).pack(anchor="w")
        
        # 3. Center (Title & Specs)
        center = ctk.CTkFrame(row, fg_color="transparent")
        center.pack(side="left", fill="x", expand=True, padx=8)
        title = h.get('title', '—')
        if len(title) > 60: title = title[:58] + "..."
        ctk.CTkLabel(center, text=title, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
        
        info_str = f"{h.get('quality', '—')}  |  {h.get('file_type', '—')}"
        ctk.CTkLabel(center, text=info_str, font=("Consolas", 10), text_color=COL_MUTED, anchor="w").pack(fill="x", pady=(2, 0))
        
        # 4. Right side actions
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
            
        ctk.CTkButton(right, text="▶ Play", width=55, height=28, font=("Segoe UI", 11, "bold"), fg_color="#0F766E", hover_color="#115E59", text_color="#FFFFFF", command=make_play_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="📁 Folder", width=60, height=28, font=("Segoe UI", 11), fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT, command=make_folder_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="Link", width=42, height=28, font=("Segoe UI", 11), fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT, command=make_open_fn()).pack(side="left", padx=(0, 4))
        ctk.CTkButton(right, text="✖", width=28, height=28, font=("Segoe UI", 11), fg_color="#7F1D1D", hover_color="#450A0A", text_color="#FFFFFF", command=make_del_fn()).pack(side="left")

# ==========================================
#  UI COMPONENT BUILDERS
# ==========================================
def make_section_label(parent, text):
    lbl = ctk.CTkLabel(parent, text=text, font=("Segoe UI", 13, "bold"),
                       text_color=COL_MUTED)
    lbl.pack(anchor="w", padx=22, pady=(14, 2))
    reg_widget(lbl, "muted_labels")
    return lbl

def make_divider(parent):
    f = ctk.CTkFrame(parent, height=1, fg_color=COL_CHECK)
    f.pack(fill="x", padx=20, pady=4)
    reg_widget(f, "dividers")
    return f

def make_info_box(parent, height=55):
    box = ctk.CTkTextbox(parent, height=height, state="disabled",
                         text_color=COL_ACCENT, fg_color=COL_DARK,
                         font=MONO_FONT, wrap="none")
    box.pack(fill="x", padx=20, pady=4)
    reg_widget(box, "info_textboxes")
    return box

def make_check_btn(parent, text, cmd):
    b = ctk.CTkButton(parent, text=text, font=BTN_SUB,
                      fg_color=COL_CHECK, hover_color=COL_CHECKH,
                      text_color=COL_TEXT,
                      height=34, command=cmd)
    b.pack(fill="x", padx=40, pady=(8, 2))
    MANAGED_BUTTONS.append(b)
    reg_widget(b, "check_btns")
    return b

def make_dl_btn_group(parent, text, dl_cmd, queue_cmd):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", padx=40, pady=(6, 10))
    b1 = ctk.CTkButton(frame, text=text, font=BTN_MAIN,
                      fg_color=COL_DL, hover_color=COL_DLH,
                      height=48, command=dl_cmd)
    b1.pack(side="left", fill="x", expand=True, padx=(0, 5))
    MANAGED_BUTTONS.append(b1)
    reg_widget(b1, "dl_btns")
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
    reg_widget(b1, "dl_btns")
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
                         font=ENTRY_FONT, height=38, text_color=COL_TEXT)
    entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
    reg_widget(entry, "entries")
    cp_btn = ctk.CTkButton(
        frame, text="📋", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
        command=lambda: paste_from_clipboard(entry)
    )
    cp_btn.pack(side="right")
    reg_widget(cp_btn, "check_btns")
    return entry

def make_textbox_row(parent):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="both", expand=True, padx=20, pady=(2, 4))
    textbox = ctk.CTkTextbox(frame, font=("Consolas", 12), fg_color=COL_DARK,
                              text_color=COL_TEXT, height=130)
    textbox.pack(side="left", fill="both", expand=True, padx=(0, 6))
    reg_widget(textbox, "textboxes")
    side = ctk.CTkFrame(frame, fg_color="transparent", width=38)
    side.pack(side="right", fill="y")
    side.pack_propagate(False)
    btn_p = ctk.CTkButton(
        side, text="📋", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
        command=lambda: paste_to_textbox(textbox)
    )
    btn_p.pack(pady=(0, 4))
    reg_widget(btn_p, "check_btns")
    btn_x = ctk.CTkButton(
        side, text="✕", width=38, height=38, font=("Segoe UI", 14, "bold"),
        fg_color="#7F1D1D", hover_color="#450A0A", text_color="#FFFFFF",
        command=lambda: textbox.delete("1.0", "end")
    )
    btn_x.pack(pady=(4, 4))
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
    btn_o = ctk.CTkButton(
        side, text="📂", width=38, height=38, font=("Segoe UI", 16),
        fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
        command=_import_urls
    )
    btn_o.pack(pady=(4, 4))
    reg_widget(btn_o, "check_btns")

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
    br_btn = ctk.CTkButton(frame, text="Browse", width=75, font=BTN_SUB,
                  fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
                  command=browse)
    br_btn.pack(side="right", padx=(5, 0))
    reg_widget(br_btn, "check_btns")
    return path_var

def create_vid_options(parent):
    frame = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=8)
    frame.pack(fill="x", padx=20, pady=6)
    reg_widget(frame, "panels")

    # ── Preset Pill Bar ──
    p_row = ctk.CTkFrame(frame, fg_color="transparent")
    p_row.pack(fill="x", padx=12, pady=(6, 2))
    p_lbl = ctk.CTkLabel(p_row, text="Presets:", font=("Segoe UI", 10, "bold"), text_color=COL_MUTED)
    p_lbl.pack(side="left", padx=(0, 6))
    reg_widget(p_lbl, "muted_labels")

    q_var = ctk.StringVar(value="Best Available")
    fmt_var = ctk.StringVar(value="Default")
    s_var = ctk.StringVar(value="None")
    vol_boost_var = ctk.StringVar(value="Normal (0 dB)")
    silence_trim_var = ctk.BooleanVar(value=False)

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
        pb = ctk.CTkButton(
            p_row, text=label, width=88, height=22, font=("Segoe UI", 10, "bold"),
            fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
            command=lambda q=q_target, f=f_target: _set_vid_preset(q, f)
        )
        pb.pack(side="left", padx=2)
        reg_widget(pb, "check_btns")

    # Row 1: Quality | Format | Subtitles
    row1 = ctk.CTkFrame(frame, fg_color="transparent")
    row1.pack(fill="x", padx=12, pady=(3, 2))

    ctk.CTkLabel(row1, text="Quality:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    ctk.CTkOptionMenu(row1, variable=q_var, width=125,
                      values=list(VIDEO_QUALITY_MAP.keys())).pack(side="left", padx=(0, 10))

    ctk.CTkLabel(row1, text="Format:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    fmt_menu = ctk.CTkOptionMenu(row1, variable=fmt_var, width=75,
                                 values=["Default", "mp4", "mkv"])
    fmt_menu.pack(side="left", padx=(0, 10))

    ctk.CTkLabel(row1, text="Subtitles:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    s_menu = ctk.CTkOptionMenu(
        row1, variable=s_var, width=155,
        values=["None"] + list(SUBTITLE_LANG_MAP.keys()))
    s_menu.pack(side="left")

    # Row 2: Volume Boost | Silence Trimmer
    row2 = ctk.CTkFrame(frame, fg_color="transparent")
    row2.pack(fill="x", padx=12, pady=(2, 6))

    ctk.CTkLabel(row2, text="🔊 Boost:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    ctk.CTkOptionMenu(
        row2, variable=vol_boost_var, width=120,
        values=["Normal (0 dB)", "+3 dB (Gentle)", "+6 dB (Medium)", "+9 dB (Strong)", "+12 dB (Max)"]
    ).pack(side="left", padx=(0, 10))

    ctk.CTkCheckBox(row2, text="✂ Trim Silence", variable=silence_trim_var, font=("Segoe UI", 11)).pack(side="left")

    return q_var, s_var, fmt_var, vol_boost_var, silence_trim_var

def create_aud_options(parent):
    frame = ctk.CTkFrame(parent, fg_color=COL_PANEL, corner_radius=8)
    frame.pack(fill="x", padx=20, pady=6)
    reg_widget(frame, "panels")

    # ── Preset Pill Bar ──
    p_row = ctk.CTkFrame(frame, fg_color="transparent")
    p_row.pack(fill="x", padx=12, pady=(6, 2))
    p_lbl = ctk.CTkLabel(p_row, text="Presets:", font=("Segoe UI", 10, "bold"), text_color=COL_MUTED)
    p_lbl.pack(side="left", padx=(0, 6))
    reg_widget(p_lbl, "muted_labels")

    q_var = ctk.StringVar(value="Best — Highest bitrate")
    fmt_var = ctk.StringVar(value="mp3")
    vol_boost_var = ctk.StringVar(value="Normal (0 dB)")
    silence_trim_var = ctk.BooleanVar(value=False)

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
        pb = ctk.CTkButton(
            p_row, text=label, width=88, height=22, font=("Segoe UI", 10, "bold"),
            fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT,
            command=lambda q=q_target, f=f_target: _set_aud_preset(q, f)
        )
        pb.pack(side="left", padx=2)
        reg_widget(pb, "check_btns")

    # Row 1: Quality | Format
    row1 = ctk.CTkFrame(frame, fg_color="transparent")
    row1.pack(fill="x", padx=12, pady=(3, 2))

    ctk.CTkLabel(row1, text="Quality:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    ctk.CTkOptionMenu(row1, variable=q_var, width=175,
                      values=list(AUDIO_BITRATE_MAP.keys())).pack(side="left", padx=(0, 10))

    ctk.CTkLabel(row1, text="Format:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    ctk.CTkOptionMenu(row1, variable=fmt_var, width=75,
                      values=["mp3", "flac", "wav", "m4a"]).pack(side="left", padx=(0, 10))

    # Row 2: Volume Boost | Silence Trimmer
    row2 = ctk.CTkFrame(frame, fg_color="transparent")
    row2.pack(fill="x", padx=12, pady=(2, 6))

    ctk.CTkLabel(row2, text="🔊 Boost:", font=LABEL_FONT).pack(side="left", padx=(0, 4))
    ctk.CTkOptionMenu(
        row2, variable=vol_boost_var, width=120,
        values=["Normal (0 dB)", "+3 dB (Gentle)", "+6 dB (Medium)", "+9 dB (Strong)", "+12 dB (Max)"]
    ).pack(side="left", padx=(0, 10))

    ctk.CTkCheckBox(row2, text="✂ Trim Silence", variable=silence_trim_var, font=("Segoe UI", 11)).pack(side="left")

    return q_var, fmt_var, vol_boost_var, silence_trim_var

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
tabview._segmented_button.configure(
    font=("Segoe UI", 12, "bold"),
    text_color=COL_TEXT,
    unselected_color=COL_PANEL,
    unselected_hover_color=COL_CHECK,
    selected_color=COL_DL,
    selected_hover_color=COL_DLH
)
for tab in TAB_NAMES:
    tabview.add(tab)

# ==========================================
#  ACTION WRAPPERS
# ==========================================
def act_svid_check():
    link = vid_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Video"); return
    execute_standard_analysis(
        get_video_opts(vid_q_var, vid_s_var, vid_fmt_var, vid_path_var.get(), True),
        [link], vid_info_box, is_audio=False, tab="Single Video",
        thumb_label=vid_thumb_label, stale_banner=vid_stale_banner)

def act_svid_dl(start_paused=False):
    link = vid_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Video"); return
    title, size = get_info_details(vid_info_box, link)
    run_download_thread(
        get_video_opts(vid_q_var, vid_s_var, vid_fmt_var, vid_path_var.get()),
        [link], vid_path_var.get(), "Single-Video", title, "Single Video",
        size, vid_q_var.get(), vid_fmt_var.get(), start_paused,
        volume_boost=vid_vol_var.get(), trim_silence=vid_trim_var.get())

def act_saud_check():
    link = aud_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Audio"); return
    execute_standard_analysis(
        get_audio_opts(aud_q_var, aud_fmt_var, aud_path_var.get(), True),
        [link], aud_info_box, is_audio=True,
        audio_bitrate=get_audio_bitrate(aud_q_var), tab="Single Audio",
        thumb_label=aud_thumb_label, stale_banner=aud_stale_banner)

def act_saud_dl(start_paused=False):
    link = aud_entry.get().strip()
    if not link:
        set_status("⚠  Paste a link first.", COL_WARN, "Single Audio"); return
    title, size = get_info_details(aud_info_box, link)
    run_download_thread(
        get_audio_opts(aud_q_var, aud_fmt_var, aud_path_var.get()),
        [link], aud_path_var.get(), "Single-Audio", title, "Single Audio",
        size, aud_q_var.get(), aud_fmt_var.get(), start_paused,
        volume_boost=aud_vol_var.get(), trim_silence=aud_trim_var.get())

def act_bvid_check():
    links = [l for l in bvid_text.get("1.0", "end").splitlines() if l.strip()]
    execute_standard_analysis(
        get_video_opts(bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_path_var.get(), True),
        links, bvid_info_box, is_audio=False, tab="Batch Video",
        thumb_label=bvid_thumb_label, stale_banner=bvid_stale_banner)

def act_bvid_dl(start_paused=False):
    links = [l for l in bvid_text.get("1.0", "end").splitlines() if l.strip()]
    if not links:
        set_status("⚠  No links in the box.", COL_WARN, "Batch Video"); return
    title, size = get_info_details(bvid_info_box, "Batch Video")
    run_download_thread(
        get_video_opts(bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_path_var.get()),
        links, bvid_path_var.get(), "Batch-Video", title, "Batch Video",
        size, bvid_q_var.get(), bvid_fmt_var.get(), start_paused,
        volume_boost=bvid_vol_var.get(), trim_silence=bvid_trim_var.get())

def act_baud_check():
    links = [l for l in baud_text.get("1.0", "end").splitlines() if l.strip()]
    execute_standard_analysis(
        get_audio_opts(baud_q_var, baud_fmt_var, baud_path_var.get(), True),
        links, baud_info_box, is_audio=True,
        audio_bitrate=get_audio_bitrate(baud_q_var), tab="Batch Audio",
        thumb_label=baud_thumb_label, stale_banner=baud_stale_banner)

def act_baud_dl(start_paused=False):
    links = [l for l in baud_text.get("1.0", "end").splitlines() if l.strip()]
    if not links:
        set_status("⚠  No links in the box.", COL_WARN, "Batch Audio"); return
    title, size = get_info_details(baud_info_box, "Batch Audio")
    run_download_thread(
        get_audio_opts(baud_q_var, baud_fmt_var, baud_path_var.get()),
        links, baud_path_var.get(), "Batch-Audio", title, "Batch Audio",
        size, baud_q_var.get(), baud_fmt_var.get(), start_paused,
        volume_boost=baud_vol_var.get(), trim_silence=baud_trim_var.get())

def act_pvid_check():
    analyze_playlist(
        get_video_opts(pvid_q_var, pvid_s_var, pvid_fmt_var, pvid_path_var.get(), True),
        pvid_entry.get().strip(), pvid_scroll, pvid_checkboxes,
        pvid_dynamic_lbl, pvid_stale_banner, is_audio=False, tab="Playlist Video",
        thumb_label=pvid_thumb_label)

def act_pvid_dl(start_paused=False):
    start_playlist_download(pvid_q_var, pvid_s_var, pvid_fmt_var,
                             pvid_path_var.get(), pvid_entry.get().strip(),
                             pvid_checkboxes, True, "Playlist Video", start_paused,
                             volume_boost=pvid_vol_var.get(), trim_silence=pvid_trim_var.get())

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
                             paud_checkboxes, False, "Playlist Audio", start_paused,
                             volume_boost=paud_vol_var.get(), trim_silence=paud_trim_var.get())

# ==========================================
#  TAB 1 — SINGLE VIDEO
# ==========================================
t1 = tabview.tab("Single Video")
t1_scroll_main = ctk.CTkScrollableFrame(t1, fg_color="transparent")
t1_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t1_top = ctk.CTkFrame(t1_scroll_main, fg_color="transparent")
t1_top.pack(fill="x", padx=20, pady=(8, 0))
t1_left = ctk.CTkFrame(t1_top, fg_color="transparent")
t1_left.pack(side="left", fill="both", expand=True)
make_section_label(t1_left, "Video link")
vid_entry = make_entry_row(t1_left, "Paste YouTube / any site URL here…")
bind_url_hint(vid_entry, "Single Video", "Playlist Video")
make_section_label(t1_left, "Options")
vid_q_var, vid_s_var, vid_fmt_var, vid_vol_var, vid_trim_var = create_vid_options(t1_left)
vid_path_var   = create_path_selector(t1_left, VID_DIR)
vid_thumb_label = make_thumb_panel(t1_top)

make_divider(t1_scroll_main)
btn_check_vid  = make_check_btn(t1_scroll_main, "Step 1 — Check size & preview", act_svid_check)
vid_stale_banner = make_stale_banner(t1_scroll_main)
vid_info_box   = make_info_box(t1_scroll_main, height=65)
btn_dl_vid, btn_q_vid = make_dl_btn_group(t1_scroll_main, "⬇  Download Video", act_svid_dl, lambda: act_svid_dl(start_paused=True))
bind_keyboard_shortcuts(vid_entry, act_svid_dl)
attach_auto_check([vid_q_var, vid_s_var, vid_fmt_var, vid_vol_var], vid_entry, act_svid_check)
bind_url_change_clear(vid_entry, vid_info_box, vid_stale_banner)

# ==========================================
#  TAB 2 — SINGLE AUDIO
# ==========================================
t2 = tabview.tab("Single Audio")
t2_scroll_main = ctk.CTkScrollableFrame(t2, fg_color="transparent")
t2_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t2_top = ctk.CTkFrame(t2_scroll_main, fg_color="transparent")
t2_top.pack(fill="x", padx=20, pady=(8, 0))
t2_left = ctk.CTkFrame(t2_top, fg_color="transparent")
t2_left.pack(side="left", fill="both", expand=True)
make_section_label(t2_left, "Audio link")
aud_entry = make_entry_row(t2_left, "Paste YouTube / any site URL here…")
bind_url_hint(aud_entry, "Single Audio", "Playlist Audio")
make_section_label(t2_left, "Options")
aud_q_var, aud_fmt_var, aud_vol_var, aud_trim_var = create_aud_options(t2_left)
aud_path_var   = create_path_selector(t2_left, AUD_DIR)
aud_thumb_label = make_thumb_panel(t2_top, "Thumbnail\nappears here")

make_divider(t2_scroll_main)
btn_check_aud  = make_check_btn(t2_scroll_main, "Step 1 — Check size & preview", act_saud_check)
aud_stale_banner = make_stale_banner(t2_scroll_main)
aud_info_box   = make_info_box(t2_scroll_main, height=65)
btn_dl_aud, btn_q_aud = make_dl_btn_group(t2_scroll_main, "⬇  Download Audio", act_saud_dl, lambda: act_saud_dl(start_paused=True))
bind_keyboard_shortcuts(aud_entry, act_saud_dl)
attach_auto_check([aud_q_var, aud_fmt_var, aud_vol_var], aud_entry, act_saud_check)
bind_url_change_clear(aud_entry, aud_info_box, aud_stale_banner)

# ==========================================
#  TAB 3 — BATCH VIDEO
# ==========================================
t3 = tabview.tab("Batch Video")
t3_scroll_main = ctk.CTkScrollableFrame(t3, fg_color="transparent")
t3_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t3_top = ctk.CTkFrame(t3_scroll_main, fg_color="transparent")
t3_top.pack(fill="x", padx=20, pady=(8, 0))
t3_left = ctk.CTkFrame(t3_top, fg_color="transparent")
t3_left.pack(side="left", fill="both", expand=True)
make_section_label(t3_left, "Video links  (one per line)")
bvid_text = make_textbox_row(t3_left)
make_section_label(t3_left, "Options")
bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_vol_var, bvid_trim_var = create_vid_options(t3_left)
bvid_path_var   = create_path_selector(t3_left, VID_DIR)
bvid_thumb_label = make_thumb_panel(t3_top, "First link\npreview")

make_divider(t3_scroll_main)
btn_check_bvid  = make_check_btn(t3_scroll_main, "Step 1 — Analyze links", act_bvid_check)
bvid_stale_banner = make_stale_banner(t3_scroll_main)
bvid_info_box   = make_info_box(t3_scroll_main, height=75)
btn_dl_bvid, btn_q_bvid = make_dl_btn_group(t3_scroll_main, "⬇  Download Batch", act_bvid_dl, lambda: act_bvid_dl(start_paused=True))

attach_auto_check([bvid_q_var, bvid_s_var, bvid_fmt_var, bvid_vol_var], bvid_text, act_bvid_check)
bind_text_change_clear(bvid_text, bvid_info_box, bvid_stale_banner)

# ==========================================
#  TAB 4 — BATCH AUDIO
# ==========================================
t4 = tabview.tab("Batch Audio")
t4_scroll_main = ctk.CTkScrollableFrame(t4, fg_color="transparent")
t4_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t4_top = ctk.CTkFrame(t4_scroll_main, fg_color="transparent")
t4_top.pack(fill="x", padx=20, pady=(8, 0))
t4_left = ctk.CTkFrame(t4_top, fg_color="transparent")
t4_left.pack(side="left", fill="both", expand=True)
make_section_label(t4_left, "Audio links  (one per line)")
baud_text = make_textbox_row(t4_left)
make_section_label(t4_left, "Options")
baud_q_var, baud_fmt_var, baud_vol_var, baud_trim_var = create_aud_options(t4_left)
baud_path_var   = create_path_selector(t4_left, AUD_DIR)
baud_thumb_label = make_thumb_panel(t4_top, "First link\npreview")

make_divider(t4_scroll_main)
btn_check_baud    = make_check_btn(t4_scroll_main, "Step 1 — Analyze links", act_baud_check)
baud_stale_banner = make_stale_banner(t4_scroll_main)
baud_info_box     = make_info_box(t4_scroll_main, height=75)
btn_dl_baud, btn_q_baud = make_dl_btn_group(t4_scroll_main, "⬇  Download Batch", act_baud_dl, lambda: act_baud_dl(start_paused=True))

attach_auto_check([baud_q_var, baud_fmt_var, baud_vol_var], baud_text, act_baud_check)
bind_text_change_clear(baud_text, baud_info_box, baud_stale_banner)

# ==========================================
#  TAB 5 — PLAYLIST VIDEO
# ==========================================
t5 = tabview.tab("Playlist Video")
t5_scroll_main = ctk.CTkScrollableFrame(t5, fg_color="transparent")
t5_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t5_top = ctk.CTkFrame(t5_scroll_main, fg_color="transparent")
t5_top.pack(fill="x", padx=20, pady=(8, 0))
t5_left = ctk.CTkFrame(t5_top, fg_color="transparent")
t5_left.pack(side="left", fill="both", expand=True)
make_section_label(t5_left, "Playlist link")
pvid_entry = make_entry_row(t5_left, "Paste YouTube playlist URL here…")
bind_url_hint(pvid_entry, "Playlist Video", "Single Video")
make_section_label(t5_left, "Options")
pvid_q_var, pvid_s_var, pvid_fmt_var, pvid_vol_var, pvid_trim_var = create_vid_options(t5_left)
pvid_path_var   = create_path_selector(t5_left, VID_DIR)
pvid_thumb_label = make_thumb_panel(t5_top, "Playlist\npreview")

make_divider(t5_scroll_main)
pvid_stale_banner = make_stale_banner(t5_scroll_main)
btn_check_pvid = make_check_btn(t5_scroll_main, "Step 1 — Fetch playlist items", act_pvid_check)

# ── Unified Actions Ribbon (Select All, Deselect All, Range Selector) ──
pvid_tools = ctk.CTkFrame(t5_scroll_main, fg_color=COL_PANEL, corner_radius=8)
pvid_tools.pack(fill="x", padx=20, pady=(6, 4))
pvid_tools_row = ctk.CTkFrame(pvid_tools, fg_color="transparent")
pvid_tools_row.pack(fill="x", padx=10, pady=6)

for txt, st in [("Select all", 1), ("Deselect all", 0)]:
    col = COL_ACCENT if st == 1 else COL_CHECK
    b   = ctk.CTkButton(pvid_tools_row, text=txt, width=95, height=28, font=BTN_SUB,
                        fg_color=col,
                        command=lambda s=st: toggle_all_checkboxes(
                            pvid_checkboxes, s, pvid_dynamic_lbl))
    b.pack(side="left", padx=(0, 6))
    MANAGED_BUTTONS.append(b)

ctk.CTkLabel(pvid_tools_row, text="Range:", font=LABEL_FONT).pack(side="left", padx=(10, 4))
pvid_range_entry = ctk.CTkEntry(pvid_tools_row, width=95, height=28, font=ENTRY_FONT, placeholder_text="e.g. 1-10")
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

ctk.CTkButton(pvid_tools_row, text="Apply", width=65, height=28, font=BTN_SUB,
              fg_color=COL_CHECK, hover_color=COL_CHECKH,
              command=_apply_pvid_range).pack(side="left")

# ── Spacious Playlist Items Checklist ──
pvid_checkboxes = []
pvid_scroll = ctk.CTkScrollableFrame(t5_scroll_main, fg_color=COL_DARK, height=280)
pvid_scroll.pack(fill="both", expand=True, padx=20, pady=(4, 6))

pvid_summary = ctk.CTkFrame(t5_scroll_main, fg_color=COL_DARK, corner_radius=8)
pvid_summary.pack(fill="x", padx=20, pady=(4, 4))
pvid_dynamic_lbl = ctk.CTkLabel(pvid_summary,
    text="Selected: 0 / 0   |   Est. total size: —",
    text_color=COL_ACCENT, font=("Segoe UI", 14, "bold"), anchor="center")
pvid_dynamic_lbl.pack(fill="x", padx=16, pady=8)

btn_dl_pvid, btn_q_pvid = make_playlist_dl_btn_group(t5_scroll_main, "⬇  Download Selected", act_pvid_dl, lambda: act_pvid_dl(start_paused=True))
pvid_info_box = make_info_box(t5_scroll_main, height=1)
attach_auto_check([pvid_q_var, pvid_s_var, pvid_fmt_var, pvid_vol_var], pvid_entry, act_pvid_check)
bind_url_change_clear(pvid_entry, pvid_info_box, pvid_stale_banner)
pvid_info_box.pack_forget()

# ==========================================
#  TAB 6 — PLAYLIST AUDIO
# ==========================================
t6 = tabview.tab("Playlist Audio")
t6_scroll_main = ctk.CTkScrollableFrame(t6, fg_color="transparent")
t6_scroll_main.pack(fill="both", expand=True, padx=0, pady=0)

t6_top = ctk.CTkFrame(t6_scroll_main, fg_color="transparent")
t6_top.pack(fill="x", padx=20, pady=(8, 0))
t6_left = ctk.CTkFrame(t6_top, fg_color="transparent")
t6_left.pack(side="left", fill="both", expand=True)
make_section_label(t6_left, "Playlist link")
paud_entry = make_entry_row(t6_left, "Paste YouTube playlist URL here…")
bind_url_hint(paud_entry, "Playlist Audio", "Single Audio")
make_section_label(t6_left, "Options")
paud_q_var, paud_fmt_var, paud_vol_var, paud_trim_var = create_aud_options(t6_left)
paud_path_var    = create_path_selector(t6_left, AUD_DIR)
paud_thumb_label  = make_thumb_panel(t6_top, "Playlist cover\nappears here")

make_divider(t6_scroll_main)
paud_stale_banner = make_stale_banner(t6_scroll_main)
btn_check_paud    = make_check_btn(t6_scroll_main, "Step 1 — Fetch checklist", act_paud_check)

# ── Unified Actions Ribbon (Select All, Deselect All, Range Selector) ──
paud_tools = ctk.CTkFrame(t6_scroll_main, fg_color=COL_PANEL, corner_radius=8)
paud_tools.pack(fill="x", padx=20, pady=(6, 4))
paud_tools_row = ctk.CTkFrame(paud_tools, fg_color="transparent")
paud_tools_row.pack(fill="x", padx=10, pady=6)

for txt, st in [("Select all", 1), ("Deselect all", 0)]:
    col = COL_ACCENT if st == 1 else COL_CHECK
    b   = ctk.CTkButton(paud_tools_row, text=txt, width=95, height=28, font=BTN_SUB,
                        fg_color=col,
                        command=lambda s=st: toggle_all_checkboxes(
                            paud_checkboxes, s, paud_dynamic_lbl))
    b.pack(side="left", padx=(0, 6))
    MANAGED_BUTTONS.append(b)

ctk.CTkLabel(paud_tools_row, text="Range:", font=LABEL_FONT).pack(side="left", padx=(10, 4))
paud_range_entry = ctk.CTkEntry(paud_tools_row, width=95, height=28, font=ENTRY_FONT, placeholder_text="e.g. 1-10")
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

ctk.CTkButton(paud_tools_row, text="Apply", width=65, height=28, font=BTN_SUB,
              fg_color=COL_CHECK, hover_color=COL_CHECKH,
              command=_apply_paud_range).pack(side="left")

# ── Spacious Playlist Items Checklist ──
paud_checkboxes = []
paud_scroll = ctk.CTkScrollableFrame(t6_scroll_main, fg_color=COL_DARK, height=280)
paud_scroll.pack(fill="both", expand=True, padx=20, pady=(4, 6))

paud_summary = ctk.CTkFrame(t6_scroll_main, fg_color=COL_DARK, corner_radius=8)
paud_summary.pack(fill="x", padx=20, pady=(4, 4))
paud_dynamic_lbl = ctk.CTkLabel(paud_summary,
    text="Selected: 0 / 0   |   Est. total size: —",
    text_color=COL_ACCENT, font=("Segoe UI", 14, "bold"), anchor="center")
paud_dynamic_lbl.pack(fill="x", padx=16, pady=8)

btn_dl_paud, btn_q_paud = make_playlist_dl_btn_group(t6_scroll_main, "⬇  Download Selected", act_paud_dl, lambda: act_paud_dl(start_paused=True))
paud_info_box = make_info_box(t6_scroll_main, height=1)
attach_auto_check([paud_q_var, paud_fmt_var, paud_vol_var], paud_entry, act_paud_check)
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

speed_canvas = ctk.CTkCanvas(net_frame, height=65, bg="#080C14", highlightthickness=0)
speed_canvas.pack(fill="x", padx=12, pady=(0, 8))
speed_canvas_ref = speed_canvas

queue_ctrl = ctk.CTkFrame(t_queue, fg_color="transparent")
queue_ctrl.pack(fill="x", padx=20, pady=(2, 2))

queue_search_var = ctk.StringVar(value="")
queue_filter_var = ctk.StringVar(value="All")

queue_search_entry = ctk.CTkEntry(queue_ctrl, placeholder_text="🔍 Filter queue...",
                                  textvariable=queue_search_var, width=200, font=("Segoe UI", 12))
queue_search_entry.pack(side="left", padx=(0, 6))
queue_search_var.trace_add("write", lambda *_: refresh_queue_tab())

def _set_queue_filter(st):
    queue_filter_var.set(st)
    refresh_queue_tab()

for st_label, st_val in [("All", "All"), ("Active", "Active"), ("Paused", "Paused"), ("Done", "Done"), ("Error", "Error")]:
    ctk.CTkButton(
        queue_ctrl, text=st_label, width=54, height=28, font=("Segoe UI", 10, "bold"),
        fg_color=COL_CHECK, hover_color=COL_CHECKH,
        command=lambda s=st_val: _set_queue_filter(s)
    ).pack(side="left", padx=2)

ctk.CTkButton(queue_ctrl, text="Clear Finished", width=110, height=28, font=BTN_SUB,
              command=global_queue.clear_finished).pack(side="right")
queue_box = ctk.CTkScrollableFrame(t_queue, fg_color=COL_DARK)
queue_box.pack(fill="both", expand=True, padx=20, pady=(4, 14))
queue_box_ref = queue_box
refresh_queue_tab()

# ==========================================
#  TAB 7 — HISTORY
# ==========================================
t7 = tabview.tab("History")
make_section_label(t7, "Download History")

hist_ctrl = ctk.CTkFrame(t7, fg_color="transparent")
hist_ctrl.pack(fill="x", padx=20, pady=(2, 6))

hist_search_var = ctk.StringVar(value="")
hist_filter_var = ctk.StringVar(value="All")

# Search entry with live trace
search_wrap = ctk.CTkFrame(hist_ctrl, fg_color="transparent")
search_wrap.pack(side="left", fill="x", expand=True, padx=(0, 8))

hist_search_entry = ctk.CTkEntry(
    search_wrap, placeholder_text="🔍 Search history by title, URL, quality...",
    textvariable=hist_search_var, font=("Segoe UI", 12), height=32
)
hist_search_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
hist_search_var.trace_add("write", lambda *_: refresh_history_tab())

def _clear_search():
    hist_search_var.set("")
    hist_search_entry.delete(0, "end")
    refresh_history_tab()

ctk.CTkButton(search_wrap, text="✕", width=32, height=32, font=("Segoe UI", 12, "bold"),
              fg_color=COL_CHECK, hover_color=COL_CHECKH, command=_clear_search).pack(side="left")

# Filter pills
def _set_hist_filter(cat):
    hist_filter_var.set(cat)
    refresh_history_tab()

filter_pills_frame = ctk.CTkFrame(hist_ctrl, fg_color="transparent")
filter_pills_frame.pack(side="left", padx=(0, 8))

for cat_label, cat_val in [("All", "All"), ("🎬 Video", "Video"), ("🎵 Audio", "Audio")]:
    ctk.CTkButton(
        filter_pills_frame, text=cat_label, width=68, height=32, font=("Segoe UI", 11, "bold"),
        fg_color=COL_CHECK, hover_color=COL_CHECKH,
        command=lambda c=cat_val: _set_hist_filter(c)
    ).pack(side="left", padx=2)

def clear_history():
    if messagebox.askyesno("Clear history", "Delete all download history?"):
        try:
            if os.path.exists(HISTORY_FILE):
                os.remove(HISTORY_FILE)
        except Exception:
            pass
        refresh_history_tab()

ctk.CTkButton(hist_ctrl, text="Refresh", width=75, height=32, font=BTN_SUB,
              command=refresh_history_tab).pack(side="right", padx=(4, 0))
ctk.CTkButton(hist_ctrl, text="Clear All", width=75, height=32, font=BTN_SUB,
              fg_color="#7F1D1D", hover_color="#450A0A",
              command=clear_history).pack(side="right")

history_box = ctk.CTkScrollableFrame(t7, fg_color=COL_DARK)
history_box.pack(fill="both", expand=True, padx=20, pady=(2, 14))
history_box_ref = history_box
refresh_history_tab()

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
reg_widget(about_frame, "panels")

# Display App Logo in About Card
_logo_png = os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd(), "icon.png")
if hasattr(sys, '_MEIPASS'):
    _meipass_png = os.path.join(sys._MEIPASS, "icon.png")
    if os.path.isfile(_meipass_png):
        _logo_png = _meipass_png
if PIL_AVAILABLE and os.path.isfile(_logo_png):
    try:
        with Image.open(_logo_png) as _lim:
            _app_logo_ctk = ctk.CTkImage(light_image=_lim.copy(), dark_image=_lim.copy(), size=(64, 64))
        _logo_img_lbl = ctk.CTkLabel(about_frame, image=_app_logo_ctk, text="")
        _logo_img_lbl.image = _app_logo_ctk
        _logo_img_lbl.pack(pady=(12, 0))
    except Exception:
        pass

_about_title = ctk.CTkLabel(about_frame,
    text=f"Hedra Downloader PRO {APP_VERSION}",
    font=("Segoe UI", 15, "bold"), text_color=COL_TEXT
)
_about_title.pack(pady=(4, 2))
reg_widget(_about_title, "text_labels")

_about_author = ctk.CTkLabel(about_frame,
    text=f"Made by  {APP_AUTHOR}",
    font=("Segoe UI", 12, "bold"), text_color=COL_ACCENT
)
_about_author.pack(pady=(0, 4))
reg_widget(_about_author, "accent_labels")

_about_desc = ctk.CTkLabel(about_frame,
    text="Powered by yt-dlp  •  FFmpeg  •  customtkinter",
    font=("Segoe UI", 11), text_color=COL_MUTED
)
_about_desc.pack(pady=(0, 4))
reg_widget(_about_desc, "muted_labels")

_about_path = ctk.CTkLabel(about_frame,
    text=f"Downloads → {BASE_DIR}",
    font=("Consolas", 10), text_color=COL_MUTED
)
_about_path.pack(pady=(0, 12))
reg_widget(_about_path, "muted_labels")

make_divider(t8_scroll)

# ── Appearance section ────────────────────────────────────
make_section_label(t8_scroll, "Appearance & Theme")
_pal_outer = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
_pal_outer.pack(fill="x", padx=20, pady=6)
reg_widget(_pal_outer, "panels")

_pal_row = ctk.CTkFrame(_pal_outer, fg_color="transparent")
_pal_row.pack(fill="x", padx=12, pady=10)

def apply_palette(name):
    """Save palette choice and apply live in-memory instantly."""
    global _ACTIVE_PALETTE
    _ACTIVE_PALETTE = name
    try:
        save_settings()
    except Exception:
        pass
    recolor_ui_live(name)

_PAL_PREVIEWS = {
    "Default":   ("#38BDF8", "#0B0F19", "Sky blue / Midnight Navy"),
    "Pure Dark": ("#A78BFA", "#000000", "Violet / OLED Pure Black"),
}

for _pname, (_pacc, _pbg, _pdesc) in _PAL_PREVIEWS.items():
    _card = ctk.CTkFrame(_pal_row, fg_color=_pbg, corner_radius=10,
                         border_width=2 if _pname == _ACTIVE_PALETTE else 0,
                         border_color=_pacc)
    _card.pack(side="left", padx=8, pady=6, ipadx=10, ipady=8, fill="x", expand=True)
    _pal_cards_dict[_pname] = _card
    
    ctk.CTkLabel(_card, text=_pname, font=("Segoe UI", 12, "bold"),
                 text_color="#FFFFFF").pack(padx=12, pady=(6, 2))
    ctk.CTkLabel(_card, text=_pdesc, font=("Segoe UI", 9),
                 text_color="#94A3B8", wraplength=180).pack(padx=12, pady=(0, 6))
    _dot = ctk.CTkFrame(_card, width=24, height=24, corner_radius=12, fg_color=_pacc)
    _dot.pack(pady=(0, 8))
    ctk.CTkButton(_card, text="Apply Theme", width=110, height=28, font=BTN_SUB,
                  fg_color=_pacc,
                  hover_color="#1E3A8A",
                  text_color="#FFFFFF",
                  command=lambda n=_pname: apply_palette(n)
                  ).pack(pady=(0, 6), padx=12)

_pal_hint = ctk.CTkLabel(_pal_outer, text="* Theme switches live instantly without restarting and is saved as your default.",
             font=("Segoe UI", 11, "italic"), text_color=COL_MUTED)
_pal_hint.pack(pady=(0, 10))
reg_widget(_pal_hint, "muted_labels")

make_divider(t8_scroll)
make_section_label(t8_scroll, "Supported Websites")
websites_frame = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
websites_frame.pack(fill="x", padx=20, pady=6)
reg_widget(websites_frame, "panels")

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
    # Logo label — starts as emoji globe, replaced with real brand icon
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
    # Load site logo
    _load_site_logo(_sdomain, _logo_lbl, _scolor)
ctk.CTkLabel(
    websites_frame,
    text="...and 1,000+ more sites supported via yt-dlp",
    font=("Segoe UI", 10), text_color=COL_MUTED
).pack(pady=(2, 10))

make_divider(t8_scroll)
make_section_label(t8_scroll, "Tab guide")
tab_guide_frame = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
tab_guide_frame.pack(fill="x", padx=20, pady=6)
reg_widget(tab_guide_frame, "panels")

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
    _tg_lbl = ctk.CTkLabel(row, text=f"{tab_name}:", font=("Segoe UI", 12, "bold"),
                 text_color=COL_MUTED, width=130, anchor="w")
    _tg_lbl.pack(side="left", padx=(0, 8))
    reg_widget(_tg_lbl, "muted_labels")
    _tg_desc = ctk.CTkLabel(row, text=desc, font=("Segoe UI", 11),
                 text_color=COL_MUTED, anchor="w", wraplength=540,
                 justify="left")
    _tg_desc.pack(side="left", fill="x", expand=True)
    reg_widget(_tg_desc, "muted_labels")

make_divider(t8_scroll)
make_section_label(t8_scroll, "Global download settings")
gset = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=8)
gset.pack(fill="x", padx=20, pady=6)
reg_widget(gset, "panels")

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

_btn_bcook = ctk.CTkButton(gr1b, text="Browse", width=65, font=BTN_SUB, fg_color=COL_CHECK, hover_color=COL_CHECKH, text_color=COL_TEXT, command=_browse_cookie_file)
_btn_bcook.pack(side="left", padx=(0, 4))
reg_widget(_btn_bcook, "check_btns")

ctk.CTkButton(gr1b, text="📋 Paste", width=65, font=BTN_SUB, fg_color="#0F766E", hover_color="#115E59", text_color="#FFFFFF", command=_paste_cookie_clipboard).pack(side="left", padx=(0, 4))
ctk.CTkButton(gr1b, text="✕", width=28, font=("Segoe UI", 12, "bold"), fg_color="#7F1D1D", hover_color="#450A0A", text_color="#FFFFFF", command=_clear_cookie_file).pack(side="left", padx=(0, 10))
_lbl_cook_hint = ctk.CTkLabel(gr1b, text="💡 Export via 'Get cookies.txt' extension to bypass Windows Chrome DPAPI lock", font=("Segoe UI", 10), text_color=COL_MUTED)
_lbl_cook_hint.pack(side="left")
reg_widget(_lbl_cook_hint, "muted_labels")

gr2 = ctk.CTkFrame(gset, fg_color="transparent")
gr2.pack(fill="x", padx=12, pady=(4, 4))
ctk.CTkLabel(gr2, text="Connections:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_concurrent_var = ctk.StringVar(value="4")
ctk.CTkOptionMenu(gr2, variable=global_concurrent_var, width=70,
                  values=[str(i) for i in range(1, 9)]).pack(side="left", padx=(0, 20))
_lbl_con_hint = ctk.CTkLabel(gr2, text="(parallel fragment downloads — higher = faster for DASH/HLS)",
             font=("Segoe UI", 10), text_color=COL_MUTED)
_lbl_con_hint.pack(side="left")
reg_widget(_lbl_con_hint, "muted_labels")

gr2b = ctk.CTkFrame(gset, fg_color="transparent")
gr2b.pack(fill="x", padx=12, pady=(0, 4))
ctk.CTkLabel(gr2b, text="Proxy:", font=LABEL_FONT).pack(side="left", padx=(0, 5))
global_proxy_entry = ctk.CTkEntry(gr2b, width=220, font=ENTRY_FONT,
                                   placeholder_text="e.g. socks5://127.0.0.1:1080")
global_proxy_entry.pack(side="left", padx=(0, 14))
_lbl_prox_hint = ctk.CTkLabel(gr2b, text="HTTP or SOCKS5 — leave blank for direct",
             font=("Segoe UI", 10), text_color=COL_MUTED)
_lbl_prox_hint.pack(side="left")
reg_widget(_lbl_prox_hint, "muted_labels")

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
reg_widget(adv_set, "panels")

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
make_section_label(t8_scroll, "Keyboard shortcuts & gestures")

sc_card = ctk.CTkFrame(t8_scroll, fg_color=COL_PANEL, corner_radius=10)
sc_card.pack(fill="x", padx=20, pady=(4, 10))

SHORTCUTS = [
    ("Ctrl + V", "Universal Paste", "Paste video/audio URL reliably on any keyboard layout (Arabic, French, etc.)", "📋"),
    ("Ctrl + S", "Instant Download", "Start immediate download from any single URL entry field", "⬇"),
    ("Escape", "Emergency Stop", "Abort and cancel all active downloads cleanly", "⏹"),
    ("Drag & Drop", "Direct Drop Import", "Drop .txt link lists or URLs directly onto the window", "🎯"),
    ("Enter", "Quick Check", "Analyze link size, duration, and thumbnail preview", "🔍"),
    ("🧹 Clean", "Batch Deduplicator", "Remove duplicates, normalize URLs, and clean blank lines", "🧹"),
]

for key_combo, title_text, desc_text, icon in SHORTCUTS:
    sc_row = ctk.CTkFrame(sc_card, fg_color="transparent")
    sc_row.pack(fill="x", padx=14, pady=5)
    
    k_badge = ctk.CTkFrame(sc_row, fg_color=COL_DARK, corner_radius=6, height=28)
    k_badge.pack(side="left", padx=(0, 12))
    k_badge.pack_propagate(False)
    ctk.CTkLabel(k_badge, text=f" {key_combo} ", font=("Consolas", 11, "bold"), text_color=COL_ACCENT).pack(padx=8, pady=3)
    
    ctk.CTkLabel(sc_row, text=f"{icon}  {title_text}", font=("Segoe UI", 11, "bold"), text_color=COL_TEXT).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(sc_row, text=f"—  {desc_text}", font=("Segoe UI", 11), text_color=COL_MUTED).pack(side="left", fill="x", expand=True, anchor="w")

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
