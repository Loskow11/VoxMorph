import threading
from typing import Callable


def run_in_thread(
    target: Callable,
    args: tuple = (),
    on_done: Callable | None = None,
    on_error: Callable | None = None,
    daemon: bool = True,
) -> threading.Thread:
    # runs target in a background thread, on_done and on_error are dispatched
    # to the main thread via after()
    import tkinter as tk

    root = tk._default_root

    def wrapper():
        try:
            target(*args)
            if on_done and root:
                root.after(0, on_done)
        except Exception as exc:
            if on_error and root:
                root.after(0, lambda e=exc: on_error(e))

    t = threading.Thread(target=wrapper, daemon=daemon)
    t.start()
    return t


def post_to_main(callback: Callable, *args, **kwargs) -> None:
    # dispatches a call to the main thread from any thread
    import tkinter as tk
    root = tk._default_root
    if root:
        root.after(0, lambda: callback(*args, **kwargs))
