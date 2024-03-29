#!python3
# -*- coding: utf-8 -*-
#Author: yinkaisheng@foxmail.com
# Press Ctrl+Alt+F12 4 seconds to close tip
import os
import sys
import time
import ctypes
import configparser
import tkinter as tk

ScreenText = 'Hi. This is a screen tip. 你好'
TextColor = '#FF0000'
FontName = '微软雅黑'
FontSize = 50
Opacity = 100  # 0~255
Anchor = 'center'  # nw, n, ne, w, center, e, sw, e, se
ColorKey = 0xFFFFFF  # rgb color
ExitAfterSeconds = 0


class Example(tk.Frame):
    def __init__(self):
        super().__init__()
        self.timerTick = 500
        self.hotkeyTimes = 0
        if not ScreenText:
            self.initConfig()
        self.initUI()

    def initConfig(self):
        fileName = os.path.basename(__file__)
        fileName, ext = os.path.splitext(fileName)
        iniFile = fileName + '.ini'
        if os.path.exists(iniFile):
            global ScreenText, TextColor, FontName, FontSize, Opacity, Anchor
            config = configparser.ConfigParser()
            config.read(iniFile, encoding='utf-8')
            ScreenText = config.get('config', 'ScreenText').replace('\\n', '\n')
            Anchor = config.get('config', 'Anchor')
            TextColor = config.get('config', 'TextColor')
            FontName = config.get('config', 'FontName')
            FontSize = config.getint('config', 'FontSize')
            Opacity = config.getint('config', 'Opacity')

    def initUI(self):
        self.master.overrideredirect(True)
        self.master.lift()
        self.master.wm_attributes("-topmost", True)
        self.master.wm_attributes("-disabled", True)
        self.master.wm_attributes("-transparentcolor", "#FFFFFF")
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        self.master.geometry('{}x{}+{}+{}'.format(sw, sh // 2, 0, 0))
        GWL_EXSTYLE = -20
        WS_EX_COMPOSITED = 0x02000000
        WS_EX_LAYERED = 0x00080000
        WS_EX_NOACTIVATE = 0x08000000
        WS_EX_TOPMOST = 0x00000008
        WS_EX_TRANSPARENT = 0x00000020
        WS_EX_TOOLWINDOW = 0x00000080
        exStyle = WS_EX_COMPOSITED | WS_EX_LAYERED | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW
        self.handle = int(self.master.frame(), 16)
        ctypes.windll.user32.SetWindowLongW(self.handle, GWL_EXSTYLE, exStyle)
        LWA_COLORKEY, LWA_ALPHA = 1, 2
        ctypes.windll.user32.SetLayeredWindowAttributes(self.handle, ColorKey, Opacity, LWA_COLORKEY | LWA_ALPHA)
        # call SetWindowDisplayAffinity to exclude from screen capture
        WDA_MONITOR = 1
        ret = ctypes.windll.user32.SetWindowDisplayAffinity(self.handle, WDA_MONITOR)
        print('SetWindowDisplayAffinity returns', ret)

        self.pack(fill=tk.BOTH, expand=1)
        label = tk.Label(self, text=ScreenText, anchor=Anchor, font=(FontName, FontSize), fg=TextColor, bg='#FFFFFF', wraplength=sw)
        label.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.master.after(self.timerTick, self.onTimer)
        self.startTime = time.perf_counter()

    def onTimer(self):
        HWND_TOPMOST = -1
        NOSIZE, NOMOVE = 1, 2
        ctypes.windll.user32.SetWindowPos(self.handle, HWND_TOPMOST, 0, 0, 0, 0, NOSIZE | NOMOVE)
        self.checkExit()
        if ExitAfterSeconds > 0 and time.perf_counter() - self.startTime > ExitAfterSeconds:
            self.master.destroy()
            return
        self.master.after(self.timerTick, self.onTimer)

    def isKeyPressed(self, key: int):
        state = ctypes.windll.user32.GetAsyncKeyState(key)
        return True if state & 0x8000 else False

    def checkExit(self):
        VK_CONTROL, VK_MENU, VK_F12 = 0x11, 0x12, 0x7B
        if self.isKeyPressed(VK_CONTROL) and self.isKeyPressed(VK_MENU) and self.isKeyPressed(VK_F12):
            self.hotkeyTimes += 1
            if self.hotkeyTimes >= 4:
                self.master.destroy()
        else:
            self.hotkeyTimes = 0


def main():
    root = tk.Tk()
    app = Example()
    root.mainloop()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--msg', type=str, default='', help='message text')
    parser.add_argument('-t', '--time', type=int, default='0', help='exit time')
    parser.add_argument('-s', '--size', type=int, default=FontSize, help='font size')
    args = parser.parse_args()

    ScreenText = args.msg
    ExitAfterSeconds = args.time
    FontSize = args.size
    main()
