import sys
import ctypes
import warnings
import os

# suppress huggingface hub authentication and symlink warnings
warnings.filterwarnings("ignore", message=".*unauthenticated.*")
warnings.filterwarnings("ignore", message=".*symlink.*")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# must be called before any window creation so windows binds the icon
# to this process instead of the python interpreter
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("voxmorph.app")
except Exception:
    pass

from gui.app import App


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    sys.exit(main())
