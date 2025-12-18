import os
import json
import ctypes
import string
import shutil
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from tkinter import filedialog

MAC_SPECIFIC_FILES = ['.DS_Store', '.apdisk']
MAC_SPECIFIC_FOLDERS = ['.fseventsd', '.Spotlight-V100', '.Trashes', '.TemporaryItems', '.DocumentRevisions-V1', '.AppleDouble']

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mac_clean_config.json')

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data.get('path'), str):
                    return data.get('path')
                paths = data.get('paths', [])
                if paths and isinstance(paths[0], str):
                    return paths[0]
        except Exception:
            return ""
    return ""

def save_config(path):
    data = {'path': path if isinstance(path, str) else ""}
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def has_mac_markers(path):
    try:
        for n in MAC_SPECIFIC_FILES:
            if os.path.exists(os.path.join(path, n)):
                return True
        for n in MAC_SPECIFIC_FOLDERS:
            if os.path.exists(os.path.join(path, n)):
                return True
        for fn in os.listdir(path):
            if fn.startswith('._'):
                return True
    except Exception:
        return False
    return False

def get_removable_drive_roots():
    roots = []
    get_type = ctypes.windll.kernel32.GetDriveTypeW
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            t = get_type(root)
            if t == 2:
                roots.append(root)
            elif t == 3 and has_mac_markers(root):
                roots.append(root)
    return roots

def perform_clean(base_path):
    deleted_files = 0
    deleted_dirs = 0
    for root, dirs, files in os.walk(base_path, topdown=False):
        for file in files:
            if file in MAC_SPECIFIC_FILES or file.startswith('._'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    deleted_files += 1
                    print(f"已删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件 {file_path} 时出错: {e}")
        for dir_name in list(dirs):
            if dir_name in MAC_SPECIFIC_FOLDERS:
                dir_path = os.path.join(root, dir_name)
                try:
                    shutil.rmtree(dir_path)
                    deleted_dirs += 1
                    print(f"已删除文件夹: {dir_path}")
                except Exception as e:
                    print(f"删除文件夹 {dir_path} 时出错: {e}")
    return deleted_files, deleted_dirs

def clean_by_picker():
    picked = filedialog.askdirectory()
    if not picked:
        return
    f, d = perform_clean(picked)
    messagebox.showinfo("完成", f"清理完成\n文件: {f} 个\n文件夹: {d} 个")

def run_quick_clean(selected_var):
    targets = []
    p = selected_var.get().strip() if selected_var else ""
    if p:
        targets.append(p)
    removable = get_removable_drive_roots()
    targets.extend(removable)
    if not targets:
        messagebox.showinfo("提示", "未配置常用文件夹且未检测到移动磁盘")
        return
    total_f = 0
    total_d = 0
    for t in targets:
        if os.path.exists(t):
            f, d = perform_clean(t)
            total_f += f
            total_d += d
    msg_extra = ""
    if removable:
        msg_extra = "\n检测到移动磁盘: " + ", ".join(removable)
    messagebox.showinfo("完成", f"一键清理完成\n共删除文件: {total_f} 个\n共删除文件夹: {total_d} 个{msg_extra}")

root = tk.Tk()
root.title("Mac 文件清理工具")
try:
    style = ttk.Style()
    style.theme_use('vista')
except Exception:
    pass
root.geometry("326x156")
root.minsize(326, 156)
root.resizable(True, True)

frame = ttk.Frame(root, padding=(16, 12))
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="可选目录：").grid(row=0, column=0, sticky="w", padx=(0, 8))
selected_var = tk.StringVar()
saved_path = load_config()
if saved_path:
    selected_var.set(saved_path)
selected_entry = ttk.Entry(frame, width=50, textvariable=selected_var)
selected_entry.grid(row=0, column=1, sticky="we")
frame.columnconfigure(1, weight=1)

def pick_single():
    p = filedialog.askdirectory()
    if p:
        selected_var.set(p)
        save_config(p)

btn_pick = ttk.Button(frame, text="选择", command=pick_single)
btn_pick.grid(row=0, column=2, padx=(8, 0))

btn_quick = ttk.Button(frame, text="一键清理（移动设备 + 所选目录）", command=lambda: run_quick_clean(selected_var))
btn_quick.grid(row=1, column=0, columnspan=3, sticky="we", pady=(12, 6))

btn_pick_clean = ttk.Button(frame, text="选择任意目录并清理", command=clean_by_picker)
btn_pick_clean.grid(row=2, column=0, columnspan=3, sticky="we")

root.mainloop()
