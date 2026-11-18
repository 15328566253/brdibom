from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .app import RunOptions, generate_from_brd
from .cadence import locate_cadence
from .config import load_settings, save_settings
from .errors import Brd2IbomError


class Brd2IbomWindow:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("brd2ibom")
        self.root.geometry("760x560")
        self.board_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        saved = load_settings()
        self.cadence_root = tk.StringVar(value=str(saved.get("cadence_root", "")))
        self.cadence_exe = tk.StringVar(value=str(saved.get("cadence_exe", "")))
        self.status = tk.StringVar(value="请选择 Allegro .brd 文件")
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)

        ttk.Label(frame, text="BRD 文件").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)
        ttk.Entry(frame, textvariable=self.board_path).grid(row=0, column=1, sticky="ew", pady=8)
        ttk.Button(frame, text="选择", command=self._choose_board).grid(row=0, column=2, padx=(8, 0), pady=8)

        ttk.Label(frame, text="输出目录").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=8)
        ttk.Entry(frame, textvariable=self.output_dir).grid(row=1, column=1, sticky="ew", pady=8)
        ttk.Button(frame, text="选择", command=self._choose_output).grid(row=1, column=2, padx=(8, 0), pady=8)

        ttk.Label(frame, text="Cadence 路径").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=8)
        cadence_display = ttk.Entry(frame, textvariable=self.cadence_exe)
        cadence_display.grid(row=2, column=1, sticky="ew", pady=8)
        ttk.Button(frame, text="Cadence 设置", command=self._open_cadence_settings).grid(
            row=2, column=2, padx=(8, 0), pady=8
        )

        ttk.Button(frame, text="生成焊接辅助 HTML", command=self._generate).grid(
            row=3, column=0, columnspan=3, pady=(18, 12)
        )
        ttk.Label(frame, textvariable=self.status, wraplength=700).grid(
            row=4, column=0, columnspan=3, sticky="w"
        )

        log_header = ttk.Frame(frame)
        log_header.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(16, 6))
        log_header.columnconfigure(0, weight=1)
        ttk.Label(log_header, text="运行日志").grid(row=0, column=0, sticky="w")
        ttk.Button(log_header, text="清空", command=self._clear_log).grid(row=0, column=1, sticky="e")
        self.log_text = ScrolledText(frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=6, column=0, columnspan=3, sticky="nsew")

        if self.cadence_exe.get():
            self.status.set(f"已设置 Allegro：{self.cadence_exe.get()}")
        elif self.cadence_root.get():
            self.status.set(f"已设置 Cadence 根目录：{self.cadence_root.get()}")

    def _choose_board(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Cadence Allegro BRD", "*.brd"), ("All files", "*.*")])
        if path:
            self.board_path.set(path)
            if not self.output_dir.get():
                self.output_dir.set(str(Path(path).parent / "ibom"))

    def _choose_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir.set(path)

    def _open_cadence_settings(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Cadence 路径设置")
        dialog.geometry("700x230")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.columnconfigure(1, weight=1)

        root_var = tk.StringVar(value=self.cadence_root.get())
        exe_var = tk.StringVar(value=self.cadence_exe.get())
        result_var = tk.StringVar(value="可以填写安装根目录，或者直接填写 allegro.exe")

        ttk.Label(dialog, text="安装根目录").grid(row=0, column=0, sticky="w", padx=14, pady=10)
        ttk.Entry(dialog, textvariable=root_var).grid(row=0, column=1, sticky="ew", padx=6, pady=10)

        def choose_root() -> None:
            path = filedialog.askdirectory(parent=dialog, title="选择 Cadence 安装根目录")
            if path:
                root_var.set(path)
                exe_var.set("")

        ttk.Button(dialog, text="选择目录", command=choose_root).grid(row=0, column=2, padx=14, pady=10)

        ttk.Label(dialog, text="allegro.exe").grid(row=1, column=0, sticky="w", padx=14, pady=10)
        ttk.Entry(dialog, textvariable=exe_var).grid(row=1, column=1, sticky="ew", padx=6, pady=10)

        def choose_exe() -> None:
            path = filedialog.askopenfilename(
                parent=dialog,
                title="选择 allegro.exe",
                filetypes=[("Allegro executable", "allegro*.exe"), ("All files", "*.*")],
            )
            if path:
                exe_var.set(path)
                root_var.set("")

        ttk.Button(dialog, text="选择文件", command=choose_exe).grid(row=1, column=2, padx=14, pady=10)

        def auto_scan() -> None:
            try:
                installation = locate_cadence()
            except Brd2IbomError as exc:
                result_var.set(str(exc))
                return
            root_var.set(str(installation.root))
            exe_var.set(str(installation.executable))
            result_var.set(f"扫描成功：{installation.executable}")

        ttk.Button(dialog, text="自动扫描", command=auto_scan).grid(row=2, column=2, padx=14, pady=4)
        ttk.Label(dialog, textvariable=result_var, wraplength=650).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=14, pady=(4, 12)
        )

        def validate() -> None:
            try:
                installation = locate_cadence(
                    root=root_var.get().strip() or None,
                    executable=exe_var.get().strip() or None,
                )
            except Brd2IbomError as exc:
                result_var.set(str(exc))
                return
            result_var.set(f"检测成功：{installation.executable}")

        def save() -> None:
            validate()
            try:
                installation = locate_cadence(
                    root=root_var.get().strip() or None,
                    executable=exe_var.get().strip() or None,
                )
            except Brd2IbomError:
                return
            self.cadence_root.set(str(installation.root))
            self.cadence_exe.set(str(installation.executable))
            save_settings({"cadence_root": str(installation.root), "cadence_exe": str(installation.executable)})
            self.status.set(f"已设置 Allegro：{installation.executable}")
            dialog.destroy()

        buttons = ttk.Frame(dialog)
        buttons.grid(row=4, column=0, columnspan=3, pady=8)
        ttk.Button(buttons, text="检测", command=validate).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _clear_log(self) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _log_from_worker(self, message: str) -> None:
        self.root.after(0, self._append_log, message)

    def _generate(self) -> None:
        board = self.board_path.get().strip()
        if not board:
            messagebox.showwarning("brd2ibom", "请先选择 .brd 文件")
            return
        self._clear_log()
        self._append_log(f"开始处理：{board}")
        options = RunOptions(
            output_dir=Path(self.output_dir.get()) if self.output_dir.get() else None,
            cadence_root=Path(self.cadence_root.get()) if self.cadence_root.get() else None,
            cadence_exe=Path(self.cadence_exe.get()) if self.cadence_exe.get() else None,
        )
        self.status.set("正在启动 Allegro 并导出数据，请稍候…")
        threading.Thread(target=self._run, args=(Path(board), options), daemon=True).start()

    def _run(self, board: Path, options: RunOptions) -> None:
        try:
            results = generate_from_brd(board, options, log_callback=self._log_from_worker)
        except Brd2IbomError as exc:
            message = str(exc)
            self.root.after(0, self._append_log, f"错误：{message}")
            self.root.after(0, self._show_error, message)
            return
        self.root.after(0, lambda: self.status.set("生成完成：\n" + "\n".join(str(path) for path in results)))
        self.root.after(0, self._append_log, "处理完成")

    def _show_error(self, message: str) -> None:
        self.status.set("生成失败")
        messagebox.showerror("brd2ibom", message)

    def run(self) -> None:
        self.root.mainloop()


def run_gui() -> None:
    Brd2IbomWindow().run()

