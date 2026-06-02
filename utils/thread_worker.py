import threading
from typing import Callable


def run_in_thread(
    target: Callable,
    args: tuple = (),
    on_done: Callable | None = None,
    daemon: bool = True,
) -> threading.Thread:
    # lance target dans un thread separe et appelle on_done dans le thread principal via after()
    import tkinter as tk

    root = tk._default_root

    def wrapper():
        target(*args)
        if on_done and root:
            root.after(0, on_done)

    t = threading.Thread(target=wrapper, daemon=daemon)
    t.start()
    return t
