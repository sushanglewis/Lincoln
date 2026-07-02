__version__ = "0.1.0"

# Textual redirects stderr to an internal stream whose fileno() is -1. tqdm
# creates a multiprocessing.RLock on first use, and its resource_tracker spawn
# passes that stderr fd to fork_exec, causing "ValueError: bad value(s) in
# fds_to_keep" when faster-whisper downloads models inside the TUI. Pin tqdm's
# lock to a thread-local RLock before any tqdm usage.
import threading

try:
    import tqdm
    import tqdm.std

    tqdm.tqdm._lock = threading.RLock()
    tqdm.std.tqdm._lock = threading.RLock()
except Exception:  # noqa: BLE001
    pass
