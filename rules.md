\# AI Coding Rules \& Constraints



\## Rule 1: STRICT THREADING PROHIBITIONS

\*\*Never, under any circumstances, block the main CustomTkinter GUI thread.\*\*

\* All `yt-dlp` operations, network I/O, and file processing must run in background threads.

\* Use thread-safe signaling (events or queues) to update GUI progress bars and labels.

\* Every active download in the `JobQueue` must have an independent `threading.Event` (in `cancel\_events\[jid]`) to allow isolated cancellation without interrupting other concurrent jobs.



\## Rule 2: STRICT NO-ARIA2C POLICY

\*\*Do not implement or suggest external multi-threaded downloaders like `aria2c`.\*\* \* This causes fatal process-spawning bugs where downloads persist after thread cancellation.

\* Achieve concurrent speed exclusively through `yt-dlp`'s native concurrent fragment settings.



\## Rule 3: UI Layout \& Packing Order

\* \*\*Footer Precedence:\*\* The footer bar (progress bar, session counter, VIEW QUEUE button) MUST be packed with `side="bottom"` \*\*BEFORE\*\* the main Tabview is packed. Reversing this order breaks the layout.

\* \*\*Input Traces:\*\* Automatically bind traces (`attach\_auto\_check`, `bind\_url\_change\_clear`) to clear stale state/banners the instant a URL input is modified.

\* \*\*Settings Tab:\*\* All content inside the Settings tab must be wrapped in a `CTkScrollableFrame` to guarantee visibility on minimum 800x600 window sizes.



\## Rule 4: Subtitles \& Formats

\* Subtitles are exclusively supported via the MKV container. If a user selects `mp4`, the subtitle menu must be disabled. 



\## Rule 5: Cross-Layout Paste Handling

\* Do not rely on standard `<Control-v>` bindings. 

\* Maintain the global `\_global\_paste\_handler` which intercepts keycode `86` on `<Control-KeyPress>` and suppresses default paste events to prevent double-pasting on foreign keyboard layouts.



\## Rule 6: Background Installations

\* When executing background `pip install` commands (like for `mutagen`), you must use `creationflags=0x08000000` on Windows to prevent console windows from flashing on screen.

