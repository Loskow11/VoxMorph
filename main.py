import sys
import ctypes

# doit etre appele avant toute creation de fenetre pour que windows
# associe l'icone de la taskbar au process et non a l'interpreteur python
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
