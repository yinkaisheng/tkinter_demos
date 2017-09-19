#!python3
# -*- coding: utf-8 -*-
#import os
#import sys
import tkinter as tk


class PopFrame(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.title("ButtonsWindow")
        self.protocol("WM_DELETE_WINDOW", self.onClose)

    def centerWindow(self, width = 400, height = 300):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2 + width + 16
        y = (sh - height) // 2
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        #self.resizable(0, 0)
        #self.minsize(width, height)
        #self.maxsize(width, height)

    def showModalless(self):
        self.centerWindow()
        self.deiconify()

    def onClose(self):
        pass

class MainFrame(tk.Frame):
    def __init__(self):
        super().__init__()
        self.popFrame = None
        self.sideDict = {1: 'LEFT', 2: 'TOP', 3: 'RIGHT', 4: 'BOTTOM',}
        self.expandDict = {0: 'False', 1: 'True',}
        self.fillDict = {1:'NONE', 2: 'X', 3: 'Y', 4: 'BOTH',}
        self.anchorDict = {1: 'CENTER', 2: 'N', 3: 'S', 4: 'W', 5: 'E',
                           6: 'NW', 7: 'SW', 8: 'NE', 9: 'SE',}
        self.sideVar = tk.IntVar()
        self.sideVar.set(1)
        self.expandVar = tk.IntVar()
        self.expandVar.set(0)
        self.fillVar = tk.IntVar()
        self.fillVar.set(1)
        self.anchorVar = tk.IntVar()
        self.anchorVar.set(1)
        self.count = 0
        self.btnFrame = None
        self.addedBtns = []

        self.initUI()

    def initUI(self):
        self.master.title('PackDemo')
        self.pack(expand = 1, fill = tk.BOTH, padx = 4, pady = 4)
        self.centerWindow()

        sideFrame = tk.LabelFrame(self, text = 'side:')
        sideFrame.pack(side = tk.TOP, fill = tk.X)
        for k, v in self.sideDict.items():
            tk.Radiobutton(sideFrame, text = v, variable = self.sideVar, value = k).pack(side = tk.LEFT)

        expandFrame = tk.LabelFrame(self, text = 'expand:')
        expandFrame.pack(side = tk.TOP, fill = tk.X)
        for k, v in self.expandDict.items():
            tk.Radiobutton(expandFrame, text = v, variable = self.expandVar, value = k).pack(side = tk.LEFT)

        fillFrame = tk.LabelFrame(self, text = 'fill:')
        fillFrame.pack(side = tk.TOP, fill = tk.X)
        for k, v in self.fillDict.items():
            tk.Radiobutton(fillFrame, text = v, variable = self.fillVar, value = k).pack(side = tk.LEFT)

        anchorFrame = tk.LabelFrame(self, text = 'anchor:')
        anchorFrame.pack(side = tk.TOP, fill = tk.X)
        sub1 = tk.Frame(anchorFrame)
        sub1.pack(side = tk.TOP, fill = tk.X)
        sub2 = tk.Frame(anchorFrame)
        sub2.pack(side = tk.TOP, fill = tk.X)
        sub3 = tk.Frame(anchorFrame)
        sub3.pack(side = tk.TOP, fill = tk.X)
        for k, v in self.anchorDict.items():
            if k == 1:
                p = sub1
            elif k <= 5:
                p = sub2
            else:
                p = sub3
            tk.Radiobutton(p, text = v, variable = self.anchorVar, value = k).pack(side = tk.LEFT)

        tk.Button(self, text = 'AddButton', command = self.add).pack(side = tk.LEFT, anchor = tk.N)
        tk.Button(self, text = 'UnDo', command = self.undo).pack(side = tk.LEFT, anchor = tk.N, padx = 8)
        tk.Button(self, text = 'ClearButtons', command = self.clear).pack(side = tk.LEFT, anchor = tk.N)

        self.popFrame = PopFrame(self)
        self.popFrame.showModalless()

    def add(self):
        self.count += 1
        btnText = 'Button' + str(self.count)
        side = self.sideDict[self.sideVar.get()].lower()
        expand = eval(self.expandDict[self.expandVar.get()])
        fill = self.fillDict[self.fillVar.get()].lower()
        anchor = self.anchorDict[self.anchorVar.get()].lower()
        if self.btnFrame is None:
            self.btnFrame = tk.Frame(self.popFrame)
            self.btnFrame.pack(side = tk.LEFT, expand = 1, fill = tk.BOTH)
        btn = tk.Button(self.btnFrame, text = btnText)
        btn.pack(side = side, expand = expand, fill = fill, anchor = anchor)
        self.addedBtns.append(btn)

    def undo(self):
        if self.addedBtns:
            self.addedBtns[-1].destroy()
            del self.addedBtns[-1]
            self.count -= 1

    def clear(self):
        self.count = 0
        if self.btnFrame:
            self.btnFrame.destroy()
            self.btnFrame = None
        self.addedBtns.clear()

    def centerWindow(self, width = 400, height = 300):
        sw = self.master.winfo_screenwidth()
        sh = self.master.winfo_screenheight()
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.master.geometry('{}x{}+{}+{}'.format(width, height, x, y))


def main():
    root = tk.Tk()
    app = MainFrame()
    root.mainloop()


if __name__ == '__main__':
    main()
