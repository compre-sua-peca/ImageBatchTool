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
    
class interfaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.criarWidgets()
        self.title("Espelhar Imagens")
        self.resizable(False, False)
        self.processing = False

    def criarWidgets(self):
        pad={'padx':10, 'pady':10}
        frm=ttk.Frame(self)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Pasta de entrada:").grid(row=0, column=0, sticky="w", **pad)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(frm, textvariable=self.input_var, width=50)
        self.input_entry.grid(row=1, column=0, columnspan=2, sticky="w", **pad)
        ttk.Button(frm, text="Selecionar...", command=self.selectInput).grid(row=1, column=2, **pad)
        # Output folder
        ttk.Label(frm, text="Pasta de saída:").grid(row=2, column=0, sticky="w", **pad)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(frm, textvariable=self.output_var, width=50)
        self.output_entry.grid(row=3, column=0, columnspan=2, sticky="w", **pad)
        ttk.Button(frm, text="Selecionar...", command=self.selectOutput).grid(row=3, column=2, **pad)
        # Options
        self.recursive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Recursivo (subpastas)", variable=self.recursive_var).grid(
            row=4, column=0, sticky="w", **pad
            )
        self.operation_var = tk.StringVar(value="rotate")
        ttk.Label(frm, text="Operação: ").grid(
            row=4, column=1, sticky="e", **pad
        )
        ttk.Radiobutton(
            frm,
            text="Girar 180°",
            variable=self.operation_var,
            value="rotate",
        ).grid(row=5, column=1, sticky="w", **pad)
        ttk.Radiobutton(
            frm,
            text="Espelhar Horizontalmente",
            variable=self.operation_var,
            value="mirror"
        ).grid(row=5, column=2, stick="w", **pad)
        # Progress bar
        ttk.Label(frm, text="Progresso:").grid(row=5, column=0, sticky="w", **pad)
        self.progress = ttk.Progressbar(frm, length=420, mode="determinate")
        self.progress.grid(row=6, column=0, columnspan=3, sticky="w", **pad)
        # Status
        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(frm, textvariable=self.status_var).grid(row=7, column=0, columnspan=3, sticky="w", **pad)
        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=8, column=0, columnspan=3, sticky="e", **pad)
        self.start_btn = ttk.Button(btn_frame, text="Iniciar", command=self.startProcessing)
        self.start_btn.grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="Fechar", command=self.onClose).grid(row=0, column=1, padx=4)


    def applyOperation(self, input_path: Path, output_path: Path):
        from PIL import Image
        op = self.operation_var.get()
        try:
            with Image.open(input_path) as im:
                if op == "rotate":
                    out_img = im.rotate(180)
                else:
                    out_img = im.transpose(Image.FLIP_LEFT_RIGHT)
                if out_img.mode not in ("RGB", "RGBA", "L"):
                    out_img = out_img.convert("RGB")
                out_img = out_img.save(output_path)
            return True, None
        except Exception as e:
            return False, str(e)
    def selectInput(self):
        folder=filedialog.askdirectory(title="Selecione a pasta de entrada")
        if folder:
            self.input_var.set(folder)
            # if not self.output_var.get():
            #     p = Path(folder)
            #     default_out=str(p.parent / (p.name + "_invertidos"))
            #     self.output_var.set(default_out)

    def selectOutput(self):
            folder = filedialog.askdirectory(title="Selecione a pasta de Saida")
            if folder:
                self.output_var.set(folder)
    
    def startProcessing(self):
        if self.processing:
            return
        input_path = self.input_var.get().strip()
        if not input_path:
            messagebox.showerror("Selecione a pasta de Entrada.")
            return
        input_folder = Path(input_path)
        if not input_folder.exists() or not input_folder.is_dir():
            messagebox.showerror("Pasta de entrada inválida.")
            return
        
        output_path = self.output_var.get().strip()
        if output_path:
            output_folder = Path(output_path)
        else:
            output_folder=input_folder.parent / (input_folder.name)
        recursive = self.recursive_var.get()
        overwrite = False

        try:
            output_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possivel criar a pasta de saida")
            return
        
        files = listarArquivos(input_folder, recursive)
        if not files:
            messagebox.showinfo("Nenhuma imagem encontrada")
        
        self.progress['maximum'] = len(files)
        self.progress['value'] = 0
        self.status_var.set(f"Preparando... 0/{len(files)}")
        self.processing = True
        self.start_btn.config(state="disabled")

        thread = threading.Thread(target=self.processFiles, args=(files, input_folder, output_folder, overwrite), daemon=True)
        thread.start()

    def processFiles(self, files, input_folder: Path, output_folder: Path, overwrite: bool):
        total = len(files)
        success = 0
        skipped = 0
        errors = []

        for i, p in enumerate(files, start=1):
            try:
                relative = p.relative_to(input_folder)
            except Exception:
                relative = Path(p.name)
            out_name = p.stem + p.suffix
            subdir = output_folder / relative.parent
            subdir.mkdir(parents=True, exist_ok=True)
            out_path = subdir / out_name

            if out_path.exists() and not overwrite:
                skipped += 1
            else:
                ok, err = self.applyOperation(p, out_path)
                if ok:
                    success += 1
                else:
                    errors.append((str(p), err))
            self.after(0, self.updateProgress, i, total, success, skipped)
        self.after(0, self.finishProcessing, total, success, skipped, errors)

    def updateProgress(self, current, total, success, skipped):
        self.progress['value'] = current
        self.progress.update_idletasks() 
        self.status_var.set(f"Precessando {current}/{total} (sucesso: {success} pulados: {skipped})")
    
    def finishProcessing(self, total, success, skipped, errors):
        self.processing=False
        self.start_btn.config(state="normal")
        self.progress['value'] = total
        summary = f"Concluído: {total} processados, {skipped} pulados, {len(errors)} erros."
        self.status_var.set(summary)
        if errors:
            msg = summary + "\n\nErros (amostra):\n" + "\n".join(f"{Path(f).name}: {e}" for f, e in errors[:10])
            messagebox.showwarning("Concluído", summary)

    def onClose(self):
        if self.processing:
            if not messagebox.askyesno("Sair", "Processamento em andamento."):
                return
        self.destroy()

if __name__== "__main__":
    app = interfaceApp()
    app.mainloop()