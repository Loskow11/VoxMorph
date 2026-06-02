import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from pathlib import Path
from gui.widgets.image_panel import ImagePanel
from utils.thread_worker import run_in_thread


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ASSETS_DIR = Path(__file__).parent.parent / "assets"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VoxMorph")
        self.geometry("900x620")
        self.resizable(False, False)
        self._image_path: str | None = None
        self._set_window_icon()
        self._build_layout()

    def _set_window_icon(self) -> None:
        # definit l'icone de la barre de titre et de la taskbar
        icon_path = ASSETS_DIR / "logo.png"
        if icon_path.exists():
            img = Image.open(icon_path).resize((32, 32), Image.LANCZOS)
            self._icon_photo = ImageTk.PhotoImage(img)
            self.iconphoto(True, self._icon_photo)

    def _build_layout(self) -> None:
        # colonne gauche : panneau image
        self._left = ctk.CTkFrame(self, width=440, fg_color="#181825")
        self._left.pack(side="left", fill="y", padx=(16, 8), pady=16)
        self._left.pack_propagate(False)

        self._panel = ImagePanel(self._left, width=400, height=400)
        self._panel.pack(padx=20, pady=(20, 12))

        self._btn_select = ctk.CTkButton(
            self._left,
            text="Selectionner une image",
            command=self._select_image,
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._btn_select.pack(pady=(0, 8), padx=20, fill="x")

        self._label_path = ctk.CTkLabel(
            self._left,
            text="",
            text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            wraplength=380,
        )
        self._label_path.pack(padx=20)

        # colonne droite : parametres et lancement
        self._right = ctk.CTkFrame(self, fg_color="#181825")
        self._right.pack(side="right", fill="both", expand=True, padx=(8, 16), pady=16)

        # header : logo + titre sur la meme ligne
        header = ctk.CTkFrame(self._right, fg_color="transparent")
        header.pack(pady=(28, 4))

        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            logo_img = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(38, 38),
            )
            ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header,
            text="VoxMorph",
            font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
            text_color="#cdd6f4",
        ).pack(side="left")

        ctk.CTkLabel(
            self._right,
            text="Reconstruction 3D depuis une image 2D",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#6c7086",
        ).pack(pady=(0, 32))

        # separateur visuel
        ctk.CTkFrame(self._right, height=1, fg_color="#313244").pack(
            fill="x", padx=24, pady=(0, 28)
        )

        self._btn_run = ctk.CTkButton(
            self._right,
            text="Lancer reconstruction",
            command=self._on_run,
            height=44,
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            text_color="#1e1e2e",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            state="disabled",
        )
        self._btn_run.pack(padx=24, fill="x")

        self._status_label = ctk.CTkLabel(
            self._right,
            text="",
            text_color="#a6e3a1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self._status_label.pack(pady=(12, 0))

    def _select_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir une image",
            filetypes=[("images", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._image_path = path
        self._panel.load_image(path)
        self._label_path.configure(text=path.split("/")[-1])
        self._btn_run.configure(state="normal")
        self._status_label.configure(text="")

    def _on_run(self) -> None:
        # desactive le bouton pendant le traitement pour eviter les doubles appels
        self._btn_run.configure(state="disabled")
        self._status_label.configure(text="Traitement en cours...", text_color="#f9e2af")
        run_in_thread(self._run_pipeline, on_done=self._on_pipeline_done)

    def _run_pipeline(self) -> None:
        # point d'entree du pipeline — remplace par l'inference reelle en phase 3
        print("traitement lance")

    def _on_pipeline_done(self) -> None:
        self._status_label.configure(text="Termine.", text_color="#a6e3a1")
        self._btn_run.configure(state="normal")
