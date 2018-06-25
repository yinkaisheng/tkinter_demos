#!python3
# -*- coding: utf-8 -*-
# author: yinkaisheng@live.com
import os
import sys
import time
import queue
from collections import namedtuple
from threading import Thread
import tkinter as tk

class TimerInfo():
    def __init__(self, tid, interval, start, func):
        self.tid = tid
        self.interval = interval
        self.start = start
        self.func = func
        self.execCount = 1
        self.elapsed = 0

class AsyncFrame(tk.Frame):
    NotifyID_ThreadExit = -1000000
    TimerID_Thread = -1000000
    def __init__(self, master=None, cnf={}, **kw):
        super().__init__()
        self._timers = []
        self._minTimerTick = 5
        self._threadid = 0
        self._threadFuncs = {}
        self._notifyQueue = queue.Queue()

    def centerWindow(self, width = 600, height = 300):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        if isinstance(width, float):
            width = int(sw * width)
        if isinstance(height, float):
            height = int(sh * height)
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def moveWindow(self, x, y, width = -1, height = -1):
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

    def showWidow(self):
        self.master.deiconify()

    def hideWindow(self):
        self.master.withdraw()

    def setTopmost(self, top = True):
        self.master.wm_attributes("-topmost", 1 if top else 0)

    def enableControl(self, control, enable):
        if enable:
            control.config(state = tk.NORMAL)
        else:
            control.config(state = tk.DISABLED)

    def appendEntryText(self, entry, text):
        entry.insert(tk.END, text)
        entry.see(tk.END)

    def getEntryText(self, entry):
        entry.get('0.0', tk.END)

    def clearEntry(self, entry):
        entry.delete(1.0, tk.END)

    def startTimer(self, timerId, timerInterval, timerFunc):
        '''
        timerId: int
        timerInterval: int, in millisecond
        timerFunc: function(callCount, elapsedTime)
        '''
        for timer in self._timers:
            if timerId == timer.tid:
                return False  #already started
        timer = TimerInfo(timerId, timerInterval, time.time(), timerFunc)
        self._timers.append(timer)
        self.master.after(self._minTimerTick, self._onTimerCall)
        return True

    def stopTimer(self, timerId):
        stopped = False
        for i, timer in enumerate(self._timers):
            if timer.tid == timerId:
                del self._timers[i]
                stopped = True
        return stopped

    def _onTimerCall(self):
        for timer in self._timers:
            timer.elapsed = time.time() - timer.start
            if timer.elapsed * 1000 >= timer.interval * timer.execCount:
                timer.func(timer.execCount, timer.elapsed)
                timer.execCount += 1
        if self._timers:
            self.master.after(self._minTimerTick, self._onTimerCall)

    def runInThread(self, func, args, notifyFunc):
        '''
        func(threadId, args) is executed in a thread
        call threadNotifyUI(threadId, notifyId, args) in func thread, then notifyFunc(notifyId, args) will be called in main thread
        '''
        self._threadid += 1
        self._threadFuncs[self._threadid] = notifyFunc
        func_thread = Thread(target = self._threadFunc, args = (self._threadid, func, args))
        func_thread.setDaemon(True)
        func_thread.start()
        self.startTimer(AsyncFrame.TimerID_Thread, 100, self._timerGetNotifies)

    def threadNotifyUI(self, threadId, notifyId, args):
        self._notifyQueue.put((threadId, notifyId, args))

    def _threadFunc(self, threadId, func, args):
        func(threadId, args)
        self._notifyQueue.put((threadId, AsyncFrame.NotifyID_ThreadExit, None))

    def _timerGetNotifies(self, callCount, elapsedTime):
        if not self._notifyQueue.empty():
            threadId, notifyId, args = self._notifyQueue.get()
            self._threadFuncs[threadId](notifyId, args)
            if notifyId == AsyncFrame.NotifyID_ThreadExit:
                del self._threadFuncs[threadId]
                if not self._threadFuncs:
                    self.stopTimer(AsyncFrame.TimerID_Thread)

