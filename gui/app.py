import subprocess
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
from pathlib import Path
from gui.widgets.image_panel import ImagePanel
from gui.widgets.mesh_viewer import MeshViewer
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
        self.geometry("1600x700")
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
        self._left = ctk.CTkFrame(self, width=360, fg_color="#181825")
        self._left.pack(side="left", fill="y", padx=(14, 5), pady=14)
        self._left.pack_propagate(False)

        ctk.CTkLabel(
            self._left, text="Original image",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#6c7086",
        ).pack(pady=(12, 4))

        self._panel_original = ImagePanel(self._left, width=320, height=340)
        self._panel_original.pack(padx=20, pady=(0, 8))

        self._label_meta_original = ctk.CTkLabel(
            self._left, text="", text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11), wraplength=320,
        )
        self._label_meta_original.pack(padx=20, pady=(0, 8))

        self._btn_select = ctk.CTkButton(
            self._left, text="Select an image", command=self._select_image,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._btn_select.pack(pady=(0, 6), padx=20, fill="x")

        self._btn_reset = ctk.CTkButton(
            self._left, text="Reset", command=self._reset,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=13), state="disabled",
        )
        self._btn_reset.pack(padx=20, fill="x")

        # center-left column: background removed
        self._mid_left = ctk.CTkFrame(self, width=360, fg_color="#181825")
        self._mid_left.pack(side="left", fill="y", padx=5, pady=14)
        self._mid_left.pack_propagate(False)

        ctk.CTkLabel(
            self._mid_left, text="Background removed",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#6c7086",
        ).pack(pady=(12, 4))

        self._panel_processed = ImagePanel(self._mid_left, width=320, height=340)
        self._panel_processed.pack(padx=20, pady=(0, 8))

        self._label_meta_processed = ctk.CTkLabel(
            self._mid_left, text="", text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_meta_processed.pack(padx=20)

        # center-right column: 3d mesh viewer
        self._mid_right = ctk.CTkFrame(self, width=480, fg_color="#181825")
        self._mid_right.pack(side="left", fill="y", padx=5, pady=14)
        self._mid_right.pack_propagate(False)

        ctk.CTkLabel(
            self._mid_right, text="3D mesh viewer",
            font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#6c7086",
        ).pack(pady=(12, 4))

        self._mesh_viewer = MeshViewer(self._mid_right, width=440, height=440)
        self._mesh_viewer.pack(padx=20, pady=(0, 6))

        self._label_mesh_hint = ctk.CTkLabel(
            self._mid_right, text="",
            text_color="#6c7086", font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_mesh_hint.pack()

        # right column: controls and export
        self._right = ctk.CTkFrame(self, fg_color="#181825")
        self._right.pack(side="right", fill="both", expand=True, padx=(5, 14), pady=14)

        # header: logo + title
        header = ctk.CTkFrame(self._right, fg_color="transparent")
        header.pack(pady=(20, 4))

        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            logo_img = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(34, 34),
            )
            ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header, text="VoxMorph",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color="#cdd6f4",
        ).pack(side="left")

        ctk.CTkLabel(
            self._right, text="3D reconstruction from a 2D image",
            font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#6c7086",
        ).pack(pady=(0, 16))

        ctk.CTkFrame(self._right, height=1, fg_color="#313244").pack(
            fill="x", padx=20, pady=(0, 16)
        )

        self._btn_run = ctk.CTkButton(
            self._right, text="Start reconstruction", command=self._on_run,
            height=42, fg_color="#89b4fa", hover_color="#74c7ec",
            text_color="#1e1e2e",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            state="disabled",
        )
        self._btn_run.pack(padx=20, fill="x")

        self._progress = ctk.CTkProgressBar(
            self._right, mode="determinate", height=5,
            progress_color="#89b4fa", fg_color="#313244",
        )
        self._progress.pack(padx=20, pady=(8, 0), fill="x")
        self._progress.set(0)

        self._progress_label = ctk.CTkLabel(
            self._right, text="", text_color="#585b70",
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._progress_label.pack(pady=(2, 0))

        self._status_label = ctk.CTkLabel(
            self._right, text="", text_color="#a6e3a1",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self._status_label.pack(pady=(6, 0))

        # export section
        ctk.CTkFrame(self._right, height=1, fg_color="#313244").pack(
            fill="x", padx=20, pady=(16, 12)
        )

        ctk.CTkLabel(
            self._right, text="Export mesh",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#cdd6f4",
        ).pack(padx=20, anchor="w")

        export_row = ctk.CTkFrame(self._right, fg_color="transparent")
        export_row.pack(padx=20, pady=(8, 0), fill="x")

        for fmt in ["OBJ", "GLB", "PLY"]:
            ctk.CTkButton(
                export_row, text=f".{fmt.lower()}",
                command=lambda f=fmt: self._export(f.lower()),
                fg_color="#313244", hover_color="#45475a",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                width=60, state="disabled",
            ).pack(side="left", padx=(0, 6))

        self._btn_open_output = ctk.CTkButton(
            self._right, text="Open output folder",
            command=self._open_output_folder,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            state="disabled",
        )
        self._btn_open_output.pack(padx=20, pady=(8, 0), fill="x")

    def _select_image(self) -> None:
        path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if not path:
            return
        self._image_path = path
        self._processed_path = None
        self._mesh_path = None
        self._panel_original.load_image(path)
        self._panel_processed.clear()
        self._mesh_viewer.clear()
        img = Image.open(path)
        size_kb = Path(path).stat().st_size // 1024
        self._label_meta_original.configure(
            text=f"{Path(path).name}  •  {img.width}x{img.height}  •  {size_kb} KB"
        )
        self._label_meta_processed.configure(text="")
        self._label_mesh_hint.configure(text="")
        self._btn_run.configure(state="normal")
        self._btn_reset.configure(state="normal")
        self._status_label.configure(text="")
        self._progress.set(0)
        self._progress_label.configure(text="")
        self._set_export_state("disabled")

    def _reset(self) -> None:
        self._image_path = None
        self._processed_path = None
        self._mesh_path = None
        self._panel_original.clear()
        self._panel_processed.clear()
        self._mesh_viewer.clear()
        self._label_meta_original.configure(text="")
        self._label_meta_processed.configure(text="")
        self._label_mesh_hint.configure(text="")
        self._status_label.configure(text="")
        self._progress.set(0)
        self._progress_label.configure(text="")
        self._btn_run.configure(state="disabled")
        self._btn_reset.configure(state="disabled")
        self._set_export_state("disabled")

    def _set_export_state(self, state: str) -> None:
        for child in self._right.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton) and btn.cget("text") in (".obj", ".glb", ".ply"):
                        btn.configure(state=state)
        self._btn_open_output.configure(state=state)

    def _set_status(self, text: str, color: str = "#f9e2af") -> None:
        # updates the status label from any thread
        post_to_main(self._status_label.configure, text=text, text_color=color)

    def _set_progress(self, value: float, label: str = "") -> None:
        # updates progress bar and label from any thread (value: 0.0 to 1.0)
        post_to_main(self._progress.set, value)
        post_to_main(
            self._progress_label.configure,
            text=f"{int(value * 100)}%  —  {label}" if label else f"{int(value * 100)}%",
        )

    def _show_preprocessed(self, path: str) -> None:
        self._panel_processed.load_image(path)
        size_kb = Path(path).stat().st_size // 1024
        self._label_meta_processed.configure(text=f"512x512  •  RGBA  •  {size_kb} KB")

    def _show_mesh(self, path: str) -> None:
        # loads mesh into viewer and enables export buttons
        self._mesh_viewer.load_mesh(path)
        self._label_mesh_hint.configure(text="drag to rotate  •  scroll to zoom")
        self._set_export_state("normal")

    def _on_run(self) -> None:
        self._btn_run.configure(state="disabled")
        self._btn_select.configure(state="disabled")
        self._btn_reset.configure(state="disabled")
        self._progress.set(0)
        self._progress_label.configure(text="")
        self._status_label.configure(text="Starting...", text_color="#f9e2af")
        run_in_thread(
            self._run_pipeline,
            on_done=self._on_pipeline_done,
            on_error=self._on_pipeline_error,
        )

    def _run_pipeline(self) -> None:
        from core.preprocessing import remove_background, normalize
        from core.inference import run_inference

        stem = Path(self._image_path).stem

        self._set_status("Step 1/3 — Removing background...")
        self._set_progress(0.05, "loading segmentation model")
        result = remove_background(self._image_path)

        self._set_status("Step 2/3 — Normalizing image...")
        self._set_progress(0.25, "resizing to 512x512")
        result = normalize(result, size=512)

        preprocessed_path = TEMP_DIR / f"{stem}_preprocessed.png"
        result.save(str(preprocessed_path))
        self._processed_path = str(preprocessed_path)
        post_to_main(self._show_preprocessed, str(preprocessed_path))

        self._set_status("Step 3/3 — Loading 3D model weights...")
        self._set_progress(0.35, "downloading triposr weights (first run only)")

        def _inference_progress(msg: str) -> None:
            steps = {
                "Preparing": 0.40,
                "Running":   0.55,
                "Extracting": 0.80,
                "Exporting": 0.92,
            }
            ratio = next((v for k, v in steps.items() if k in msg), None)
            if ratio:
                self._set_progress(ratio, msg.lower())
            self._set_status(f"Step 3/3 — {msg}")

        mesh_path = OUTPUT_DIR / f"{stem}.obj"
        run_inference(
            image_path=preprocessed_path,
            output_path=mesh_path,
            export_format="obj",
            mc_resolution=128,
            on_progress=_inference_progress,
        )
        self._mesh_path = str(mesh_path)

    def _on_pipeline_done(self) -> None:
        self._set_progress(1.0, "done")
        mesh_kb = Path(self._mesh_path).stat().st_size // 1024
        self._status_label.configure(
            text=f"Mesh ready — {Path(self._mesh_path).name}  •  {mesh_kb} KB",
            text_color="#a6e3a1",
        )
        self._show_mesh(self._mesh_path)
        self._btn_run.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_reset.configure(state="normal")

    def _on_pipeline_error(self, exc: Exception) -> None:
        self._progress.set(0)
        self._progress_label.configure(text="")
        self._status_label.configure(text=f"Error: {exc}", text_color="#f38ba8")
        self._btn_run.configure(state="normal")
        self._btn_select.configure(state="normal")
        self._btn_reset.configure(state="normal")

    def _export(self, fmt: str) -> None:
        if not self._mesh_path:
            return
        from core.export import export_mesh
        stem = Path(self._mesh_path).stem
        dest = filedialog.asksaveasfilename(
            title=f"Export as .{fmt}",
            defaultextension=f".{fmt}",
            initialfile=f"{stem}.{fmt}",
            filetypes=[(fmt.upper(), f"*.{fmt}")],
        )
        if dest:
            export_mesh(self._mesh_path, dest)
            self._status_label.configure(
                text=f"Exported to {Path(dest).name}", text_color="#a6e3a1"
            )

    def _open_output_folder(self) -> None:
        subprocess.Popen(f'explorer "{OUTPUT_DIR}"')
