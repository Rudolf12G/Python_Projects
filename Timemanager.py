import tkinter as tk
from tkinter import colorchooser
import time
import json
import os

CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".transparent_clock_config.json")

DEFAULT_CONFIG = {
    "font_family": "Consolas",
    "font_size": 22,
    "text_color": "#FEC47F",
    "is_pinned": True,
    "is_locked": False,
    "x_pos": None,
    "y_pos": None
}


class TransparentClock:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)

        # Load saved settings or defaults
        self.config = self.load_config()

        self.root.attributes("-topmost", self.config["is_pinned"])
        self.is_pinned = self.config["is_pinned"]
        self.is_locked = self.config["is_locked"]
        self.font_family = self.config["font_family"]
        self.font_size = self.config["font_size"]
        self.text_color = self.config["text_color"]
        self.active_menu = None

        WINDOW_BG = "#010101"
        self.root.config(bg=WINDOW_BG)
        self.root.wm_attributes("-transparentcolor", WINDOW_BG)

        # Determine window positioning
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x_pos = self.config["x_pos"] if self.config["x_pos"] is not None else screen_width - 220
        y_pos = self.config["y_pos"] if self.config["y_pos"] is not None else 50

        initial_time = time.strftime("%I:%M %p")

        self.time_label = tk.Label(
            root,
            text=initial_time,
            font=(self.font_family, self.font_size, "bold"),
            fg=self.text_color,
            bg=WINDOW_BG,
            padx=10,
            pady=5
        )
        self.time_label.pack(expand=True, fill="both")

        self.update_window_size(x_pos, y_pos)

        # Dragging bindings
        self.time_label.bind("<B1-Motion>", self.move_window)
        self.time_label.bind("<Button-1>", self.get_pos)
        self.time_label.bind("<ButtonRelease-1>", self.save_position_on_drop)

        # Edge-to-edge Right-click bindings
        for widget in (self.root, self.time_label):
            widget.bind("<Button-3>", self.show_custom_menu)
            widget.bind("<Button-2>", self.show_custom_menu)

        self.root.bind("<Escape>", lambda e: self.safe_exit())
        self.update_time()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    # Ensure all keys exist
                    for key, val in DEFAULT_CONFIG.items():
                        if key not in data:
                            data[key] = val
                    return data
        except Exception:
            pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            self.config["font_family"] = self.font_family
            self.config["font_size"] = self.font_size
            self.config["text_color"] = self.text_color
            self.config["is_pinned"] = self.is_pinned
            self.config["is_locked"] = self.is_locked
            self.config["x_pos"] = self.root.winfo_x()
            self.config["y_pos"] = self.root.winfo_y()

            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)
        except Exception:
            pass

    def safe_exit(self):
        self.save_config()
        self.root.destroy()

    def update_window_size(self, x=None, y=None):
        self.root.update_idletasks()
        width = self.time_label.winfo_reqwidth() + 20
        height = self.time_label.winfo_reqheight() + 10

        if x is None:
            x = self.root.winfo_x()
        if y is None:
            y = self.root.winfo_y()

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.save_config()

    def get_pos(self, event):
        self.x = event.x
        self.y = event.y

    def move_window(self, event):
        if self.is_locked:
            return

        deltax = event.x - self.x
        deltay = event.y - self.y
        new_x = self.root.winfo_x() + deltax
        new_y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{new_x}+{new_y}")

    def save_position_on_drop(self, event):
        if not self.is_locked:
            self.save_config()

    def show_custom_menu(self, event):
        if self.active_menu is not None:
            try:
                self.active_menu.destroy()
            except:
                pass
            self.active_menu = None

        menu_win = tk.Toplevel(self.root)
        self.active_menu = menu_win

        menu_win.overrideredirect(True)
        menu_win.attributes("-topmost", True)
        menu_win.config(bg="#1e1e1e", highlightbackground="#444444", highlightthickness=1)

        x = event.x_root
        y = event.y_root

        screen_w = menu_win.winfo_screenwidth()
        screen_h = menu_win.winfo_screenheight()
        if x + 210 > screen_w:
            x = screen_w - 220
        if y + 430 > screen_h:
            y = screen_h - 440

        menu_win.geometry(f"210x430+{x}+{y}")
        menu_win.update_idletasks()

        open_time = time.time()
        global_click_id = None
        is_closing = False

        def close_menu(e=None):
            nonlocal global_click_id, is_closing
            if is_closing:
                return
            is_closing = True

            if global_click_id:
                try:
                    self.root.unbind("<Button-1>", global_click_id)
                except:
                    pass
            if self.active_menu == menu_win:
                self.active_menu = None
            try:
                menu_win.destroy()
            except:
                pass

        def on_global_click(e):
            if is_closing or time.time() - open_time < 0.25:
                return
            try:
                wx = menu_win.winfo_rootx()
                wy = menu_win.winfo_rooty()
                ww = menu_win.winfo_width()
                wh = menu_win.winfo_height()
                if not (wx <= e.x_root <= wx + ww and wy <= e.y_root <= wy + wh):
                    close_menu()
            except:
                close_menu()

        global_click_id = self.root.bind("<Button-1>", on_global_click, add="+")
        menu_win.protocol("WM_DELETE_WINDOW", close_menu)

        # --- Custom Title Bar with 'X' Close Button ---
        title_bar = tk.Frame(menu_win, bg="#252525", height=26)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)

        title_label = tk.Label(title_bar, text=" Clock Settings", bg="#252525", fg="#FEC47F",
                               font=("Consolas", 9, "bold"))
        title_label.pack(side="left", padx=4)

        close_btn = tk.Label(title_bar, text=" ✕ ", bg="#252525", fg="#ff9999", font=("Consolas", 9, "bold"),
                             cursor="hand2")
        close_btn.pack(side="right", fill="y")
        close_btn.bind("<Button-1>", lambda e: close_menu())
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg="#ff4444", fg="white"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg="#252525", fg="#ff9999"))

        def start_move(e):
            menu_win._x = e.x
            menu_win._y = e.y

        def do_move(e):
            nx = menu_win.winfo_x() + (e.x - menu_win._x)
            ny = menu_win.winfo_y() + (e.y - menu_win._y)
            menu_win.geometry(f"+{nx}+{ny}")

        title_bar.bind("<Button-1>", start_move)
        title_bar.bind("<B1-Motion>", do_move)
        title_label.bind("<Button-1>", start_move)
        title_label.bind("<B1-Motion>", do_move)

        content_frame = tk.Frame(menu_win, bg="#1e1e1e")
        content_frame.pack(fill="both", expand=True, padx=4, pady=4)

        def refresh_menu():
            for widget in content_frame.winfo_children():
                widget.destroy()
            build_menu_content()

        def make_clickable_option(parent, text, bg, fg, command):
            lbl = tk.Label(parent, text=text, bg=bg, fg=fg, font=("Consolas", 9), anchor="w", padx=8, pady=4,
                           cursor="hand2")
            lbl.bind("<Button-1>", lambda e: command())

            def on_enter(e):
                if bg != "#3a3a3a":
                    lbl.config(bg="#383838")

            def on_leave(e):
                if bg != "#3a3a3a":
                    lbl.config(bg=bg)

            lbl.bind("<Enter>", on_enter)
            lbl.bind("<Leave>", on_leave)
            return lbl

        def build_menu_content():
            pin_text = "✓ Pinned to Top" if self.is_pinned else "Pin to Top"
            pin_lbl = make_clickable_option(content_frame, pin_text, "#2d2d2d", "white",
                                            lambda: [self.toggle_pin(), refresh_menu()])
            pin_lbl.pack(fill="x", padx=4, pady=1)

            lock_text = "✓ Position Locked" if self.is_locked else "Lock Position"
            lock_lbl = make_clickable_option(content_frame, lock_text, "#2d2d2d", "white",
                                             lambda: [self.toggle_lock(), refresh_menu()])
            lock_lbl.pack(fill="x", padx=4, pady=1)

            tk.Frame(content_frame, height=1, bg="#444444").pack(fill="x", padx=4, pady=4)

            tk.Label(content_frame, text="Font Family", bg="#1e1e1e", fg="#aaaaaa", font=("Consolas", 8, "bold")).pack(
                anchor="w", padx=4)

            fonts = ["Consolas", "Arial", "Courier New", "Segoe UI", "Impact"]
            for f in fonts:
                is_active = (f == self.font_family)
                prefix = "▶ " if is_active else "   "
                bg_col = "#3a3a3a" if is_active else "#2d2d2d"
                fg_col = "#FEC47F" if is_active else "white"

                f_lbl = make_clickable_option(content_frame, f"{prefix}{f}", bg_col, fg_col,
                                              lambda fam=f: [self.set_font_family(fam), refresh_menu()])
                f_lbl.pack(fill="x", padx=4, pady=1)

            tk.Frame(content_frame, height=1, bg="#444444").pack(fill="x", padx=4, pady=4)

            tk.Label(content_frame, text="Font Size Slider", bg="#1e1e1e", fg="#aaaaaa",
                     font=("Consolas", 8, "bold")).pack(anchor="w", padx=4)

            size_slider = tk.Scale(
                content_frame,
                from_=12,
                to=72,
                orient="horizontal",
                bg="#1e1e1e",
                fg="#FEC47F",
                troughcolor="#2d2d2d",
                highlightthickness=0,
                bd=0,
                command=self.set_font_size_from_slider
            )
            size_slider.set(self.font_size)
            size_slider.pack(fill="x", padx=4, pady=4)

            tk.Frame(content_frame, height=1, bg="#444444").pack(fill="x", padx=4, pady=4)

            def open_color():
                close_menu()
                color_code = colorchooser.askcolor(title="Choose Custom Color", initialcolor=self.time_label.cget("fg"))
                if color_code[1]:
                    self.set_color(color_code[1])

            color_lbl = make_clickable_option(content_frame, "Text Color Spectrum...", "#2d2d2d", "white", open_color)
            color_lbl.pack(fill="x", padx=4, pady=1)

            exit_lbl = make_clickable_option(content_frame, "Close Program", "#4a2222", "#ff9999", self.safe_exit)
            exit_lbl.pack(fill="x", padx=4, pady=(2, 4))

        build_menu_content()

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.root.attributes("-topmost", self.is_pinned)
        if not self.is_pinned:
            self.root.lower()
        self.save_config()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.save_config()

    def set_font_family(self, family):
        self.font_family = family
        self.time_label.config(font=(self.font_family, self.font_size, "bold"))
        self.update_window_size()
        self.save_config()

    def set_font_size_from_slider(self, val):
        try:
            new_size = int(float(val))
            if new_size != self.font_size:
                self.font_size = new_size
                self.time_label.config(font=(self.font_family, self.font_size, "bold"))
                self.update_window_size()
                self.save_config()
        except ValueError:
            pass

    def set_color(self, hex_code):
        self.text_color = hex_code
        self.time_label.config(fg=self.text_color)
        self.save_config()

    def update_time(self):
        current_time = time.strftime("%I:%M %p")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)


if __name__ == "__main__":
    root = tk.Tk()
    app = TransparentClock(root)
    root.mainloop()