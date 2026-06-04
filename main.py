import sys
import ctypes
import warnings
import os

# suppress huggingface hub and transformers warnings
warnings.filterwarnings("ignore", message=".*unauthenticated.*")
warnings.filterwarnings("ignore", message=".*symlink.*")
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

import logging
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

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
