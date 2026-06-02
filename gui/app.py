import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from pathlib import Path
from gui.widgets.image_panel import ImagePanel
from utils.thread_worker import run_in_thread, post_to_main


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ASSETS_DIR = Path(__file__).parent.parent / "assets"
TEMP_DIR = Path(__file__).parent.parent / "temp"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VoxMorph")
        self.geometry("1260x680")
        self.resizable(False, False)
        self._image_path: str | None = None
        self._processed_path: str | None = None
        self._mesh_path: str | None = None
        self._set_window_icon()
        self._build_layout()

    def _set_window_icon(self) -> None:
        # iconbitmap for the title bar, iconphoto for the windows taskbar
        ico_path = ASSETS_DIR / "logo.ico"
        png_path = ASSETS_DIR / "logo.png"
        if ico_path.exists():
            self.iconbitmap(str(ico_path))
        if png_path.exists():
            img = Image.open(png_path).resize((64, 64), Image.LANCZOS)
            self._taskbar_icon = ImageTk.PhotoImage(img)
            self.iconphoto(True, self._taskbar_icon)

    def _build_layout(self) -> None:
        # left column: original image
        self._left = ctk.CTkFrame(self, width=420, fg_color="#181825")
        self._left.pack(side="left", fill="y", padx=(16, 6), pady=16)
        self._left.pack_propagate(False)

        ctk.CTkLabel(
            self._left,
            text="Original image",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#6c7086",
        ).pack(pady=(14, 4))

        self._panel_original = ImagePanel(self._left, width=380, height=380)
        self._panel_original.pack(padx=20, pady=(0, 8))

        self._label_meta_original = ctk.CTkLabel(
            self._left,
            text="",
            text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            wraplength=360,
        )
        self._label_meta_original.pack(padx=20, pady=(0, 8))

        self._btn_select = ctk.CTkButton(
            self._left,
            text="Select an image",
            command=self._select_image,
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._btn_select.pack(pady=(0, 6), padx=20, fill="x")

        self._btn_reset = ctk.CTkButton(
            self._left,
            text="Reset",
            command=self._reset,
            fg_color="#313244",
            hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            state="disabled",
        )
        self._btn_reset.pack(padx=20, fill="x")

        # center column: background-removed result
        self._mid = ctk.CTkFrame(self, width=420, fg_color="#181825")
        self._mid.pack(side="left", fill="y", padx=6, pady=16)
        self._mid.pack_propagate(False)

        ctk.CTkLabel(
            self._mid,
            text="Background removed",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#6c7086",
        ).pack(pady=(14, 4))

        self._panel_processed = ImagePanel(self._mid, width=380, height=380)
        self._panel_processed.pack(padx=20, pady=(0, 8))

        self._label_meta_processed = ctk.CTkLabel(
            self._mid,
            text="",
            text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_meta_processed.pack(padx=20)

        # right column: header and controls
        self._right = ctk.CTkFrame(self, fg_color="#181825")
        self._right.pack(side="right", fill="both", expand=True, padx=(6, 16), pady=16)

        # header: logo + title
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
            text="3D reconstruction from a 2D image",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#6c7086",
        ).pack(pady=(0, 24))

        ctk.CTkFrame(self._right, height=1, fg_color="#313244").pack(
            fill="x", padx=24, pady=(0, 24)
        )

        self._btn_run = ctk.CTkButton(
            self._right,
            text="Start reconstruction",
            command=self._on_run,
            height=44,
            fg_color="#89b4fa",
            hover_color="#74c7ec",
            text_color="#1e1e2e",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            state="disabled",
        )
        self._btn_run.pack(padx=24, fill="x")

        # indeterminate progress bar, visible only during processing
        self._progress = ctk.CTkProgressBar(
            self._right,
            mode="indeterminate",
            height=6,
            progress_color="#89b4fa",
            fg_color="#313244",
        )
        self._progress.pack(padx=24, pady=(10, 0), fill="x")
        self._progress.set(0)

        self._status_label = ctk.CTkLabel(
            self._right,
            text="",
            text_color="#a6e3a1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self._status_label.pack(pady=(8, 0))

    def _select_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._image_path = path
        self._processed_path = None
        self._panel_original.load_image(path)
        self._panel_processed.clear()

        # display original image metadata
        img = Image.open(path)
        size_kb = Path(path).stat().st_size // 1024
        self._label_meta_original.configure(
            text=f"{Path(path).name}  •  {img.width}x{img.height}  •  {size_kb} KB"
        )
        self._label_meta_processed.configure(text="")
        self._btn_run.configure(state="normal")
        self._btn_reset.configure(state="normal")
        self._status_label.configure(text="")
        self._progress.set(0)

    def _reset(self) -> None:
        self._image_path = None
        self._processed_path = None
        self._mesh_path = None
        self._panel_original.clear()
        self._panel_processed.clear()
        self._label_meta_original.configure(text="")
        self._label_meta_processed.configure(text="")
        self._status_label.configure(text="")
        self._progress.set(0)
        self._btn_run.configure(state="disabled")
        self._btn_reset.configure(state="disabled")

    def _set_status(self, text: str, color: str = "#f9e2af") -> None:
        # updates the status label from any thread
        post_to_main(self._status_label.configure, text=text, text_color=color)

    def _on_run(self) -> None:
        # disables controls and starts the progress bar during processing
        self._btn_run.configure(state="disabled")
        self._btn_select.configure(state="disabled")
        self._btn_reset.configure(state="disabled")
        self._progress.start()
        self._status_label.configure(text="Initializing...", text_color="#f9e2af")
        run_in_thread(
            self._run_pipeline,
            on_done=self._on_pipeline_done,
            on_error=self._on_pipeline_error,
        )

    def _run_pipeline(self) -> None:
        from core.preprocessing import remove_background, normalize
        from core.inference import run_inference

        stem = Path(self._image_path).stem

        # step 1: background removal
        self._set_status("Loading segmentation model...")
        result = remove_background(self._image_path)

        # step 2: normalization
        self._set_status("Normalizing image (512x512)...")
        result = normalize(result, size=512)

        preprocessed_path = TEMP_DIR / f"{stem}_preprocessed.png"
        result.save(str(preprocessed_path))
        self._processed_path = str(preprocessed_path)

        # step 3: 3d inference
        mesh_path = OUTPUT_DIR / f"{stem}.obj"
        run_inference(
            image_path=preprocessed_path,
            output_path=mesh_path,
            export_format="obj",
            mc_resolution=128,
            on_progress=self._set_status,
        )
        self._mesh_path = str(mesh_path)

    def _on_pipeline_done(self) -> None:
        self._progress.stop()
        self._progress.set(1)

        # display processed image with its metadata
        self._panel_processed.load_image(self._processed_path)
        size_kb = Path(self._processed_path).stat().st_size // 1024
        self._label_meta_processed.configure(
            text=f"512x512  •  RGBA  •  {size_kb} KB"
        )

        mesh_kb = Path(self._mesh_path).stat().st_size // 1024
        self._status_label.configure(
            text=f"Mesh exported — {Path(self._mesh_path).name}  •  {mesh_kb} KB",
            text_color="#a6e3a1",
        )
        self._btn_run.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_reset.configure(state="normal")

    def _on_pipeline_error(self, exc: Exception) -> None:
        self._progress.stop()
        self._progress.set(0)
        self._status_label.configure(text=f"Error: {exc}", text_color="#f38ba8")
        self._btn_run.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_reset.configure(state="normal")
