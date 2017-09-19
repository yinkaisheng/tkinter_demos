#!python3
# -*- coding: utf-8 -*-
#author: yinkaisheng@foxmail.com
import os
import sys
import time
import json
import queue
import pickle
import traceback
from threading import Thread
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

try:
    import requests
except Exception as ex:
    rst = input('You need to install requests first! Press Enter to install it. Press q to exit.')
    if rst == 'q' or rst == 'Q':
        sys.exit(0)
    print('pip install requests')
    rst = os.system('pip install requests')
    if rst == 0:
        import subprocess
        sys.argv.insert(0, 'python')
        subprocess.Popen(sys.argv)
    sys.exit(0)

ISO_TIME_FORMAT = '%Y-%m-%d %X'
HEADER_TEXT_HEIGHT = 8


class HttpRequest():
    def __init__(self):
        self.time = ''
        self.url = ''
        self.proxy = ()
        self.proxy_dict = {}
        self.request_header = ''
        self.request_header_dict = {}
        self.request_data = ''
        self.real_url = ''
        self.response_header = ''
        self.response_header_dict = {}
        self.response_data = ''
        self.response_json = ''
        self.response_code = ''
        self.response_time = 0
        self.exception = None
        self.timeout = 60


class Util():
    @staticmethod
    def header_2_dict(header, header_dict = None):
        headers = header.splitlines()
        if header_dict is None:
            header_dict = {}
        for it in headers:
            item = it.split(':')
            if len(item) == 2:
                header_dict[item[0].strip()] = item[1].strip()
        return header_dict

    @staticmethod
    def dict_2_header(header_dict):
        header = ''
        for key in header_dict:
            header += "%s: %s\r\n" % (key, header_dict[key])
        return header


class MainFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.history_var = tk.StringVar()
        self.url_var = tk.StringVar()
        self.json_format_var = tk.BooleanVar()
        self.proxy_var = tk.StringVar()
        self.timeout_var = tk.StringVar()
        self.quene = queue.Queue()
        self.http_item = HttpRequest()
        self.http_items = []
        self.history_file = 'history.dat'
        script_dir = os.path.dirname(__file__)
        if script_dir:
            os.chdir(script_dir)

        if os.path.exists(self.history_file):
            self.http_items = pickle.load(open(self.history_file, 'rb'))

        self.pack(expand = True, fill = tk.BOTH)
        self.init_ui()

        self.master.protocol("WM_DELETE_WINDOW", self.close)

    def init_ui(self):
        self.master.title('HttpRequester')
        self.pack(fill = tk.BOTH, expand = 1)
        self.center_window()

        history_frame = ttk.Frame(self)
        history_frame.pack(fill = tk.X, padx = 4, pady = 4)
        ttk.Label(history_frame, text = 'History:', width = 8).pack(side = tk.LEFT)
        ttk.Button(history_frame, text = 'ClearHistory', command = self.clear_history).pack(side = tk.RIGHT)
        self.history_combo = ttk.Combobox(history_frame, textvariable = self.history_var, state = 'readonly')
        self.history_combo.bind("<<ComboboxSelected>>", self.history_select)
        self.history_combo['values'] = ()
        self.history_combo.pack(fill = tk.X, expand = 1, padx = 4)

        url_frame = ttk.Frame(self)
        url_frame.pack(fill = tk.X, padx = 4, pady = 4)
        ttk.Label(url_frame, text = 'URL:', width = 8).pack(side = tk.LEFT)
        self.send_btn = ttk.Button(url_frame, text = 'Send', command = self.send)
        self.send_btn.pack(side = tk.RIGHT)
        self.url_entry = ttk.Entry(url_frame, textvariable = self.url_var)
        self.url_entry.pack(fill = tk.X, expand = 1, padx = 4)

        config_frame = ttk.Frame(self)
        config_frame.pack(fill = tk.X, padx = 4, pady = 4)
        self.time_label = ttk.Label(config_frame, text = '')
        self.time_label.pack(side = tk.RIGHT)
        self.timeout_var.set('10')
        self.timeout_entry = ttk.Entry(config_frame, textvariable = self.timeout_var, width = 4)
        self.timeout_entry.pack(side = tk.RIGHT)
        ttk.Label(config_frame, text = 'Timeout:').pack(side = tk.RIGHT)
        self.proxy_entry = ttk.Entry(config_frame)
        self.proxy_entry.pack(side = tk.RIGHT)
        self.proxy_combo = ttk.Combobox(config_frame, textvariable = self.proxy_var, state = 'readonly', width = 4)
        self.proxy_combo.pack(side = tk.RIGHT, padx = 4)
        self.proxy_combo['values'] = ('http', 'https')
        self.proxy_combo.current(0)
        ttk.Label(config_frame, text = 'Proxy:').pack(side = tk.RIGHT)

        data_frame = ttk.Frame(self)
        data_frame.pack(fill = tk.BOTH, expand = 1, padx = 4, pady = 4)
        data_frame.columnconfigure(0, weight = 1)
        data_frame.columnconfigure(4, weight = 1)
        data_frame.rowconfigure(3, weight = 1)

        ttk.Label(data_frame, text = 'RequestHeader:').grid(row = 0, column = 0, stick = tk.W)
        ttk.Label(data_frame, text = 'ResponsetHeader:').grid(row = 0, column = 4, stick = tk.W)
        self.request_header_entry = ScrolledText(data_frame, height = HEADER_TEXT_HEIGHT)
        self.request_header_entry.grid(row = 1, column = 0, columnspan = 4, stick = tk.NSEW)

        self.response_header_entry = ScrolledText(data_frame, height = HEADER_TEXT_HEIGHT)
        self.response_header_entry.grid(row = 1, column = 4, columnspan = 4, stick = tk.NSEW)

        ttk.Label(data_frame, text = 'RequestData:').grid(row = 2, column = 0, stick = tk.W)
        ttk.Label(data_frame, text = 'ResponsetData:').grid(row = 2, column = 4, stick = tk.W)

        self.json_check = ttk.Checkbutton(data_frame, text = 'JsonFormat', variable = self.json_format_var, command = self.format_json)
        self.json_check.grid(row = 2, column = 5, stick = tk.W)
        self.request_data_entry = ScrolledText(data_frame, wrap = tk.WORD)
        self.request_data_entry.grid(row = 3, column = 0, columnspan = 4, stick = tk.NSEW)

        self.response_data_entry = ScrolledText(data_frame, wrap = tk.WORD)
        self.response_data_entry.grid(row = 3, column = 4, columnspan = 4, stick = tk.NSEW)

        values = [http.time + ' ' + http.url for http in self.http_items]
        self.history_combo['values'] = values
        self.request_header_entry.insert(1.0, 'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0')

    def center_window(self, width = 1400, height = 700):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight() - 40
        if width > sw:
            width = sw
        if height > sh:
            height = sh
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        self.master.minsize(640, 480)

    def close(self):
        pickle.dump(self.http_items, open(self.history_file, 'wb'))
        self.master.destroy()

    def history_select(self, event):
        selected = self.history_combo.current()
        self.set_ui(self.http_items[selected])

    def enable_ui(self, enable):
        if enable:
            self.send_btn.config(state = tk.NORMAL)
        else:
            self.send_btn.config(state = tk.DISABLED)

    def clear_history(self):
        self.history_combo['values'] = ()
        self.history_var.set('')
        self.http_items = []
        pickle.dump(self.http_items, open(self.history_file, 'wb'))

    def set_ui(self, http_item):
        self.http_item = http_item
        self.url_var.set(http_item.url)
        self.request_header_entry.delete(1.0, tk.END)
        self.request_header_entry.insert(1.0, http_item.request_header)
        self.request_data_entry.delete(1.0, tk.END)
        self.request_data_entry.insert(1.0, http_item.request_data)
        self.response_header_entry.delete(1.0, tk.END)
        self.response_header_entry.insert(1.0, http_item.response_header)
        self.format_json()

    def format_json(self):
        if self.json_format_var.get() and self.http_item.response_data.startswith('{'):
            if not self.http_item.response_json:
                try:
                    self.http_item.response_json = json.dumps(json.loads(self.http_item.response_data), sort_keys = False, indent = 2, ensure_ascii = False)
                except Exception as ex:
                    pass
            self.response_data_entry.delete(1.0, tk.END)
            self.response_data_entry.insert(1.0, self.http_item.response_json)
        else:
            self.response_data_entry.delete(1.0, tk.END)
            self.response_data_entry.insert(1.0, self.http_item.response_data)

    def send(self):
        url = self.url_var.get().strip()
        if not url:
            return
        try:
            timeout = int(self.timeout_entry.get())
        except Exception as ex:
            timeout = 10
        proxy_type = self.proxy_var.get()
        proxy = self.proxy_entry.get().strip()
        format_json = self.json_format_var.get()
        request_header = self.request_header_entry.get('0.0', tk.END)
        request_data = self.request_data_entry.get('0.0', tk.END).strip()

        http_item = HttpRequest()
        self.http_item = http_item

        http_item.url = url
        http_item.timeout = timeout
        if proxy:
            http_item.proxy = (proxy_type, proxy)
            if not proxy.startswith('http'):
                proxy = '%s://%s' % (proxy_type, proxy)
            http_item.proxy_dict[proxy_type] = proxy

        http_item.request_header = request_header
        Util.header_2_dict(http_item.request_header, http_item.request_header_dict)
        http_item.request_data = request_data

        self.response_data_entry.delete(1.0, tk.END)
        self.response_header_entry.delete(1.0, tk.END)
        func_thread = Thread(target = self.thread_func, args = (http_item, ))
        func_thread.setDaemon(True)
        func_thread.start()

        self.enable_ui(False)
        self.time_label.config(text = 'Waiting ...')

        self.master.after(100, self.timer, 1)

    def send_finished(self):
        if self.http_item.exception:
            response_time = 'Exception: {}'.format(self.http_item.exception.__class__.__name__)
        else:
            response_time = 'ResponseTime: {:.3f}s'.format(self.http_item.response_time)
        self.time_label.config(text = response_time)
        self.request_header_entry.delete(1.0, tk.END)
        self.request_header_entry.insert(1.0, self.http_item.request_header)
        self.response_header_entry.delete(1.0, tk.END)
        self.response_header_entry.insert(1.0, self.http_item.response_header)
        self.format_json()

        self.http_items.append(self.http_item)
        self.history_combo['values'] += (self.http_item.time + ' ' + self.http_item.url, )
        self.enable_ui(True)
        pickle.dump(self.http_items, open(self.history_file, 'wb'))

    def timer(self, timer_id):
        if self.quene.empty():
            self.master.after(100, self.timer, timer_id)
        else:
            self.quene.get()
            self.send_finished()

    def thread_func(self, http_item):
        start = time.clock()
        try:
            # get raw data if stream is True
            http_item.time = time.strftime(ISO_TIME_FORMAT, time.localtime())
            if http_item.request_data:
                response = requests.post(http_item.url, data=http_item.request_data, headers=http_item.request_header_dict, proxies=http_item.proxy_dict, timeout=http_item.timeout, stream=False)
            else:
                response = requests.get(http_item.url, headers=http_item.request_header_dict, proxies=http_item.proxy_dict, timeout=http_item.timeout, stream=False)
            header = ''
            for key in response.request.headers:
                if key not in http_item.request_header:
                    header += '%s: %s\r\n' % (key, response.request.headers[key])
            http_item.request_header = header + http_item.request_header
            http_item.real_url = response.url
            http_item.response_header_dict = response.headers
            http_item.response_header = Util.dict_2_header(response.headers)
            http_item.response_data = response.text
            http_item.response_code = response.status_code
        except requests.exceptions.RequestException as ex:
            http_item.exception = ex
            print(traceback.format_exc())

        http_item.response_time = time.clock() - start
        self.quene.put(0)

def main():
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
