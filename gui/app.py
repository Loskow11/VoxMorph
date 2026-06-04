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

# ui scaling constants relative to screen size
_SIDEBAR_W = 240
_MIN_PREVIEW = 300
_MAX_PREVIEW = 520


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("VoxMorph")
        self._image_path: str | None = None
        self._processed_path: str | None = None
        self._mesh_path: str | None = None
        self._set_window_icon()
        self._compute_geometry()
        self._build_layout()

    def _compute_geometry(self) -> None:
        # fits the window to 90% of the screen, respecting min/max bounds
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w = min(int(sw * 0.90), 1400)
        h = min(int(sh * 0.88), 820)
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.resizable(True, True)
        self.minsize(800, 560)
        # preview size scales with window width
        self._preview_size = min(
            max(_MIN_PREVIEW, int((w - _SIDEBAR_W) * 0.70)), _MAX_PREVIEW
        )

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
        ps = self._preview_size

        # sidebar (right): controls fixed width
        self._sidebar = ctk.CTkFrame(self, width=_SIDEBAR_W, fg_color="#181825")
        self._sidebar.pack(side="right", fill="y", padx=(6, 12), pady=12)
        self._sidebar.pack_propagate(False)
        self._build_sidebar()

        # main area (left): tabview fills remaining space
        self._main = ctk.CTkFrame(self, fg_color="#181825")
        self._main.pack(side="left", fill="both", expand=True, padx=(12, 6), pady=12)

        self._tabs = ctk.CTkTabview(
            self._main,
            fg_color="#1e1e2e",
            segmented_button_fg_color="#313244",
            segmented_button_selected_color="#89b4fa",
            segmented_button_selected_hover_color="#74c7ec",
            segmented_button_unselected_color="#313244",
            segmented_button_unselected_hover_color="#45475a",
            text_color="#cdd6f4",
        )
        self._tabs.pack(fill="both", expand=True)

        # tab 1: original image
        self._tabs.add("Original")
        tab_orig = self._tabs.tab("Original")
        self._panel_original = ImagePanel(tab_orig, width=ps, height=ps)
        self._panel_original.pack(padx=20, pady=(16, 8))
        self._label_meta_original = ctk.CTkLabel(
            tab_orig, text="", text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_meta_original.pack()

        # tab 2: background removed
        self._tabs.add("Preprocessed")
        tab_proc = self._tabs.tab("Preprocessed")
        self._panel_processed = ImagePanel(tab_proc, width=ps, height=ps)
        self._panel_processed.pack(padx=20, pady=(16, 8))
        self._label_meta_processed = ctk.CTkLabel(
            tab_proc, text="", text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_meta_processed.pack()

        # tab 3: 3d viewer
        self._tabs.add("3D Viewer")
        tab_3d = self._tabs.tab("3D Viewer")
        self._mesh_viewer = MeshViewer(tab_3d, width=ps, height=ps)
        self._mesh_viewer.pack(padx=20, pady=(16, 4))
        self._label_mesh_hint = ctk.CTkLabel(
            tab_3d, text="",
            text_color="#6c7086", font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self._label_mesh_hint.pack()

    def _build_sidebar(self) -> None:
        sb = self._sidebar

        # header
        header = ctk.CTkFrame(sb, fg_color="transparent")
        header.pack(pady=(16, 4), padx=12)
        logo_path = ASSETS_DIR / "logo.png"
        if logo_path.exists():
            logo_img = ctk.CTkImage(
                light_image=Image.open(logo_path),
                dark_image=Image.open(logo_path),
                size=(28, 28),
            )
            ctk.CTkLabel(header, image=logo_img, text="").pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            header, text="VoxMorph",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color="#cdd6f4",
        ).pack(side="left")

        ctk.CTkLabel(
            sb, text="2D → 3D reconstruction",
            font=ctk.CTkFont(family="Segoe UI", size=10), text_color="#6c7086",
        ).pack(pady=(0, 12))

        ctk.CTkFrame(sb, height=1, fg_color="#313244").pack(fill="x", padx=12, pady=(0, 12))

        # image selection
        self._btn_select = ctk.CTkButton(
            sb, text="Select image", command=self._select_image,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        self._btn_select.pack(padx=12, pady=(0, 6), fill="x")

        self._btn_reset = ctk.CTkButton(
            sb, text="Reset", command=self._reset,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=12), state="disabled",
        )
        self._btn_reset.pack(padx=12, pady=(0, 12), fill="x")

        ctk.CTkFrame(sb, height=1, fg_color="#313244").pack(fill="x", padx=12, pady=(0, 12))

        # launch button
        self._btn_run = ctk.CTkButton(
            sb, text="Start reconstruction", command=self._on_run,
            height=38, fg_color="#89b4fa", hover_color="#74c7ec",
            text_color="#1e1e2e",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            state="disabled",
        )
        self._btn_run.pack(padx=12, fill="x")

        # progress
        self._progress = ctk.CTkProgressBar(
            sb, mode="determinate", height=5,
            progress_color="#89b4fa", fg_color="#313244",
        )
        self._progress.pack(padx=12, pady=(8, 0), fill="x")
        self._progress.set(0)

        self._progress_label = ctk.CTkLabel(
            sb, text="", text_color="#585b70",
            font=ctk.CTkFont(family="Segoe UI", size=10),
        )
        self._progress_label.pack(pady=(2, 0))

        self._status_label = ctk.CTkLabel(
            sb, text="", text_color="#a6e3a1",
            font=ctk.CTkFont(family="Segoe UI", size=11), wraplength=210,
        )
        self._status_label.pack(pady=(6, 0), padx=8)

        ctk.CTkFrame(sb, height=1, fg_color="#313244").pack(fill="x", padx=12, pady=(14, 10))

        # settings section
        ctk.CTkLabel(
            sb, text="Settings",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#cdd6f4",
        ).pack(padx=12, anchor="w")

        ctk.CTkLabel(
            sb, text="Mesh resolution",
            font=ctk.CTkFont(family="Segoe UI", size=10), text_color="#6c7086",
        ).pack(padx=12, pady=(6, 2), anchor="w")

        self._resolution_var = ctk.StringVar(value="128")
        self._resolution_seg = ctk.CTkSegmentedButton(
            sb,
            values=["64", "128", "256"],
            variable=self._resolution_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            selected_color="#89b4fa",
            selected_hover_color="#74c7ec",
            unselected_color="#313244",
            unselected_hover_color="#45475a",
            text_color="#1e1e2e",
            text_color_disabled="#6c7086",
        )
        self._resolution_seg.pack(padx=12, pady=(0, 6), fill="x")

        ctk.CTkLabel(
            sb, text="64 = fast  •  256 = detailed",
            font=ctk.CTkFont(family="Segoe UI", size=9), text_color="#585b70",
        ).pack(padx=12, anchor="w")

        self._remove_bg_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            sb,
            text="Remove background",
            variable=self._remove_bg_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#cdd6f4",
            checkbox_width=16, checkbox_height=16,
            checkmark_color="#1e1e2e",
            fg_color="#89b4fa", hover_color="#74c7ec",
        ).pack(padx=12, pady=(10, 0), anchor="w")

        ctk.CTkFrame(sb, height=1, fg_color="#313244").pack(fill="x", padx=12, pady=(12, 10))

        # export section
        ctk.CTkLabel(
            sb, text="Export mesh",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#cdd6f4",
        ).pack(padx=12, anchor="w")

        export_row = ctk.CTkFrame(sb, fg_color="transparent")
        export_row.pack(padx=12, pady=(6, 6), fill="x")

        self._export_btns = {}
        for fmt in ["obj", "glb", "ply"]:
            btn = ctk.CTkButton(
                export_row, text=f".{fmt}",
                command=lambda f=fmt: self._export(f),
                fg_color="#313244", hover_color="#45475a",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                width=52, state="disabled",
            )
            btn.pack(side="left", padx=(0, 4))
            self._export_btns[fmt] = btn

        self._btn_open_output = ctk.CTkButton(
            sb, text="Open output folder",
            command=self._open_output_folder,
            fg_color="#313244", hover_color="#45475a",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            state="disabled",
        )
        self._btn_open_output.pack(padx=12, fill="x")

    # --- actions ---

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
        self._tabs.set("Original")

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
        for btn in self._export_btns.values():
            btn.configure(state=state)
        self._btn_open_output.configure(state=state)

    def _set_status(self, text: str, color: str = "#f9e2af") -> None:
        post_to_main(self._status_label.configure, text=text, text_color=color)

    def _set_progress(self, value: float, label: str = "") -> None:
        post_to_main(self._progress.set, value)
        post_to_main(
            self._progress_label.configure,
            text=f"{int(value * 100)}%  —  {label}" if label else f"{int(value * 100)}%",
        )

    def _show_preprocessed(self, path: str) -> None:
        self._panel_processed.load_image(path)
        size_kb = Path(path).stat().st_size // 1024
        self._label_meta_processed.configure(text=f"512x512  •  RGBA  •  {size_kb} KB")
        self._tabs.set("Preprocessed")

    def _show_mesh(self, path: str) -> None:
        self._mesh_viewer.load_mesh(path)
        self._label_mesh_hint.configure(text="drag to rotate  •  scroll to zoom")
        self._set_export_state("normal")
        self._tabs.set("3D Viewer")

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
        from PIL import Image as PilImage

        stem = Path(self._image_path).stem
        mc_res = int(self._resolution_var.get())
        do_remove_bg = self._remove_bg_var.get()

        if do_remove_bg:
            self._set_status("Step 1/3 — Removing background...")
            self._set_progress(0.05, "loading segmentation model")
            result = remove_background(self._image_path)
        else:
            # skip background removal, load image directly as rgba
            self._set_status("Step 1/3 — Skipping background removal...")
            self._set_progress(0.10, "background removal disabled")
            result = PilImage.open(self._image_path).convert("RGBA")

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
            mc_resolution=mc_res,
            on_progress=_inference_progress,
        )
        self._mesh_path = str(mesh_path)

    def _on_pipeline_done(self) -> None:
        self._set_progress(1.0, "done")
        mesh_kb = Path(self._mesh_path).stat().st_size // 1024
        self._status_label.configure(
            text=f"Mesh ready\n{Path(self._mesh_path).name}\n{mesh_kb} KB",
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
                text=f"Exported\n{Path(dest).name}", text_color="#a6e3a1"
            )

    def _open_output_folder(self) -> None:
        subprocess.Popen(f'explorer "{OUTPUT_DIR}"')
