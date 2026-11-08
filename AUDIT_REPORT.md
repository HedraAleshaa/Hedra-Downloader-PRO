# Cold, Zero-Trust Architecture & Code Audit Report
**Target Repository:** `Hedra Downloader PRO (V19)`  
**Audit Conducted By:** Principal Software Architect & QA Lead  
**Audit Status:** Complete — All P0, P1, and P2 Items Implemented & Verified  
**Primary Artifact Under Audit:** `Hedra Downloader PRO.pyw`, entry points, configuration, and packaging specs.

---

## Executive Summary

A comprehensive, zero-trust audit of the codebase was conducted across four core categories:
1. Broken & Fragile Logic (Critical Bugs, Race Conditions, Concurrency)
2. Architectural & Performance Bottlenecks (UI Thread Freezes, Leaks, Redundant I/O)
3. Security & Dependency Risks (Command Injections, Frozen Executable Safety)
4. High-Value Feature & UX Improvements (Clip Trimming, Queue Actions, Auto-Retry)

All critical vulnerabilities (P0), architectural refactorings (P1), and high-value user experience features (P2) have been systematically resolved, tested, and validated.

---

## Prioritized Action Plan & Resolution Status

---

### [P0 - Critical / Broken] — STATUS: ALL RESOLVED & VERIFIED

#### 1. Command Injection in Toast Notification Dispatcher [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 625 - 638`
- **Resolution:** Removed Python f-string interpolation into the PowerShell scriptblock. Switched to parameter passing via `$args[0]` and `$args[1]` through `-args` flags (`powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -Command <static_script> <title> <message>`), eliminating all arbitrary code execution vectors.

---

#### 2. Command Injection via `shell=True` in File Explorer Revealer [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 587 - 589`
- **Resolution:** Replaced `subprocess.run(f'explorer /select,"{os.path.normpath(path)}"', shell=True)` with direct binary argument dispatch `subprocess.run(['explorer.exe', f'/select,{os.path.normpath(path)}'], shell=False)`.

---

#### 3. Unsynchronized Concurrent Access & Race Conditions in `JobQueue` [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1550 - 1650`
- **Resolution:** Integrated `self._lock = threading.RLock()` across all `JobQueue` methods (`add`, `pause`, `resume`, `cancel`, `clear_finished`, `pump`, and `_worker` cleanup). Introduced thread-safe snapshot method `get_jobs_snapshot()`, preventing concurrent mutation crashes (`RuntimeError: list changed size during iteration`) and desynchronized worker allocations. Upgraded job IDs to collision-proof `uuid.uuid4().hex`.

---

#### 4. Sequential Monolithic Batch Downloads Defeating Concurrency [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 3080 - 3130`
- **Resolution:** In `act_bvid_dl()` and `act_baud_dl()`, decoupled batch URL inputs so each link is registered as an independent discrete job in `JobQueue`. Enables true concurrent multi-threading up to `max_concurrent` (1–5 downloads simultaneously) and ensures individual link failures do not abort remaining batch items.

---

#### 5. Data Loss Vulnerability During Audio Enhancement & Silence Trimming [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1850 - 1885`
- **Resolution:** Eliminated premature `os.remove(fpath)`. Replaced with atomic `os.replace(temp_aud, fpath)` inside exception handling, guaranteeing that if file replacement fails due to a temporary lock, the original downloaded file remains safe and untouched while `temp_aud` is cleaned up.

---

#### 6. Wrong-File Subtitle Deletion Bug via Broad Prefix Matching [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1885 - 1900`
- **Resolution:** Changed broad prefix match `sub_f.startswith(fbase)` to exact delimited match `sub_f.startswith(fbase + ".") and sub_f.lower().endswith(('.srt', '.vtt', '.ass', '.lrc'))`, preventing `Episode 1` from accidentally deleting `Episode 10.srt`.

---

#### 7. Thread Storm & UI Lockup on Search Keystrokes (History & Queue) [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 2470 - 2500, 3460 - 3500`
- **Resolution:** 
  1. Added 250ms debouncers (`_on_queue_search_change`, `_on_hist_search_change`) canceling pending `app.after` calls to prevent widget teardown/rebuild storms on every keystroke.
  2. Bounded background history thumbnail fetching to a dedicated `ThreadPoolExecutor(max_workers=3, thread_name_prefix="ThumbWorker")`, replacing unbounded thread spawning.

---

### [P1 - Architecture & Refactoring] — STATUS: ALL RESOLVED & VERIFIED

#### 8. UI Text Scraping for Core Business Parameters [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 887 - 905, 2120 - 2130`
- **Resolution:** Decoupled business logic from visual Tkinter widgets. Extracted metadata is stored directly in an in-memory dictionary `_last_analyzed_meta[info_box] = {'title': ..., 'size': ...}` upon analysis completion. `get_info_details()` retrieves structured metadata directly before falling back to UI parsing.

---

#### 9. Missing Application Shutdown Protocol (`WM_DELETE_WINDOW`) [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 4035 - 4055`
- **Resolution:** Added `on_app_close()` callback registered to `app.protocol("WM_DELETE_WINDOW", on_app_close)`. Gracefully signals cancellation to all active workers, flushes `save_queue()` and `save_settings()`, shuts down `_thumb_pool`, and terminates cleanly.

---

#### 10. Queue Persistence Restored (`save_queue()` / `load_queue()`) [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1990 - 2035`
- **Resolution:** Connected `save_queue()` to state transitions (`add`, `pause`, `resume`, `cancel`, `clear_finished`, and `_worker` completion). Restored serialization of all audio parameters (`volume_boost`, `trim_silence`, `segment`, `fpath`). Removed destructive premature `os.remove(QUEUE_FILE)` in `load_queue()`.

---

#### 11. "Stop" Action Restarts Queue Processing Bug [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 940 - 948`
- **Resolution:** Removed `app.after(100, global_queue.pump)` from `trigger_stop()`. Clicking "Stop" cancels active jobs without immediately popping and downloading the next pending job.

---

#### 12. Non-Unique Job Identifiers via `time.time()` [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1603`
- **Resolution:** Replaced `str(time.time())` with `uuid.uuid4().hex` for 100% collision-free job identification across high-speed concurrent enqueuing.

---

#### 13. Shared Global Variable Collision During Multi-Downloads [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1704 - 1735, 1835`
- **Resolution:** Eliminated `global _last_downloading_size` from concurrent worker threads. Stored `last_downloading_size` directly on the `job` dictionary in `_job_progress_hook`.

---

#### 14. O(N) Sequential Playlist Analysis Stalling the UI [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 2180 - 2185`
- **Resolution:** Set `local_opts['extract_flat'] = 'in_playlist'` for both video and audio playlists. Prevents minutes of sequential format tree HTTP queries on large playlists, fetching entries in 1-2 seconds.

---

#### 15. Unbounded In-Memory & Disk Thumbnail Leaks [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 730 - 750, 1370 - 1500, 2350 - 2400`
- **Resolution:** 
  1. Added `_clean_thumb_cache()` background cleanup capping the `~/.hedra_downloader/thumbs/` directory at 100MB with LRU disk pruning.
  2. Implemented 100-item LRU cache for in-memory thumbnail images.
  3. Decoupled Tkinter widgets from data models via `_queue_ui_widgets` mapping to prevent widget memory leaks and snapshot mutation bugs.

---

#### 16. Fragile Dependency Check in Frozen Executables [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 32 - 48`
- **Resolution:** Added `if getattr(sys, 'frozen', False): return` guard at entry of `check_deps()`, preventing infinite pip process spawning when compiled with PyInstaller.

---

#### 17. Subtitle Container Constraint (Rule 4 Violation) [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 2805 - 2820`
- **Resolution:** In `create_vid_options()`, attached a trace callback to `fmt_var`. When `mp4` is selected, `s_menu` is immediately disabled (`state='disabled'`) and forced to `"None"`. Re-enabled when `Default` or `mkv` is selected.

---

#### 18. Timestamp Query Stripping on YouTube URLs [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 780 - 795`
- **Resolution:** Removed `|t` from `track_pattern` regex in `normalize_media_url()`, preserving video timestamps (e.g., `?t=120`) while stripping tracking parameters.

---

#### 19. Git Repository Hygiene [RESOLVED]
- **Location:** `.gitignore`
- **Resolution:** Verified `*.exe` and `*.dll` are ignored in `.gitignore`, preventing accidental commits of large external binaries into version control.

---

#### 20. Modernized Requirements Specification [RESOLVED]
- **Location:** `requirements.txt`
- **Resolution:** Updated `requirements.txt` to require `yt-dlp>=2026.10.26`, `customtkinter>=5.2.2`, `pillow>=10.0.0`, `mutagen>=1.47.0`, and `windnd>=1.0.7; sys_platform == 'win32'`.

---

### [P2 - High-Value Features & UX Polish] — STATUS: ALL RESOLVED & VERIFIED

#### 21. Automatic Network Retry & Stream Auto-Resume [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1770 - 1830`
- **Resolution:** Integrated exponential backoff retry loop in `JobQueue._worker` for transient network drops (timeouts, connection resets). Displays live retry counter (`"Network drop. Retry 1/3 in 2s..."`) and auto-resumes using `.part` files before failing.

---

#### 22. True Video Clip & Segment Trimming UI [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1205 - 1240, 2900 - 2930, 3165, 3195`
- **Resolution:** 
  1. Built `parse_timestamp(text)` supporting `hh:mm:ss`, `mm:ss`, seconds, and natural language (`1m 30s`).
  2. Added `create_segment_row` UI inputs to Single Video and Single Audio tabs.
  3. Injected `download_ranges` with `force_keyframes_at_cuts=True` into yt-dlp download options.

---

#### 23. Direct Media Playback & Explorer Actions in Queue & History [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1550 - 1585`
- **Resolution:** Added 1-click `▶ Play` and `📁` folder reveal buttons to completed Queue cards. Added `🔄 Retry` button to failed/cancelled Queue cards allowing instant re-enqueue without re-pasting URLs.

---

#### 24. Overall Queue Progress & ETA Dashboard [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1450 - 1485, 3450 - 3465`
- **Resolution:** Added `lbl_q_pending` to network monitor bar displaying `⏳ Pending: X` alongside `⚡ Speed`, `▲ Peak`, `⬇ Active`, and `📦 Session completed`.

---

#### 25. Per-Item Progress & Overall Completion in Playlist Downloads [RESOLVED]
- **Location:** `Hedra Downloader PRO.pyw : 1720 - 1755`
- **Resolution:** Added `[idx/total]` item progress prefix in `_job_progress_hook`. Formulated aggregate playlist percentage calculation `((playlist_idx - 1) + item_pct) / playlist_count`, giving smooth continuous 0%–100% progress across entire multi-item playlists.

---

## Action Item Summary Table

| ID | Priority | Category | Component | Status |
|---|---|---|---|---|
| **#1** | **P0** | Security | `send_notification` | **RESOLVED** |
| **#2** | **P0** | Security | `show_in_explorer` | **RESOLVED** |
| **#3** | **P0** | Concurrency | `JobQueue` | **RESOLVED** |
| **#4** | **P0** | Logic / Concurrency | `act_bvid_dl` | **RESOLVED** |
| **#5** | **P0** | Reliability | Audio Enhancer | **RESOLVED** |
| **#6** | **P0** | Logic | Subtitle Cleaner | **RESOLVED** |
| **#7** | **P0** | Performance | History / Queue UI | **RESOLVED** |
| **#8** | **P1** | Architecture | Analyzer / Disptacher | **RESOLVED** |
| **#9** | **P1** | Lifecycle | Main Application | **RESOLVED** |
| **#10** | **P1** | Reliability | `JobQueue` | **RESOLVED** |
| **#11** | **P1** | Logic | `trigger_stop` | **RESOLVED** |
| **#12** | **P1** | Logic | `JobQueue` | **RESOLVED** |
| **#13** | **P1** | Concurrency | `_worker` | **RESOLVED** |
| **#14** | **P1** | Performance | Playlist Analyzer | **RESOLVED** |
| **#15** | **P1** | Resource Management | History / Queue UI | **RESOLVED** |
| **#16** | **P1** | Reliability | `check_deps` | **RESOLVED** |
| **#17** | **P1** | Logic | Options UI | **RESOLVED** |
| **#18** | **P1** | Logic | URL Normalizer | **RESOLVED** |
| **#19** | **P1** | Hygiene | Git Repository | **RESOLVED** |
| **#20** | **P1** | Packaging | `requirements.txt` | **RESOLVED** |
| **#21** | **P2** | Feature | Download Engine | **RESOLVED** |
| **#22** | **P2** | Feature | Trimming Engine | **RESOLVED** |
| **#23** | **P2** | UX | Queue / History UI | **RESOLVED** |
| **#24** | **P2** | UX | Queue UI | **RESOLVED** |
| **#25** | **P2** | UX | Playlist Engine | **RESOLVED** |
