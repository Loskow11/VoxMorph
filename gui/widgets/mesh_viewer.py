import numpy as np
import trimesh
import customtkinter as ctk
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


class MeshViewer(ctk.CTkFrame):
    # offscreen mesh viewer using matplotlib, with drag-to-rotate and scroll-to-zoom
    def __init__(self, master, width=480, height=480, **kwargs):
        super().__init__(master, width=width, height=height, **kwargs)
        self.render_width = width
        self.render_height = height
        self.configure(fg_color="#1e1e2e")
        self.pack_propagate(False)

        self._mesh = None
        self._azimuth = 45.0
        self._elevation = 20.0
        self._distance = 2.5
        self._drag_start = None
        self._photo = None

        self._placeholder = ctk.CTkLabel(
            self,
            text="No mesh loaded",
            text_color="#6c7086",
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self._canvas_label = ctk.CTkLabel(self, text="")
        self._canvas_label.place(relx=0.5, rely=0.5, anchor="center")

        self._canvas_label.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas_label.bind("<B1-Motion>", self._on_drag)
        self._canvas_label.bind("<MouseWheel>", self._on_scroll)

    def load_mesh(self, path: str) -> None:
        # loads an obj/glb/ply mesh and triggers the first render
        raw = trimesh.load(path, force="mesh")
        if isinstance(raw, trimesh.Scene):
            raw = trimesh.util.concatenate(list(raw.geometry.values()))
        self._mesh = raw
        self._normalize_mesh()
        self._placeholder.place_forget()
        self._render()

    def _normalize_mesh(self) -> None:
        # centers the mesh at origin and scales it to fit in a unit sphere
        self._mesh.vertices -= self._mesh.centroid
        scale = np.max(np.linalg.norm(self._mesh.vertices, axis=1))
        if scale > 0:
            self._mesh.vertices /= scale

    def _render(self) -> None:
        if self._mesh is None:
            return

        verts = self._mesh.vertices
        faces = self._mesh.faces

        dpi = 96
        fig_w = self.render_width / dpi
        fig_h = self.render_height / dpi

        fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi, facecolor="#1e1e2e")
        ax = fig.add_subplot(111, projection="3d", facecolor="#1e1e2e")

        # build face polygons for rendering
        tris = verts[faces]

        # compute per-face normals for basic shading
        v0 = tris[:, 0]
        v1 = tris[:, 1]
        v2 = tris[:, 2]
        normals = np.cross(v1 - v0, v2 - v0)
        norms = np.linalg.norm(normals, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normals /= norms

        # light direction from camera-ish angle
        light = np.array([0.5, 0.8, 0.6])
        light /= np.linalg.norm(light)
        intensity = np.clip(normals @ light, 0.15, 1.0)

        # map intensity to blue-ish color palette
        base = np.array([0.34, 0.71, 0.98])
        colors = intensity[:, None] * base
        colors = np.clip(colors, 0, 1)
        face_colors = np.hstack([colors, np.full((len(colors), 1), 0.92)])

        poly = Poly3DCollection(tris, zsort="average")
        poly.set_facecolor(face_colors)
        poly.set_edgecolor("none")
        ax.add_collection3d(poly)

        # fit axes to mesh bounds
        lim = 1.1
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_zlim(-lim, lim)
        ax.set_axis_off()

        ax.view_init(elev=self._elevation, azim=self._azimuth)
        ax.dist = self._distance + 7

        fig.tight_layout(pad=0)

        # render to PIL image
        from io import BytesIO
        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight",
                    facecolor="#1e1e2e", edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf).copy()

        ctk_img = ctk.CTkImage(
            light_image=img, dark_image=img,
            size=(self.render_width, self.render_height),
        )
        self._photo = ctk_img
        self._canvas_label.configure(image=ctk_img)

    def _on_drag_start(self, event) -> None:
        self._drag_start = (event.x, event.y)

    def _on_drag(self, event) -> None:
        if self._drag_start is None or self._mesh is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._azimuth += dx * 0.6
        self._elevation = float(np.clip(self._elevation - dy * 0.6, -89, 89))
        self._drag_start = (event.x, event.y)
        self._render()

    def _on_scroll(self, event) -> None:
        if self._mesh is None:
            return
        self._distance = float(np.clip(self._distance - event.delta * 0.002, 0.5, 4.0))
        self._render()

    def clear(self) -> None:
        self._mesh = None
        self._canvas_label.configure(image=None)
        self._photo = None
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")
