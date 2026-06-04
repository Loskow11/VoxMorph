import numpy as np
import trimesh
import customtkinter as ctk
from PIL import Image


class MeshViewer(ctk.CTkFrame):
    # offscreen mesh viewer with drag-to-rotate and scroll-to-zoom
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

        # bind mouse events for rotation and zoom
        self._canvas_label.bind("<ButtonPress-1>", self._on_drag_start)
        self._canvas_label.bind("<B1-Motion>", self._on_drag)
        self._canvas_label.bind("<MouseWheel>", self._on_scroll)

    def load_mesh(self, path: str) -> None:
        # loads an obj/glb/ply mesh and triggers the first render
        self._mesh = trimesh.load(path, force="mesh")
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
        try:
            import pyrender
            import os
            os.environ.setdefault("PYOPENGL_PLATFORM", "")
        except ImportError:
            self._render_fallback()
            return

        try:
            mesh_pr = pyrender.Mesh.from_trimesh(self._mesh, smooth=False)
            scene = pyrender.Scene(ambient_light=[0.3, 0.3, 0.3])
            scene.add(mesh_pr)

            # compute camera position from spherical coordinates
            az = np.radians(self._azimuth)
            el = np.radians(self._elevation)
            cx = self._distance * np.cos(el) * np.sin(az)
            cy = self._distance * np.sin(el)
            cz = self._distance * np.cos(el) * np.cos(az)
            camera_pose = _look_at(np.array([cx, cy, cz]), np.zeros(3))

            camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
            scene.add(camera, pose=camera_pose)

            # directional light from camera position
            light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
            scene.add(light, pose=camera_pose)

            renderer = pyrender.OffscreenRenderer(self.render_width, self.render_height)
            color, _ = renderer.render(scene)
            renderer.delete()

            img = Image.fromarray(color)
            self._update_display(img)
        except Exception:
            self._render_fallback()

    def _render_fallback(self) -> None:
        # software fallback using trimesh's built-in scene renderer
        try:
            scene = self._mesh.scene()
            az = np.radians(self._azimuth)
            el = np.radians(self._elevation)
            cx = self._distance * np.cos(el) * np.sin(az)
            cy = self._distance * np.sin(el)
            cz = self._distance * np.cos(el) * np.cos(az)
            scene.set_camera(angles=(el, 0, az), distance=self._distance)
            png = scene.save_image(
                resolution=(self.render_width, self.render_height), visible=False
            )
            img = Image.open(__import__("io").BytesIO(png))
            self._update_display(img)
        except Exception as e:
            print(f"render error: {e}")

    def _update_display(self, img: Image.Image) -> None:
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._photo = ctk_img
        self._canvas_label.configure(image=ctk_img)

    def _on_drag_start(self, event) -> None:
        self._drag_start = (event.x, event.y)

    def _on_drag(self, event) -> None:
        if self._drag_start is None or self._mesh is None:
            return
        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._azimuth += dx * 0.5
        self._elevation = np.clip(self._elevation - dy * 0.5, -89, 89)
        self._drag_start = (event.x, event.y)
        self._render()

    def _on_scroll(self, event) -> None:
        if self._mesh is None:
            return
        self._distance = np.clip(self._distance - event.delta * 0.001, 1.0, 6.0)
        self._render()

    def clear(self) -> None:
        self._mesh = None
        self._canvas_label.configure(image=None)
        self._photo = None
        self._placeholder.place(relx=0.5, rely=0.5, anchor="center")


def _look_at(eye: np.ndarray, target: np.ndarray) -> np.ndarray:
    # builds a 4x4 camera pose matrix looking from eye toward target
    up = np.array([0.0, 1.0, 0.0])
    forward = target - eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    if np.linalg.norm(right) < 1e-6:
        up = np.array([0.0, 0.0, 1.0])
        right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    pose = np.eye(4)
    pose[:3, 0] = right
    pose[:3, 1] = up
    pose[:3, 2] = -forward
    pose[:3, 3] = eye
    return pose
