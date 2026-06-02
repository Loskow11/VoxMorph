import sys
import ctypes

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
