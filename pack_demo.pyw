#!python3
# -*- coding: utf-8 -*-
#author: yinkaisheng@live.com

import tkinter as tk
from tkinter.scrolledtext import ScrolledText


class PopFrame(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.transient(parent)
        self.title("ButtonsWindow")
        self.protocol("WM_DELETE_WINDOW", self.close)

    def center_window(self, width: int = 400, height: int = 300):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - width) // 2 + width + 16
        y = (sh - height) // 2
        self.geometry('{}x{}+{}+{}'.format(width, height, x, y))
        #self.resizable(0, 0)
        #self.minsize(width, height)
        #self.maxsize(width, height)

    def show_modalless(self):
        self.center_window()
        self.deiconify()

    def close(self):
        pass


class MainFrame(tk.Frame):
    def __init__(self):
        super().__init__()
        self.pop_frame = None
        self.widget_dict = {0: 'Label', 1: 'Button', 2: 'Entry', 3: 'ScrolledText', }
        self.widget_con = {0: tk.Label, 1: tk.Button, 2: tk.Entry, 3: ScrolledText, }
        self.side_dict = {1: 'LEFT', 2: 'TOP', 3: 'RIGHT', 4: 'BOTTOM', }
        self.expand_dict = {0: 'False', 1: 'True', }
        self.fill_dict = {1: 'NONE', 2: 'X', 3: 'Y', 4: 'BOTH', }
        self.anchor_dict = {1: 'CENTER', 2: 'N', 3: 'S', 4: 'W', 5: 'E',
                            6: 'NW', 7: 'SW', 8: 'NE', 9: 'SE', }

        self.widget_var = tk.IntVar()
        self.widget_var.set(0)
        self.padx_var = tk.StringVar()
        self.pady_var = tk.StringVar()
        self.side_var = tk.IntVar()
        self.side_var.set(1)
        self.expand_var = tk.IntVar()
        self.expand_var.set(0)
        self.fill_var = tk.IntVar()
        self.fill_var.set(1)
        self.anchor_var = tk.IntVar()
        self.anchor_var.set(1)
        self.widget_count = {}
        self.widget_frame = None
        self.added_widgets = []

        self.init_ui()

    def init_ui(self):
        self.master.title('PackDemo')
        self.pack(expand=1, fill=tk.BOTH, padx=4, pady=4)
        self.center_window()

        widget_frame = tk.LabelFrame(self, text='widget:')
        widget_frame.pack(side=tk.TOP, fill=tk.X)
        for k, v in self.widget_dict.items():
            tk.Radiobutton(widget_frame, text=v, variable=self.widget_var, value=k).pack(side=tk.LEFT)

        pad_frame = tk.LabelFrame(self, text='pad:')
        pad_frame.pack(side=tk.TOP, fill=tk.X)
        tk.Label(pad_frame, text='padx:').pack(side=tk.LEFT)
        self.sbox_x = tk.Spinbox(pad_frame, from_=0, to=10, increment=1, width=6, textvariable=self.padx_var)
        self.sbox_x.pack(side=tk.LEFT)
        tk.Label(pad_frame, text='pady:').pack(side=tk.LEFT)
        self.sbox_y = tk.Spinbox(pad_frame, values=list(range(0, 11, 2)), width=6, textvariable=self.pady_var)
        self.sbox_y.pack(side=tk.LEFT)

        side_frame = tk.LabelFrame(self, text='side:')
        side_frame.pack(side=tk.TOP, fill=tk.X)
        for k, v in self.side_dict.items():
            tk.Radiobutton(side_frame, text=v, variable=self.side_var, value=k).pack(side=tk.LEFT)

        expand_frame = tk.LabelFrame(self, text='expand:')
        expand_frame.pack(side=tk.TOP, fill=tk.X)
        for k, v in self.expand_dict.items():
            tk.Radiobutton(expand_frame, text=v, variable=self.expand_var, value=k).pack(side=tk.LEFT)

        fill_frame = tk.LabelFrame(self, text='fill:')
        fill_frame.pack(side=tk.TOP, fill=tk.X)
        for k, v in self.fill_dict.items():
            tk.Radiobutton(fill_frame, text=v, variable=self.fill_var, value=k).pack(side=tk.LEFT)

        anchor_frame = tk.LabelFrame(self, text='anchor:')
        anchor_frame.pack(side=tk.TOP, fill=tk.X)
        sub1 = tk.Frame(anchor_frame)
        sub1.pack(side=tk.TOP, fill=tk.X)
        sub2 = tk.Frame(anchor_frame)
        sub2.pack(side=tk.TOP, fill=tk.X)
        sub3 = tk.Frame(anchor_frame)
        sub3.pack(side=tk.TOP, fill=tk.X)
        for k, v in self.anchor_dict.items():
            if k == 1:
                p = sub1
            elif k <= 5:
                p = sub2
            else:
                p = sub3
            tk.Radiobutton(p, text=v, variable=self.anchor_var, value=k).pack(side=tk.LEFT)

        tk.Button(self, text='Add', command=self.add).pack(side=tk.LEFT, anchor=tk.N)
        tk.Button(self, text='UnDo', command=self.undo).pack(side=tk.LEFT, anchor=tk.N, padx=8)
        tk.Button(self, text='Clear', command=self.clear).pack(side=tk.LEFT, anchor=tk.N)

        self.pop_frame = PopFrame(self)
        self.pop_frame.show_modalless()

    def add(self):
        widget_type = self.widget_var.get()
        widget_con = self.widget_con[widget_type]
        self.widget_count[widget_type] = self.widget_count.get(widget_type, 0) + 1
        widget_text = self.widget_dict[widget_type] + str(self.widget_count[widget_type])
        side = self.side_dict[self.side_var.get()].lower()
        expand = eval(self.expand_dict[self.expand_var.get()])
        fill = self.fill_dict[self.fill_var.get()].lower()
        anchor = self.anchor_dict[self.anchor_var.get()].lower()
        if self.widget_frame is None:
            self.widget_frame = tk.Frame(self.pop_frame)
            self.widget_frame.pack(side=tk.LEFT, expand=1, fill=tk.BOTH)
        widget = widget_con(self.widget_frame)
        if isinstance(widget, tk.Label) or isinstance(widget, tk.Button):
            widget['text'] = widget_text
        else:
            widget.insert(tk.END, widget_text)
            # widget.see(tk.END)
        x = int(self.padx_var.get())
        y = int(self.pady_var.get())
        widget.pack(side=side, expand=expand, fill=fill, anchor=anchor, padx=x, pady=y)
        self.added_widgets.append(widget)

    def undo(self):
        if self.added_widgets:
            self.added_widgets[-1].destroy()
            del self.added_widgets[-1]
            self.count -= 1

    def clear(self):
        self.count = 0
        if self.widget_frame:
            self.widget_frame.destroy()
            self.widget_frame = None
        self.added_widgets.clear()

    def center_window(self, width: int = 400, height: int = 380):
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
