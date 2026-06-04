from pathlib import Path
import trimesh


SUPPORTED_FORMATS = ["obj", "glb", "ply"]


def export_mesh(mesh_path: str | Path, output_path: str | Path) -> Path:
    # re-exports a mesh to a different format based on output_path extension
    output_path = Path(output_path)
    mesh = trimesh.load(str(mesh_path), force="mesh")
    mesh.export(str(output_path))
    return output_path
