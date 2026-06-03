import sys
from pathlib import Path
from PIL import Image
import torch


# add vendor/TripoSR to path so tsr can be imported without pip install
_vendor_path = Path(__file__).parent.parent / "vendor" / "TripoSR"
if str(_vendor_path) not in sys.path:
    sys.path.insert(0, str(_vendor_path))


# model instance kept in memory after first load
_model = None
_device = None


def _get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def load_model(on_progress=None):
    # loads triposr weights from huggingface hub (cached after first download)
    global _model, _device
    if _model is not None:
        return _model

    from tsr.system import TSR

    _device = _get_device()
    if on_progress:
        on_progress("Downloading model weights (first run only)...")

    _model = TSR.from_pretrained(
        "stabilityai/TripoSR",
        config_name="config.yaml",
        weight_name="model.ckpt",
    )
    _model.renderer.set_chunk_size(8192)
    _model.to(_device)
    return _model


def run_inference(
    image_path: str | Path,
    output_path: str | Path,
    export_format: str = "obj",
    mc_resolution: int = 128,
    on_progress=None,
) -> Path:
    # runs triposr on a preprocessed rgba image and exports the 3d mesh
    model = load_model(on_progress=on_progress)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if on_progress:
        on_progress("Preparing input image...")

    img = Image.open(image_path).convert("RGBA")

    # composite on white background for model input (expects rgb)
    background = Image.new("RGB", img.size, (255, 255, 255))
    background.paste(img, mask=img.split()[3])
    rgb = background

    if on_progress:
        on_progress("Running 3D inference...")

    with torch.no_grad():
        scene_codes = model([rgb], device=_device)

    if on_progress:
        on_progress("Extracting mesh...")

    meshes = model.extract_mesh(scene_codes, resolution=mc_resolution)
    mesh = meshes[0]

    if on_progress:
        on_progress(f"Exporting mesh as .{export_format}...")

    mesh.export(str(output_path))
    return output_path
