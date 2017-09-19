#!python3
# -*- coding: utf-8 -*-
#author: yinkaisheng@live.com
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

ISOTIMEFORMAT = '%Y-%m-%d %X'
HEIGHT_TEXT_HEIGHT = 8


class HttpRequest():
    def __init__(self):
        self.time = ''
        self.url = ''
        self.proxy = ()
        self.proxyDict = {}
        self.requestHeader = ''
        self.requestHeaderDict = {}
        self.requestData = ''
        self.realUrl = ''
        self.responseHeader = ''
        self.responseHeaderDict = {}
        self.responseData = ''
        self.responseJson = ''
        self.responseCode = ''
        self.responseTime = 0
        self.exception = None
        self.timeout = 60


class Util():
    @staticmethod
    def headerToDict(header, headerDict = None):
        headers = header.splitlines()
        if headerDict is None:
            headerDict = {}
        for it in headers:
            item = it.split(':')
            if len(item) == 2:
                headerDict[item[0].strip()] = item[1].strip()
        return headerDict

    @staticmethod
    def dictToHeader(headerDict):
        header = ''
        for key in headerDict:
            header += "%s: %s\r\n" % (key, headerDict[key])
        return header


class MainFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.historyVar = tk.StringVar()
        self.urlVar = tk.StringVar()
        self.jsonFormatVar = tk.BooleanVar()
        self.proxyVar = tk.StringVar()
        self.timeoutVar = tk.StringVar()
        self.quene = queue.Queue()
        self.httpItem = HttpRequest()
        self.httpItems = []
        self.configFile = 'history.dat'
        scriptDir = os.path.dirname(__file__)
        if scriptDir:
            os.chdir(scriptDir)

        if os.path.exists(self.configFile):
            self.httpItems = pickle.load(open(self.configFile, 'rb'))

        self.pack(expand = True, fill = tk.BOTH)
        self.initUI()

        self.master.protocol("WM_DELETE_WINDOW", self.onClose)

    def initUI(self):
        self.master.title('HttpRequester')
        self.pack(fill = tk.BOTH, expand = 1)
        self.centerWindow()

        historyFrame = ttk.Frame(self)
        historyFrame.pack(fill = tk.X, padx = 4, pady = 4)
        ttk.Label(historyFrame, text = 'History:', width = 8).pack(side = tk.LEFT)
        ttk.Button(historyFrame, text = 'ClearHistory', command = self.clearHistory).pack(side = tk.RIGHT)
        self.historyCombo = ttk.Combobox(historyFrame, textvariable = self.historyVar, state = 'readonly')
        self.historyCombo.bind("<<ComboboxSelected>>", self.historySelect)
        self.historyCombo['values'] = ()
        self.historyCombo.pack(fill = tk.X, expand = 1, padx = 4)

        urlFrame = ttk.Frame(self)
        urlFrame.pack(fill = tk.X, padx = 4, pady = 4)
        ttk.Label(urlFrame, text = 'URL:', width = 8).pack(side = tk.LEFT)
        self.sendBtn = ttk.Button(urlFrame, text = 'Send', command = self.send)
        self.sendBtn.pack(side = tk.RIGHT)
        self.urlEntry = ttk.Entry(urlFrame, textvariable = self.urlVar)
        self.urlEntry.pack(fill = tk.X, expand = 1, padx = 4)

        configFrame = ttk.Frame(self)
        configFrame.pack(fill = tk.X, padx = 4, pady = 4)
        self.timeLabel = ttk.Label(configFrame, text = '')
        self.timeLabel.pack(side = tk.RIGHT)
        self.timeoutVar.set('10')
        self.timeoutEntry = ttk.Entry(configFrame, textvariable = self.timeoutVar, width = 4)
        self.timeoutEntry.pack(side = tk.RIGHT)
        ttk.Label(configFrame, text = 'Timeout:').pack(side = tk.RIGHT)
        self.proxyEntry = ttk.Entry(configFrame)
        self.proxyEntry.pack(side = tk.RIGHT)
        self.proxyCombo = ttk.Combobox(configFrame, textvariable = self.proxyVar, state = 'readonly', width = 4)
        self.proxyCombo.pack(side = tk.RIGHT, padx = 4)
        self.proxyCombo['values'] = ('http', 'https')
        self.proxyCombo.current(0)
        ttk.Label(configFrame, text = 'Proxy:').pack(side = tk.RIGHT)

        dataFrame = ttk.Frame(self)
        dataFrame.pack(fill = tk.BOTH, expand = 1, padx = 4, pady = 4)
        dataFrame.columnconfigure(0, weight = 1)
        dataFrame.columnconfigure(4, weight = 1)
        dataFrame.rowconfigure(3, weight = 1)

        ttk.Label(dataFrame, text = 'RequestHeader:').grid(row = 0, column = 0, stick = tk.W)
        ttk.Label(dataFrame, text = 'ResponsetHeader:').grid(row = 0, column = 4, stick = tk.W)
        self.requestHeaderEntry = ScrolledText(dataFrame, height = HEIGHT_TEXT_HEIGHT)
        self.requestHeaderEntry.grid(row = 1, column = 0, columnspan = 4, stick = tk.NSEW)

        self.responseHeaderEntry = ScrolledText(dataFrame, height = HEIGHT_TEXT_HEIGHT)
        self.responseHeaderEntry.grid(row = 1, column = 4, columnspan = 4, stick = tk.NSEW)

        ttk.Label(dataFrame, text = 'RequestData:').grid(row = 2, column = 0, stick = tk.W)
        ttk.Label(dataFrame, text = 'ResponsetData:').grid(row = 2, column = 4, stick = tk.W)
        #self.jsonCheck = tk.Checkbutton(dataFrame, text = 'JsonFormat', variable = self.jsonFormatVar)
        #self.jsonCheck.deselect()
        self.jsonCheck = ttk.Checkbutton(dataFrame, text = 'JsonFormat', variable = self.jsonFormatVar, command = self.formatJson)
        self.jsonCheck.grid(row = 2, column = 5, stick = tk.W)
        self.requestDataEntry = ScrolledText(dataFrame, wrap = tk.WORD)
        self.requestDataEntry.grid(row = 3, column = 0, columnspan = 4, stick = tk.NSEW)

        self.responseDataEntry = ScrolledText(dataFrame, wrap = tk.WORD)
        self.responseDataEntry.grid(row = 3, column = 4, columnspan = 4, stick = tk.NSEW)

        values = [http.time + ' ' + http.url for http in self.httpItems]
        self.historyCombo['values'] = values
        self.requestHeaderEntry.insert(1.0, 'User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0')

    def centerWindow(self, width = 1400, height = 700):
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

    def onClose(self):
        pickle.dump(self.httpItems, open(self.configFile, 'wb'))
        self.master.destroy()

    def historySelect(self, event):
        selected = self.historyCombo.current()
        self.setUI(self.httpItems[selected])

    def enableUI(self, isEnable):
        if isEnable:
            self.sendBtn.config(state = tk.NORMAL)
        else:
            self.sendBtn.config(state = tk.DISABLED)

    def clearHistory(self):
        self.historyCombo['values'] = ()
        self.historyVar.set('')
        self.httpItems = []
        pickle.dump(self.httpItems, open(self.configFile, 'wb'))

    def setUI(self, httpItem):
        self.httpItem = httpItem
        self.urlVar.set(httpItem.url)
        self.requestHeaderEntry.delete(1.0, tk.END)
        self.requestHeaderEntry.insert(1.0, httpItem.requestHeader)
        self.requestDataEntry.delete(1.0, tk.END)
        self.requestDataEntry.insert(1.0, httpItem.requestData)
        self.responseHeaderEntry.delete(1.0, tk.END)
        self.responseHeaderEntry.insert(1.0, httpItem.responseHeader)
        self.formatJson()

    def formatJson(self):
        if self.jsonFormatVar.get() and self.httpItem.responseData.startswith('{'):
            if not self.httpItem.responseJson:
                try:
                    self.httpItem.responseJson = json.dumps(json.loads(self.httpItem.responseData), sort_keys = False, indent = 2, ensure_ascii = False)
                except Exception as ex:
                    pass
            self.responseDataEntry.delete(1.0, tk.END)
            self.responseDataEntry.insert(1.0, self.httpItem.responseJson)
        else:
            self.responseDataEntry.delete(1.0, tk.END)
            self.responseDataEntry.insert(1.0, self.httpItem.responseData)

    def send(self):
        url = self.urlVar.get().strip()
        if not url:
            return
        try:
            timeout = int(self.timeoutEntry.get())
        except Exception as ex:
            timeout = 10
        proxyType = self.proxyVar.get()
        proxy = self.proxyEntry.get().strip()
        formatJson = self.jsonFormatVar.get()
        requestHeader = self.requestHeaderEntry.get('0.0', tk.END)
        requestData = self.requestDataEntry.get('0.0', tk.END).strip()

        httpItem = HttpRequest()
        self.httpItem = httpItem

        httpItem.url = url
        httpItem.timeout = timeout
        if proxy:
            httpItem.proxy = (proxyType, proxy)
            if not proxy.startswith('http'):
                proxy = '%s://%s' % (proxyType, proxy)
            httpItem.proxyDict[proxyType] = proxy

        httpItem.requestHeader = requestHeader
        Util.headerToDict(httpItem.requestHeader, httpItem.requestHeaderDict)
        httpItem.requestData = requestData

        self.responseDataEntry.delete(1.0, tk.END)
        self.responseHeaderEntry.delete(1.0, tk.END)
        funcThread = Thread(target = self.threadFunc, args = (httpItem, ))
        funcThread.setDaemon(True)
        funcThread.start()

        self.enableUI(False)
        self.timeLabel.config(text = 'Waiting ...')

        self.master.after(100, self.timer, 1)

    def sendFinished(self):
        if self.httpItem.exception:
            responseTime = 'Exception: {}'.format(self.httpItem.exception.__class__.__name__)
        else:
            responseTime = 'ResponseTime: {:.3f}s'.format(self.httpItem.responseTime)
        self.timeLabel.config(text = responseTime)
        self.requestHeaderEntry.delete(1.0, tk.END)
        self.requestHeaderEntry.insert(1.0, self.httpItem.requestHeader)
        self.responseHeaderEntry.delete(1.0, tk.END)
        self.responseHeaderEntry.insert(1.0, self.httpItem.responseHeader)
        self.formatJson()

        self.httpItems.append(self.httpItem)
        self.historyCombo['values'] += (self.httpItem.time + ' ' + self.httpItem.url, )
        self.enableUI(True)
        pickle.dump(self.httpItems, open(self.configFile, 'wb'))

    def timer(self, timerId):
        if self.quene.empty():
            self.master.after(100, self.timer, timerId)
        else:
            self.quene.get()
            self.sendFinished()

    def threadFunc(self, httpItem):
        start = time.clock()
        try:
            # get raw data if stream is True
            httpItem.time = time.strftime(ISOTIMEFORMAT, time.localtime())
            if httpItem.requestData:
                response = requests.post(httpItem.url, data=httpItem.requestData, headers=httpItem.requestHeaderDict, proxies=httpItem.proxyDict, timeout=httpItem.timeout, stream=False)
            else:
                response = requests.get(httpItem.url, headers=httpItem.requestHeaderDict, proxies=httpItem.proxyDict, timeout=httpItem.timeout, stream=False)
            header = ''
            for key in response.request.headers:
                if key not in httpItem.requestHeader:
                    header += '%s: %s\r\n' % (key, response.request.headers[key])
            httpItem.requestHeader = header + httpItem.requestHeader
            httpItem.realUrl = response.url
            httpItem.responseHeaderDict = response.headers
            httpItem.responseHeader = Util.dictToHeader(response.headers)
            httpItem.responseData = response.text
            #httpItem.responseJson = response.json()
            httpItem.responseCode = response.status_code
        except requests.exceptions.RequestException as ex:
            httpItem.exception = ex
            print(traceback.format_exc())

        httpItem.responseTime = time.clock() - start
        self.quene.put(0)

def main():
    root = tk.Tk()
    app = MainFrame(root)
    root.mainloop()


if __name__ == '__main__':
    main()
