#!python3
# -*- coding: utf-8 -*-
# author: yinkaisheng@foxmail.com
import os
import sys
import time
import queue
from collections import namedtuple
from threading import Thread
from typing import (Any, Callable, Dict, List, Sequence, Tuple)
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class TimerInfo():
    def __init__(self, tid: int, interval: int, startTime: float, func: Callable[[int, int, float], None]):
        self.tid = tid
        self.interval = interval
        self.startTime = startTime
        self.func = func
        self.execCount = 1
        self.elapsed = 0


class WidgetUtil():
    def enableWidget(self, widget: tk.Widget, enable: bool):
        if enable:
            widget.config(state=tk.NORMAL)
        else:
            widget.config(state=tk.DISABLED)

    def appendEntryText(self, entry: ttk.Entry, text: str):
        entry.insert(tk.END, text)
        if entry.__class__.__name__ == 'Entry':
            entry.icursor(tk.END)
        elif entry.__class__.__name__ == 'ScrolledText':
            entry.see(tk.END)

    def getEntryText(self, entry: ttk.Entry) -> str:
        entry.get('0.0', tk.END)

    def clearEntry(self, entry: ttk.Entry):
        if isinstance(entry, tk.Entry):
            entry.delete(0, tk.END)
        elif isinstance(entry, ScrolledText):
            entry.delete(1.0, tk.END)

    def deleteEntrySelection(self, entry: ttk.Entry):
        try:
            self.widget.delete('sel.first', 'sel.last')
        except Exception as ex:
            pass

    def getComboBoxSelection(self, combo: ttk.Combobox) -> int:
        return combo.current()

    def setComboBoxSelection(self, combo: ttk.Combobox, index: int):
        combo.current(index)

    def getComboBoxItemText(self, combo: ttk.Combobox, index: int) -> str:
        return combo['values'][index]

    def getComboBoxAllItemsText(self, combo: ttk.Combobox) -> tuple:
        return combo['values']

    def getComboBoxItemsCount(self, combo: ttk.Combobox) -> tuple:
        return len(combo['values'])

    def addComboBoxItem(self, combo: ttk.Combobox, item: str):
        combo['values'] += (item, )  # tuple add

    def addComboBoxItemIfNotExists(self, combo: ttk.Combobox, item: str):
        if item in combo['values']:
            return
        self.addComboBoxItem(combo, item)

    def insertComboBoxItem(self, combo: ttk.Combobox, index: int, item: str):
        combo['values'] = combo['values'][:index] + (item, ) + combo['values'][index:]

    def insertComboBoxItemIfNotExists(self, combo: ttk.Combobox, index: int, item: str):
        if item in combo['values']:
            return
        self.insertComboBoxItem(combo, index, item)

    def deleteComboBoxItem(self, combo: ttk.Combobox, index: int):
        if index < 0:
            index = len(combo['values']) + index
        combo['values'] = combo['values'][:index] + combo['values'][index + 1:]

    def deleteComboBoxItemStr(self, combo: ttk.Combobox, item: str):
        try:
            index = combo['values'].index(item)
            self.deleteComboBoxItem(combo, index)
        except ValueError as ex:
            pass

    def clearComboBox(self, combo: ttk.Combobox):
        combo['values'] = ()


class AsyncFrame(tk.Frame):
    NotifyID_ThreadExit = -1
    TimerID_Thread = -1

    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master, cnf, **kw)
        self._timers = []
        self._minTimerTick = 5
        self._threadNotifyCheckInterval = 20
        self._threadid = 0
        self._threadNotifyFuncs = {}
        self._notifyQueue = queue.Queue()

    def setIcon(self, iconPath: str = '', iconBytes: bytes = None, overWrite: bool = True):
        '''Linux should use xbm image'''
        if iconBytes:
            iconPath = 'tkframetemp.ico'
            fout = open(iconPath, 'wb')
            fout.write(iconBytes)
            fout.close()
        if os.path.exists(iconPath):
            self.master.iconbitmap(iconPath)
        if iconBytes:
            os.remove(iconPath)

    def centerWindow(self, width: int = 600, height: int = 300):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight() - 40
        if isinstance(width, float):
            width = int(sw * width)
        if isinstance(height, float):
            height = int(sh * height)
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def showWidow(self):
        self.master.deiconify()

    def minSize(self, width: int, height: int):
        self.master.minsize(width, height)

    def maxSize(self, widht: int, height: int):
        self.master.maxsize(widht, height)

    def moveWindow(self, x: int, y: int, width: int = -1, height: int = -1):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        if isinstance(width, float):
            width = int(sw * width)
        if isinstance(height, float):
            height = int(sh * height)
        if width < 0:
            width = self.winfo_width()
        if height < 0:
            height = self.winfo_height()
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def moveWindowRatio(self, lRatio: float, tRatio: float, rRatio: float, bRatio: float):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight() - 40
        l = int(sw * lRatio)
        t = int(sh * tRatio)
        r = int(sw * rRatio)
        b = int(sh * bRatio)
        self.master.geometry('{}x{}+{}+{}'.format(r - l, b - t, l, t))

    def hideWindow(self):
        self.master.withdraw()

    def setTopmost(self, top: bool = True):
        self.master.wm_attributes("-topmost", 1 if top else 0)

    def setMiniTimerInterval(self, interval: int):
        self._minTimerTick = interval

    def isTimerStart(self, timerId: int):
        for timer in self._timers:
            if timerId == timer.tid:
                return True
        return False

    def startTimer(self, timerId: int, timerInterval: int, timerFunc: Callable[[int, int, float], None]):
        '''
        timerId: int, must > 0
        timerInterval: int, in millisecond, must > 0
        timerFunc: function(timerId: int, callCount: int, elapsedTime: float
        '''
        if self.isTimerStart(timerId):
            print('timer {} already started'.format(timerId))
            return False  # already started
        timer = TimerInfo(timerId, timerInterval, time.perf_counter(), timerFunc)
        self._timers.append(timer)
        if len(self._timers) == 1:  # first start
            self.master.after(self._minTimerTick, self._onTimerCall)
        return True

    def stopTimer(self, timerId: int):
        stopped = False
        for i, timer in enumerate(self._timers):
            if timer.tid == timerId:
                del self._timers[i]
                stopped = True
                break
        return stopped

    def _onTimerCall(self):
        for timer in self._timers:
            timer.elapsed = time.perf_counter() - timer.startTime
            if timer.elapsed * 1000 >= timer.interval * timer.execCount:
                timer.func(timer.tid, timer.execCount, timer.elapsed)
                timer.execCount += 1
        if self._timers:
            self.master.after(self._minTimerTick, self._onTimerCall)

    def runInThread(self, func: Callable[[int, Any], Any], args: Any, notifyFunc: Callable[[int, int, Any], None]) -> int:
        '''
        func(threadId, args) is executed in a thread
        call threadNotifyUI(threadId, notifyId, args) in func thread
        then notifyFunc(threadId, notifyId, args) will be called in main thread
        return a fake thread id starts with 1
        '''
        self._threadid += 1
        self._threadNotifyFuncs[self._threadid] = notifyFunc
        func_thread = Thread(target=self._threadFunc, args=(self._threadid, func, args))
        func_thread.setDaemon(True)
        func_thread.start()
        if not self.isTimerStart(AsyncFrame.TimerID_Thread):
            self.startTimer(AsyncFrame.TimerID_Thread, self._threadNotifyCheckInterval, self._timerGetNotifies)
        return self._threadid

    def threadNotifyUI(self, threadId: int, notifyId: int, args: Any):
        self._notifyQueue.put((threadId, notifyId, args))

    def _threadFunc(self, threadId: int, func: Callable[[int, Any], Any], args: Any):
        ret = func(threadId, args)
        self._notifyQueue.put((threadId, AsyncFrame.NotifyID_ThreadExit, ret))

    def _timerGetNotifies(self, timerId: int, callCount: int, elapsedTime: float):
        while not self._notifyQueue.empty():
            threadId, notifyId, args = self._notifyQueue.get()
            self._notifyQueue.task_done()
            self._threadNotifyFuncs[threadId](threadId, notifyId, args)
            if notifyId == AsyncFrame.NotifyID_ThreadExit:
                del self._threadNotifyFuncs[threadId]
                if not self._threadNotifyFuncs:
                    self.stopTimer(AsyncFrame.TimerID_Thread)


class EditMenu():
    def __init__(self, widget: tk.Widget):
        self.widget = widget
        self.menu = tk.Menu(widget, tearoff=0)
        self.menu.add_command(label="(Ctrl+A) SelectAll", command=self.onSelectAll)
        self.menu.add_separator()
        self.menu.add_command(label="(Ctrl+C) Copy", command=self.onCopy)
        self.menu.add_command(label="(Ctrl+V) Paste", command=self.onPaste)
        self.menu.add_command(label="(Ctrl+X) Cut", command=self.onCut)

    def deleteSelection(self):
        if self.widget.__class__.__name__ == 'Entry':
            if self.widget.selection_present():
                self.widget.selection_clear()
        elif self.widget.__class__.__name__ == 'ScrolledText':
            try:
                self.widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except Exception as ex:
                pass

    def onSelectAll(self):
        if self.widget.__class__.__name__ == 'Entry':
            self.widget.selection_range(0, tk.END)
            self.widget.icursor(tk.END)
        elif self.widget.__class__.__name__ == 'ScrolledText':
            self.widget.tag_add(tk.SEL, 1.0, 'end-1c')
            self.widget.mark_set(tk.INSERT, 1.0)

    def onCopy(self):
        self.widget.event_generate("<<Copy>>")
        # try:
            # if self.widget.__class__.__name__ == 'Entry':
                #text = self.widget.get()
            # elif self.widget.__class__.__name__ == 'ScrolledText':
                # text = self.widget.get(tk.SEL_FIRST, tk.SEL_LAST)  # text = self.widget.selection_get()
            # self.widget.clipboard_clear()
            # self.widget.clipboard_append(text)
        # except Exception as ex:
            # pass

    def onPaste(self):
        self.widget.event_generate("<<Paste>>")
        # self.deleteSelection()
        #text = self.widget.clipboard_get()
        #self.widget.insert(tk.INSERT, text)

    def onCut(self):
        self.widget.event_generate("<<Cut>>")
        # self.onCopy()
        # self.deleteSelection()

    def showMenu(self, event: tk.Event):
        self.widget.focus_set()
        self.menu.post(event.x_root, event.y_root)

