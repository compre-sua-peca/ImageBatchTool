import threading
from pathlib import Path
from PIL import Image, ImageSequence
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

imageExensions = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'] 

def listarArquivos(input_folder: Path, recursive: bool):
    if recursive:
        files=[p for p in input_folder.rglob("*") if p.is_file() and p.suffix.lower() in imageExensions]
    else:
        files=[p for p in input_folder.iterdir() if p.is_file() and p.suffix.lower() in imageExensions]
    return sorted(files)
def espelharImagem(input_path: Path, output_path: Path):
    try:
        with Image.open(input_path) as im:
            if getattr(im, "is_animated", False) and im.format == "GIF":
                frames=[]
                info=im.info
                for frame in ImageSequence.Iterator(im):
                    f=frame.convert("RGBA").transpose(Image.FLIP_LEFT_RIGHT)
                    frames.append(f)
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    loop=info.get("loop", 0),
                duration=info.get("disposal", 2),
                optimize=False,
                )
            else:
                img = im.transpose(Image.FLIP_LEFT_RIGHT)
                if img.mode not in ("RGB", "RGBA", "L"):
                    img=img.convert("RGB")
                img.save(output_path)
        return True, None
    except Exception as e:
        return False, str(e)
    
