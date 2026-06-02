import threading
from typing import Callable


def run_in_thread(
    target: Callable,
    args: tuple = (),
    on_done: Callable | None = None,
    on_error: Callable | None = None,
    daemon: bool = True,
) -> threading.Thread:
    # lance target dans un thread separe, on_done et on_error sont rappeles via after() dans le thread principal
    import tkinter as tk

    root = tk._default_root

    def wrapper():
        try:
            target(*args)
            if on_done and root:
                root.after(0, on_done)
        except Exception as exc:
            if on_error and root:
                root.after(0, lambda: on_error(exc))

    t = threading.Thread(target=wrapper, daemon=daemon)
    t.start()
    return t


def post_to_main(callback: Callable, *args) -> None:
    # envoie un appel dans le thread principal depuis n'importe quel thread
    import tkinter as tk
    root = tk._default_root
    if root:
        root.after(0, lambda: callback(*args))
