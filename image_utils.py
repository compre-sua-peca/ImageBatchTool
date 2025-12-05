import threading
from pathlib import Path
from PIL import Image, ImageSequence
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
 

class ImageOperator():
    def __init__(self):
        self.IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'] 

    def _process_gif(self, gif, output_path):
        frames=[]
        info=gif.info
        for frame in ImageSequence.Iterator(gif):
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
        return frames

    def _mirror_image(self, input_path: Path, output_path: Path):
        try:
            with Image.open(input_path) as im:
                if getattr(im, "is_animated", True) and im.format == "GIF":
                    self._process_gif(im, output_path)

                if im.mode not in ("RGB", "RGBA", "L"):
                    im=im.convert("RGB")
                
                img = im.transpose(Image.FLIP_LEFT_RIGHT)
                img.save(output_path)

            return True, None
        except Exception as e:
            return False, str(e)


    def _apply_operation(self, input_path: Path, output_path: Path):
        op = self.operation_var.get()
        try:
            with Image.open(input_path) as im:
                if im.mode not in ("RGB", "RGBA", "L"):
                    im = im.convert("RGB")

                if op == "rotate":
                    out_img = im.rotate(180)
                else:
                    out_img = im.transpose(Image.FLIP_LEFT_RIGHT)

                out_img = out_img.save(output_path)
            return True, None

        except Exception as e:
            return False, str(e)


class InterfaceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.image_operator = ImageOperator()
        if not self.image_operator:
            raise Exception("ImageOperator not available")
        
        self._create_widgets()
        self.title("Espelhar Imagens")
        self.resizable(False, False)
        self.processing = False


    def _list_files(self, input_folder: Path, recursive: bool):
        if recursive:
            files=[p for p in input_folder.rglob("*") if p.is_file() and p.suffix.lower() in self.image_operator.IMAGE_EXTENSIONS]
        else:
            files=[p for p in input_folder.iterdir() if p.is_file() and p.suffix.lower() in self.image_operator.IMAGE_EXTENSIONS]
        return sorted(files)
   

    def _create_widgets(self):
        pad={'padx':10, 'pady':10}
        frm=ttk.Frame(self)
        frm.grid(row=0, column=0, sticky="nsew")

        ttk.Label(frm, text="Pasta de entrada:").grid(row=0, column=0, sticky="w", **pad)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(frm, textvariable=self.input_var, width=50)
        self.input_entry.grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        ttk.Button(frm, text="Selecionar...", command=self.select_input).grid(row=1, column=2, **pad)
        # Output folder
        ttk.Label(frm, text="Pasta de saída:").grid(row=2, column=0, sticky="w", **pad)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(frm, textvariable=self.output_var, width=50)
        self.output_entry.grid(row=3, column=0, columnspan=2, sticky="w", **pad)
        ttk.Button(frm, text="Selecionar...", command=self.select_output).grid(row=3, column=2, **pad)
        # Options
        self.recursive_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frm, text="Recursivo (subpastas)", variable=self.recursive_var).grid(
            row=4, column=0, sticky="w", **pad
            )
        self.operation_var = tk.StringVar(value="rotate")

        ttk.Label(frm, text="Operação: ").grid(
            row=4, column=1, sticky="w", **pad
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


    def select_input(self):
        folder=filedialog.askdirectory(title="Selecione a pasta de entrada")
        if folder:
            self.input_var.set(folder)


    def select_output(self):
            folder = filedialog.askdirectory(title="Selecione a pasta de Saida")
            if folder:
                self.output_var.set(folder)


    def _process_file(self, file, input_folder: Path, output_folder: Path, overwrite: bool):
        success = 0
        skipped = 0
        errors = []
        try:
                relative = file.relative_to(input_folder)
        except Exception:
                relative = Path(file.name)
        out_name = file.stem + file.suffix
        subdir = output_folder / relative.parent
        subdir.mkdir(parents=True, exist_ok=True)
        out_path = subdir / out_name

        if out_path.exists() and not overwrite:
            skipped += 1
        else:
            ok, err = self._apply_operation(file, out_path)
            if ok:
                success += 1
            else:
                errors.append((str(file), err))
        return success,skipped,errors
        

    def _process_files(self, files, input_folder: Path, output_folder: Path, overwrite: bool):
        total = len(files)
        success = 0
        skipped = 0
        errors = []

        for index, file in enumerate(files, start=1):
            success, skipped, errors = self._process_file(file, input_folder, output_folder, overwrite)
            errors.extend(errors)
            self.after(0, self._update_progress, index, total, success, skipped)

        self.after(0, self._finish_processing, total, success, skipped, errors)


    def _update_progress(self, current, total, success, skipped):
        self.progress['value'] = current
        self.progress.update_idletasks() 
        self.status_var.set(f"Precessando {current}/{total} (sucesso: {success} pulados: {skipped})")


    def _finish_processing(self, total, skipped, errors):
        self.processing=False
        self.start_btn.config(state="normal")
        self.progress['value'] = total
        summary = f"Concluído: {total} processados, {skipped} pulados, {len(errors)} erros."
        self.status_var.set(summary)
        if errors:
            messagebox.showwarning("Concluído", summary)


    def _on_close(self):
        if self.processing:
            if not messagebox.askyesno("Sair", "Processamento em andamento."):
                return
        self.destroy()
    

    def start_processing(self):
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
        
        files = self._list_files(input_folder, recursive)
        if not files:
            messagebox.showinfo("Nenhuma imagem encontrada")
        
        self.progress.get('maximum') = len(files)
        self.progress.get('value') = 0
        self.status_var.set(f"Preparando... 0/{len(files)}")
        self.processing = True
        self.start_btn.config(state="disabled")

        thread = threading.Thread(target=self._process_files, args=(files, input_folder, output_folder, overwrite), daemon=True)
        thread.start()


if __name__== "__main__":
    app = InterfaceApp()
    app.mainloop()