#!python3
# -*- coding: utf-8 -*-
# author: yinkaisheng@foxmail.com
import os
import sys
import time
import shutil
from threading import Event
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from tkasyncframe import AsyncFrame, WidgetUtil
from typing import (Any, Callable, Dict, List, Sequence, Tuple)
import util


ANALYZE_NOTIFY_ID = 1
TIMER_DUMP = 1
DUMP_BIN_WINDBG = 1
DUMP_BIN_CDB = 2
ExePath = os.path.abspath(sys.argv[0])
ExeDir, ExeNameWithExt = os.path.split(ExePath)
ExeNameNoExt = ExeNameWithExt.split('.')[0]
ConfigPath = os.path.join(ExeDir, f'{ExeNameWithExt}.config')


class MainFrame(AsyncFrame, WidgetUtil):
    def __init__(self, parent):
        super().__init__(parent)
        self.started = False
        self.dir_name = os.path.splitext(os.path.split(__file__)[1])[0]
        self.user_data_dir = os.path.expandvars('%appdata%\\' + self.dir_name)
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
        self.get_version_bat_path = os.path.join(self.user_data_dir, 'cdb_get_version.bat')
        self.get_version_result_path = os.path.join(self.user_data_dir, 'cdb_get_version_result.txt')
        self.get_stack_bat_path = os.path.join(self.user_data_dir, 'cdb_get_stack.bat')
        self.cdb_get_stack_path = os.path.join(self.user_data_dir, 'cdb_get_stack.txt')
        self.cdb_get_stack_result_path = os.path.join(self.user_data_dir, 'cdb_get_stack_result.txt')
        self.stop_event = Event()
        self.windbg_dir_var = tk.StringVar()
        self.dump_bin_var = tk.StringVar()
        self.nt_symbol_var = tk.StringVar()
        self.wow64exts_var = tk.BooleanVar()
        self.src_path_var = tk.StringVar()
        self.dst_path_var = tk.StringVar()
        script_dir = os.path.dirname(__file__)
        if script_dir:
            os.chdir(script_dir)
        self.pack(expand=True, fill=tk.BOTH)
        self.init_ui()
        self.master.protocol("WM_DELETE_WINDOW", self.close)

    def init_ui(self):
        self.master.title('WindowsDump快速分析工具')
        self.pack(fill=tk.BOTH, expand=1)
        self.centerWindow(0.6, 0.5)
        self.master.minsize(600, 400)

        debug_frame = ttk.Frame(self)
        debug_frame.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        debug_label = ttk.Label(debug_frame, text='WinDbg Dir:')
        debug_label.pack(side=tk.LEFT)
        tk.Radiobutton(debug_frame, text='windbg.exe', variable=self.dump_bin_var, value='windbg.exe').pack(side=tk.RIGHT)
        tk.Radiobutton(debug_frame, text='cdb.exe', variable=self.dump_bin_var, value='cdb.exe').pack(side=tk.RIGHT)
        self.dump_bin_var.set('windbg.exe')
        self.windbg_entry = ttk.Entry(debug_frame, textvariable=self.windbg_dir_var)
        self.windbg_entry.pack(fill=tk.X, expand=1, padx=4)

        symbol_frame = ttk.Frame(self)
        symbol_frame.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        symbo_label = ttk.Label(symbol_frame, text='_NT_SYMBOL_PATH:')
        symbo_label.pack(side=tk.LEFT)
        self.wow64exts_check = ttk.Checkbutton(symbol_frame, text='wow64exts', variable=self.wow64exts_var)
        self.wow64exts_check.pack(side=tk.RIGHT)
        self.nt_symbol_entry = ttk.Entry(symbol_frame, textvariable=self.nt_symbol_var)
        self.nt_symbol_entry.pack(fill=tk.X, expand=1, padx=4)

        src_frame = ttk.Frame(self)
        src_frame.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        src_label = ttk.Label(src_frame, text='输入:')
        src_label.pack(side=tk.LEFT)
        self.open_dir_btn = ttk.Button(src_frame, text='打开目录', command=self.on_click_open_dir)
        self.open_dir_btn.pack(side=tk.RIGHT)
        self.open_file_btn = ttk.Button(src_frame, text='打开文件', command=self.on_click_open_file)
        self.open_file_btn.pack(side=tk.RIGHT)
        self.src_path_entry = ttk.Entry(src_frame, textvariable=self.src_path_var)
        self.src_path_entry.pack(fill=tk.X, expand=1, padx=4)

        dst_frame = ttk.Frame(self)
        dst_frame.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        dst_label = ttk.Label(dst_frame, text='输出:')
        dst_label.pack(side=tk.LEFT)
        self.start_btn = ttk.Button(dst_frame, text='开始', command=self.on_click_start)
        self.start_btn.pack(side=tk.RIGHT)
        self.dst_path_entry = ttk.Entry(dst_frame, textvariable=self.dst_path_var)
        self.dst_path_entry.pack(fill=tk.X, expand=1, padx=4)

        self.output_tip_label = ttk.Label(self, text='输出:')
        self.output_tip_label.pack(side=tk.TOP)

        self.output_entry = ScrolledText(self, wrap=tk.WORD)
        self.output_entry.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.config = util.jsonFromFile(ConfigPath)
        self.windbg_dir_var.set(self.config['windbg_dir'])
        self.nt_symbol_var.set(self.config['symbols_dir'])

    def init_bat(self):
        if self.wow64exts_var.get():
            load_wow64exts = '.load wow64exts\n!wow64exts.sw\n.echo'
        else:
            load_wow64exts = ''
        cdb_get_stack_text = f'''
.logopen {self.cdb_get_stack_result_path}

.echo
.effmach
.echo

.symopt+0x10
.lines -e
.echo

{load_wow64exts}

.echo "dump context:"
.ecxr
.echo

.echo "dump type:"
.lastevent
.echo

.echo "crash module:"
lm a eip
.echo

.echo "dump register:"
r
.echo

.echo "dump stack:"
kL
.echo

.logclose'''
        prev_get_stack_text = util.getFileText(self.cdb_get_stack_path, encoding='ansi')
        if prev_get_stack_text != cdb_get_stack_text:
            util.writeTextFile(self.cdb_get_stack_path, cdb_get_stack_text, encoding='ansi')

    def close(self):
        self.master.destroy()

    def on_click_open_file(self):
        dmp_path = filedialog.askopenfilename(title='选择dmp文件', filetypes=[('dmp', '*.dmp'), ('All Files', '*')], initialdir='')
        if dmp_path:
            dmp_path = dmp_path.replace('/', '\\')
            self.src_path_var.set(dmp_path)
            self.dst_path_var.set(os.path.dirname(dmp_path) + '\\dump_result.txt')
            self.clearEntry(self.output_entry)
            output = self.cdb_get_version(dmp_path)
            self.appendEntryText(self.output_entry, '{}\n\n{}\n\n----\n\n'.format(dmp_path, output))

    def on_click_open_dir(self):
        file_dir = filedialog.askdirectory(title='选择dmp目录')
        if file_dir:
            file_dir = file_dir.replace('/', '\\')
            self.src_path_var.set(file_dir)
            self.dst_path_var.set(file_dir + '\\dump_result.txt')

    def on_click_start(self):
        if not self.started:
            src_path = self.src_path_var.get()
            dst_path = self.dst_path_var.get()
            symbol_path = self.nt_symbol_var.get()
            if not os.path.exists(src_path):
                return
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            self.init_bat()
            self.runInThread(self.analyze_func, (self.stop_event, src_path, dst_path, symbol_path), self.analyze_dump_notify)
            self.start_btn.config(text='停止')
            self.started = True
            # self.clearEntry(self.output_entry)
            self.startTimer(TIMER_DUMP, 200, self.on_timer)
        else:
            self.stop_event.set()

    def analyze_dump_notify(self, thread_id: int, notify_id: int, args: Any):
        if notify_id == ANALYZE_NOTIFY_ID:
            dmp_path, output = args
            output = f'{dmp_path}\n\n{output}\n\n====\n\n'
            self.appendEntryText(self.output_entry, output)

        elif notify_id == AsyncFrame.NotifyID_ThreadExit:
            self.start_btn.config(text='开始')
            self.output_tip_label.config(text='输出:')
            self.appendEntryText(self.output_entry, '----\nDone\n')
            self.stop_event.clear()
            self.stopTimer(TIMER_DUMP)
            self.started = False
        else:
            pass

    def analyze_func(self, threadId: int, args: Any):
        stop_event, src_dir, dst_path, symbol_path = args
        if os.path.isfile(src_dir):
            dmp_file = src_dir
            output = self.cdb_get_stack(dmp_file, symbol_path)
            self.threadNotifyUI(threadId, ANALYZE_NOTIFY_ID, (dmp_file, output))
            util.appendTextFile(f'{dmp_file}\n\n{output}\n\n====\n\n', dst_path, 'ansi')
        else:
            for filePath, isDir, fileName, depth, remainCount in util.walkDir(src_dir, maxDepth=1):
                if stop_event.is_set():
                    break
                if not isDir and filePath[-4:].lower() == '.dmp':
                    output = self.cdb_get_stack(filePath, symbol_path)
                    self.threadNotifyUI(threadId, ANALYZE_NOTIFY_ID, (filePath, output))
                    util.appendTextFile(f'{filePath}\n\n{output}\n\n====\n\n', dst_path, encoding='ansi')

    def cdb_get_version(self, dmp_path: str) -> str:
        dump_bin_path = os.path.join(self.windbg_dir_var.get(), self.dump_bin_var.get())
        lmvm_text = ';'.join('lmv m ' + it for it in self.config['binaries'])
        bat = f'''
set _NT_SYMBOL_PATH=C:\\Symbols;{os.path.dirname(dmp_path)}
"{dump_bin_path}" -z "{dmp_path}" -c ".logopen {self.get_version_result_path};{lmvm_text};.echo;.effmach;.logclose;q"
'''
        util.writeTextFile(self.get_version_bat_path, bat, encoding='ansi')
        ret = os.system(self.get_version_bat_path)
        content = util.getFileText(self.get_version_result_path, encoding='ansi')
        output = '\n'.join(content.splitlines()[1:-1])
        return output

    def cdb_get_stack(self, dmp_path: str, symbol_path: str) -> str:
        dump_bin_path = os.path.join(self.windbg_dir_var.get(), self.dump_bin_var.get())
        bat = f'''
set _NT_SYMBOL_PATH={symbol_path}
echo _NT_SYMBOL_PATH=%_NT_SYMBOL_PATH%
"{dump_bin_path}" -z "{dmp_path}" -c "$$><{self.cdb_get_stack_path};q"
'''
        util.writeTextFile(self.get_stack_bat_path, bat, encoding='ansi')
        ret = os.system(self.get_stack_bat_path)
        content = util.getFileText(self.cdb_get_stack_result_path, encoding='ansi')
        output = '\n'.join(content.splitlines()[1:-1])
        return output

    def on_timer(self, timerId: int, callCount: int, elapsedTime: float):
        self.output_tip_label.config(text='分析中:' + '.' * (callCount % 10))


def main():
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
