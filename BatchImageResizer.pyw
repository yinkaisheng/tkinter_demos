#!python3
# -*- coding: utf-8 -*-
#author: yinkaisheng@foxmail.com
import os
import sys
import time
import shutil
from threading import Event
from PIL import Image
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkasyncframe import AsyncFrame

RESIZE_NOTIFY_ID = 1

ImgMode = {
    '.png': 'RGBA',
    '.jpg': 'RGB',
    '.tiff': 'RGB',
    '.bmp': 'RGB',
    '.gif': 'P',
}

class MainFrame(AsyncFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.started = False
        self.stop_event = Event()
        self.src_path_var = tk.StringVar()
        self.dst_path_var = tk.StringVar()
        self.src_ext_var = tk.StringVar()
        self.src_ext_var.set('.jpg .jpeg .png .bmp .tif .tiff')
        self.dst_ext_var = tk.StringVar()
        self.dst_ext_var.set('.png')
        self.side_var = tk.StringVar()
        self.side_var.set(1920)
        self.rotate_var = tk.StringVar()
        self.rotate_var.set('0')
        self.flip_left_right_var = tk.BooleanVar()
        self.flip_top_bottom_var = tk.BooleanVar()
        script_dir = os.path.dirname(__file__)
        if script_dir:
            os.chdir(script_dir)
        self.pack(expand = True, fill = tk.BOTH)
        self.init_ui()
        self.master.protocol("WM_DELETE_WINDOW", self.close)

    def init_ui(self):
        self.master.title('Batch Image Resizer by yinkaisheng')
        self.pack(fill = tk.BOTH, expand = 1)
        self.centerWindow(600, 0.5)
        self.master.minsize(600, 400)

        src_frame = ttk.Frame(self)
        src_frame.pack(side = tk.TOP, fill = tk.X, padx = 4, pady = 4)
        src_label = ttk.Label(src_frame, text = 'Pictures Folder:')
        src_label.pack(side = tk.LEFT)
        self.open_btn = ttk.Button(src_frame, text = 'Open...', command = self.on_click_open)
        self.open_btn.pack(side = tk.RIGHT)
        self.src_path_entry = ttk.Entry(src_frame, textvariable = self.src_path_var)
        self.src_path_entry.pack(fill = tk.X, expand = 1, padx = 4)

        dst_frame = ttk.Frame(self)
        dst_frame.pack(side = tk.TOP, fill = tk.X, padx = 4, pady = 4)
        dst_label = ttk.Label(dst_frame, text = 'Output Folder:')
        dst_label.pack(side = tk.LEFT)
        self.start_btn = ttk.Button(dst_frame, text = 'Start', command = self.on_click_start)
        self.start_btn.pack(side = tk.RIGHT)
        self.dst_path_entry = ttk.Entry(dst_frame, textvariable = self.dst_path_var)
        self.dst_path_entry.pack(fill = tk.X, expand = 1, padx = 4)

        format_frame = ttk.Frame(self)
        format_frame.pack(side = tk.TOP, fill = tk.X, padx = 4, pady = 4)
        src_ext_label = ttk.Label(format_frame, text = 'Only Convert the Following Formats:')
        src_ext_label.pack(side = tk.LEFT)
        self.ext_entry = ttk.Entry(format_frame, textvariable = self.src_ext_var, width = 30)
        self.ext_entry.pack(side = tk.LEFT)
        dst_ext_label = ttk.Label(format_frame, text = ' Output Format:')
        dst_ext_label.pack(side = tk.LEFT)
        self.dst_ext_combo = ttk.Combobox(format_frame, textvariable = self.dst_ext_var, state = 'readonly', width = 10)
        self.dst_ext_combo['values'] = ['.png', '.jpg', '.gif', '.tiff', '.bmp', 'Doesn\'t Change']
        self.dst_ext_combo.pack(side = tk.LEFT)

        transform_frame = ttk.Frame(self)
        transform_frame.pack(side = tk.TOP, fill = tk.X, padx = 4, pady = 4)
        size_label = ttk.Label(transform_frame, text = 'Max Width or Height:')
        size_label.pack(side = tk.LEFT)
        self.side_entry = ttk.Entry(transform_frame, textvariable = self.side_var, width = 6)
        self.side_entry.pack(side = tk.LEFT)
        rotate_label = ttk.Label(transform_frame, text = ' Rotate:')
        rotate_label.pack(side = tk.LEFT)
        self.rotate_combo = ttk.Combobox(transform_frame, textvariable = self.rotate_var, state = 'readonly', width = 4)
        self.rotate_combo['values'] = ['0', '90', '180', '270']
        self.rotate_combo.pack(side = tk.LEFT)
        self.flip_lr_check = ttk.Checkbutton(transform_frame, text = 'Horizontal Flip', variable = self.flip_left_right_var)
        self.flip_lr_check.pack(side = tk.LEFT, padx = 4)
        self.flip_tb_check = ttk.Checkbutton(transform_frame, text = 'Vertical Flip', variable = self.flip_top_bottom_var)
        self.flip_tb_check.pack(side = tk.LEFT, padx = 4)

        ttk.Label(self, text = 'Output:').pack(side = tk.TOP)

        self.output_entry = ScrolledText(self, wrap = tk.WORD)
        self.output_entry.pack(side = tk.TOP, fill = tk.BOTH, expand = True)

    def close(self):
        self.master.destroy()

    def on_click_open(self):
        imgdir = filedialog.askdirectory()
        if imgdir:
            self.src_path_var.set(imgdir)
            self.dst_path_var.set(imgdir + '_resized_output')

    def on_click_start(self):
        if not self.started:
            src_path = self.src_path_var.get()
            dst_path = self.dst_path_var.get()
            if not os.path.exists(src_path):
                return
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)
            max_side = int(self.side_var.get())
            src_exts = self.src_ext_var.get()
            dst_ext = self.dst_ext_var.get()
            rotate = int(self.rotate_var.get())
            flip_lr = self.flip_left_right_var.get()
            flip_tb = self.flip_top_bottom_var.get()
            self.runInThread(self.convert_func, (self.stop_event, src_path, dst_path, src_exts, dst_ext, max_side, rotate, flip_lr, flip_tb), self.convert_notify)
            self.start_btn.config(text = 'Stop')
            self.started = True
            self.clearEntry(self.output_entry)
        else:
            self.stop_event.set()

    def convert_notify(self, notify_id, args):
        if notify_id == RESIZE_NOTIFY_ID:
            self.appendEntryText(self.output_entry, args + '\n')
        elif notify_id == AsyncFrame.NotifyID_ThreadExit:
            self.start_btn.config(text = 'Start')
            self.appendEntryText(self.output_entry, '----\nDone\n')
            self.stop_event.clear()
            self.started = False
        else:
            pass

    def convert_func(self, threadId, args):
        stop_event, src_dir, dst_dir, src_exts, dst_ext, max_side, rotate, flip_lr, flip_tb = args
        files = os.listdir(src_dir)
        src_exts = src_exts.lower().split()
        for it in files:
            if stop_event.is_set():
                break
            name, ext = os.path.splitext(it)
            ext = ext.lower()
            if ext in src_exts:
                if not dst_ext.startswith('.'):
                    dst_ext = ext
                if src_dir == dst_dir:
                    newfile = name + '_resized' + dst_ext
                else:
                    newfile = name + dst_ext
                src_file = os.path.join(src_dir, it)
                dst_file = os.path.join(dst_dir, newfile)
                w, h, nw, nh = self.resize_image(src_file, ext, dst_file, dst_ext, max_side, rotate, flip_lr, flip_tb)
                info = '{}, {}x{} -> {}, {}x{}'.format(it, w, h, newfile, nw, nh)
                self.threadNotifyUI(threadId, RESIZE_NOTIFY_ID, info)

    def resize_image(self, src_path, src_ext, dst_path, dst_ext, max_side = 1920, rotate = 0, flip_lr = 0, flip_rb = 0):
        img = Image.open(src_path)
        width, height = img.size
        max_src = max(width, height)
        if os.path.exists(dst_path):
            os.remove(dst_path)
        newimg = img
        if max_src > max_side:
            if width > height:
                new_width = max_side
                new_height = int(height / (width / max_side))
            else:
                new_height = max_side
                new_width = int(width / (height / max_side))
            newimg = newimg.resize((new_width, new_height), Image.ANTIALIAS)
        else:
            new_width, new_height = width, height
        if rotate != 0:
            newimg = newimg.rotate(rotate, expand = True)
            if rotate // 90 % 2 == 1:
                new_width, new_height = new_height, new_width
        if flip_lr:
            newimg = newimg.transpose(Image.FLIP_LEFT_RIGHT)
        if flip_rb:
            newimg = newimg.transpose(Image.FLIP_TOP_BOTTOM)
        if src_ext != dst_ext:
            if newimg.mode != ImgMode[dst_ext]:
                newimg = newimg.convert(ImgMode[dst_ext])
        newimg.save(dst_path)
        del img
        del newimg
        return width, height, new_width, new_height

def main():
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
