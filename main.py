"""DINEFLOW: a beginner-friendly restaurant billing application built with Tkinter."""
from datetime import datetime
from pathlib import Path
import json
import math
import re
import shutil
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, filedialog

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

BASE_DIR = Path(__file__).resolve().parent
RECEIPTS_DIR = BASE_DIR / "receipts"
ASSETS_DIR = BASE_DIR / "assets"
MENU_FILE = BASE_DIR / "menu.json"
BG = "#F4F6F3"
WHITE = "#FFFFFF"
TEXT = "#23332F"
MUTED = "#78857F"
ACCENT = "#BC7054"
ACCENT_HOVER = "#A95D43"
BORDER = "#E2E9E5"
SOFT = "#F6EAE3"
PRIMARY = "#28594F"
PRIMARY_HOVER = "#1F473F"
MINT = "#E8F1EC"


def rounded_rectangle(canvas, x1, y1, x2, y2, radius=14, fill=WHITE,
                      outline=BORDER, width=1, tags=()):
    """Draw a genuinely rounded polygon on a Tk Canvas."""
    radius = max(0, min(radius, (x2 - x1) / 2, (y2 - y1) / 2))
    points = []
    corners = [
        (x2 - radius, y1 + radius, -90),
        (x2 - radius, y2 - radius, 0),
        (x1 + radius, y2 - radius, 90),
        (x1 + radius, y1 + radius, 180),
    ]
    for cx, cy, start in corners:
        for step in range(7):
            angle = math.radians(start + step * 15)
            points.extend((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return canvas.create_polygon(*points, smooth=False, fill=fill, outline=outline,
                                 width=width, joinstyle="round", tags=tags)


def rounded_surface(parent, fill=WHITE, outline=BORDER, radius=16):
    """Add a rounded card background behind the frame's inset contents."""
    parent.configure(bg=BG)
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0, bd=0, takefocus=0)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    def redraw(event):
        canvas.delete("surface")
        if event.width > 3 and event.height > 3:
            rounded_rectangle(canvas, 1, 1, event.width - 2, event.height - 2,
                              radius, fill, outline, tags="surface")

    canvas.bind("<Configure>", redraw)
    parent._surface_canvas = canvas

MENU = [
    ("Paneer Tikka", 220, "Starters", "🥘"), ("Veg Manchurian", 180, "Starters", "🥗"),
    ("Crispy Corn", 160, "Starters", "🌽"), ("Hara Bhara Kebab", 190, "Starters", "🍢"),
    ("Paneer Butter Masala", 260, "Main Course", "🍛"), ("Dal Makhani", 230, "Main Course", "🥣"),
    ("Kadai Paneer", 250, "Main Course", "🍲"), ("Mix Veg", 210, "Main Course", "🥘"),
    ("Butter Naan", 45, "Breads", "🫓"), ("Garlic Naan", 60, "Breads", "🫓"),
    ("Tandoori Roti", 25, "Breads", "🫓"), ("Jeera Rice", 160, "Rice", "🍚"),
    ("Veg Biryani", 220, "Rice", "🍚"), ("Steamed Rice", 120, "Rice", "🍚"),
    ("Fresh Lime Soda", 90, "Beverages", "🍋"), ("Cold Coffee", 130, "Beverages", "☕"),
    ("Masala Chaas", 60, "Beverages", "🥛"), ("Brownie", 120, "Desserts", "🍫"),
    ("Gulab Jamun", 80, "Desserts", "🍮"), ("Ice Cream", 100, "Desserts", "🍨"),
]
CATEGORIES = ["All", "Starters", "Main Course", "Breads", "Rice", "Beverages", "Desserts"]


def money(value):
    return f"₹{value:,.2f}"


class RestaurantBillingSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("DINEFLOW | Restaurant Billing Management System")
        self.root.geometry("1440x900")
        self.root.minsize(1100, 700)
        self.root.configure(bg=BG)
        self.order_number = 1
        self.cart = {}
        self.category = "All"
        self.menu_items = [{"name": n, "price": p, "category": c, "emoji": e, "image": ""}
                           for n, p, c, e in MENU]
        self._load_menu()
        self.menu_photos = []
        self.search_var = tk.StringVar()
        self.discount_var = tk.StringVar(value="0")
        self.clock_var = tk.StringVar()
        self.order_id_var = tk.StringVar(value=self.order_id())
        self.order_status_var = tk.StringVar(value="●  NEW ORDER")
        self.current_receipt = ""
        self._configure_styles()
        self.create_widgets()
        self.search_var.trace_add("write", lambda *_: self.search_menu())
        self.discount_var.trace_add("write", lambda *_: self.update_bill())
        self.update_clock()
        self.refresh_menu()
        self.update_bill()

    def order_id(self):
        return f"DF-{datetime.now():%y%m%d}-{self.order_number:03d}"

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=WHITE, fieldbackground=WHITE, foreground=TEXT,
                        rowheight=42, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#F1F4F1", foreground=MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat", padding=(10, 12))
        style.map("Treeview", background=[("selected", SOFT)], foreground=[("selected", TEXT)])
        style.configure("Vertical.TScrollbar", background=BG, troughcolor=BG, bordercolor=BG,
                        arrowcolor=MUTED)

    def create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        self.create_header()
        body = tk.Frame(self.root, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(8, 22))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=42, uniform="dashboard")
        body.grid_columnconfigure(1, weight=35, uniform="dashboard")
        body.grid_columnconfigure(2, weight=23, uniform="dashboard")
        self.create_menu_section(body)
        self.create_order_section(body)
        self.create_billing_section(body)

    def create_header(self):
        header = tk.Frame(self.root, bg=BG, height=94)
        rounded_surface(header, WHITE, BORDER, 18)
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(18, 0))
        header.grid_columnconfigure(1, weight=1)
        tk.Label(header, text="DINEFLOW", bg=WHITE, fg=ACCENT, font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w", padx=(22, 12), pady=(17, 0))
        tk.Label(header, text="Restaurant Billing Management System", bg=WHITE, fg=MUTED, font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=24, pady=(0, 17))
        self._flat_button(header, "About", self.show_about, "#F1F4F1", TEXT, hover_bg=MINT, font=("Segoe UI", 9, "bold"), padx=15, pady=9).grid(row=0, column=1, rowspan=2, sticky="e", padx=14)
        meta = tk.Frame(header, bg=WHITE)
        meta.grid(row=0, column=2, rowspan=2, sticky="e", padx=22)
        self.date_label = tk.Label(meta, text=datetime.now().strftime("%A, %d %B %Y"), bg=WHITE, fg=MUTED, font=("Segoe UI", 9))
        self.date_label.grid(row=0, column=0, sticky="e", pady=(14, 3))
        tk.Label(meta, textvariable=self.clock_var, bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="e")
        tk.Label(meta, textvariable=self.order_id_var, bg=MINT, fg=PRIMARY, font=("Segoe UI", 9, "bold"), padx=10, pady=7).grid(row=0, column=1, rowspan=2, padx=(20, 0))
        tk.Label(meta, textvariable=self.order_status_var, bg=WHITE, fg="#628A68", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, rowspan=2, padx=(18, 22))

    def update_clock(self):
        now = datetime.now()
        self.clock_var.set(now.strftime("%I:%M:%S %p"))
        self.date_label.config(text=now.strftime("%A, %d %B %Y"))
        self.root.after(1000, self.update_clock)

    def _panel(self, parent, column):
        panel = tk.Frame(parent, bg=BG)
        rounded_surface(panel, WHITE, BORDER, 18)
        panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 12, 0), pady=2)
        panel.grid_columnconfigure(0, weight=1)
        return panel

    def _section_title(self, parent, title, subtitle):
        box = tk.Frame(parent, bg=WHITE)
        box.grid(row=0, column=0, sticky="ew", padx=20, pady=(19, 10))
        tk.Label(box, text=title, bg=WHITE, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w")
        tk.Label(box, text=subtitle, bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))
        return box

    def create_menu_section(self, parent):
        panel = self._panel(parent, 0)
        self._section_title(panel, "EXPLORE MENU", "Fresh favourites, made to order")
        tools = tk.Frame(panel, bg=WHITE)
        tools.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        tools.grid_columnconfigure(0, weight=1)
        search_box = tk.Frame(tools, bg=BG)
        rounded_surface(search_box, "#F7F9F7", BORDER, 12)
        search_box.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(search_box, text="⌕", bg="#F7F9F7", fg=MUTED, font=("Segoe UI", 16)).pack(side="left", padx=(12, 5), pady=6)
        tk.Entry(search_box, textvariable=self.search_var, relief="flat", bd=0, highlightthickness=0, bg="#F7F9F7", fg=TEXT, insertbackground=PRIMARY, font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True, ipady=10, padx=(0, 12), pady=4)
        self.category_frame = tk.Frame(tools, bg=WHITE)
        self.category_frame.grid(row=1, column=0, sticky="ew")
        self.category_buttons = {}
        for i, category in enumerate(CATEGORIES):
            b = self._flat_button(self.category_frame, category, lambda c=category: self.filter_category(c), "#F1F4F1", MUTED, hover_bg=MINT, font=("Segoe UI", 8, "bold"), padx=11, pady=7)
            b.grid(row=i // 4, column=i % 4, padx=(0, 7), pady=(0, 5), sticky="w")
            self.category_buttons[category] = b
        self.filter_category("All")
        manage_bar = tk.Frame(tools, bg=WHITE)
        manage_bar.grid(row=2, column=0, sticky="ew", pady=(2, 10))
        tk.Label(manage_bar, text="MENU ITEMS", bg=WHITE, fg=MUTED, font=("Segoe UI", 8, "bold")).pack(side="left")
        self._flat_button(manage_bar, "＋  Add or edit items", lambda: self.open_menu_manager(), PRIMARY, WHITE, hover_bg=PRIMARY_HOVER, font=("Segoe UI", 8, "bold"), padx=12, pady=7).pack(side="right")
        area = tk.Frame(panel, bg=WHITE)
        area.grid(row=3, column=0, sticky="nsew", padx=(18, 8), pady=(0, 14))
        panel.grid_rowconfigure(3, weight=1)
        area.grid_rowconfigure(0, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self.menu_canvas = tk.Canvas(area, bg=WHITE, highlightthickness=0)
        scroll = ttk.Scrollbar(area, orient="vertical", command=self.menu_canvas.yview)
        self.menu_canvas.configure(yscrollcommand=scroll.set)
        self.menu_canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.menu_inner = tk.Frame(self.menu_canvas, bg=WHITE)
        self.menu_window = self.menu_canvas.create_window((0, 0), window=self.menu_inner, anchor="nw")
        self.menu_inner.bind("<Configure>", lambda e: self.menu_canvas.configure(scrollregion=self.menu_canvas.bbox("all")))
        self.menu_canvas.bind("<Configure>", lambda e: self.menu_canvas.itemconfigure(self.menu_window, width=e.width))
        self.menu_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _load_menu(self):
        """Load saved menu edits while retaining the built-in sample menu."""
        if not MENU_FILE.exists():
            return
        try:
            saved = json.loads(MENU_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, list) and all(isinstance(item, dict) and item.get("name") for item in saved):
                self.menu_items = saved
        except (OSError, ValueError, TypeError) as exc:
            messagebox.showwarning("Menu could not be loaded", f"The saved menu could not be read. Built-in items will be used.\n{exc}")

    def _save_menu(self):
        try:
            ASSETS_DIR.mkdir(parents=True, exist_ok=True)
            MENU_FILE.write_text(json.dumps(self.menu_items, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Menu could not be saved", f"Your menu changes could not be saved.\n{exc}")
            return False
        return True

    def _load_food_photo(self, image_path, size):
        if not image_path:
            return None
        path = Path(image_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        try:
            if Image and ImageTk:
                image = Image.open(path).convert("RGB")
                image.thumbnail(size)
                return ImageTk.PhotoImage(image)
            return tk.PhotoImage(file=str(path))
        except (OSError, tk.TclError):
            return None

    def open_menu_manager(self, selected_name=None):
        win = tk.Toplevel(self.root)
        win.title("Manage menu items | DINEFLOW")
        win.geometry("760x520")
        win.minsize(700, 470)
        win.configure(bg=BG)
        win.transient(self.root)
        win.grid_columnconfigure(0, weight=1)
        win.grid_columnconfigure(1, weight=1)
        win.grid_rowconfigure(2, weight=1)
        tk.Label(win, text="Manage menu", bg=BG, fg=TEXT, font=("Segoe UI", 18, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=22, pady=(18, 2))
        tk.Label(win, text="Add dishes, update prices and categories, or attach a food photo.", bg=BG, fg=MUTED, font=("Segoe UI", 9)).grid(row=1, column=0, columnspan=2, sticky="w", padx=22, pady=(0, 14))
        left = tk.Frame(win, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=2, column=0, sticky="nsew", padx=(20, 8), pady=(0, 20))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)
        tk.Label(left, text="YOUR DISHES", bg=WHITE, fg=MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=12)
        listing = ttk.Treeview(left, columns=("category", "price"), show="tree headings", selectmode="browse")
        listing.heading("#0", text="DISH")
        listing.heading("category", text="CATEGORY")
        listing.heading("price", text="PRICE")
        listing.column("#0", width=145)
        listing.column("category", width=105)
        listing.column("price", width=75, anchor="e")
        listing.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 10))
        right = tk.Frame(win, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=2, column=1, sticky="nsew", padx=(8, 20), pady=(0, 20))
        right.grid_columnconfigure(0, weight=1)
        tk.Label(right, text="DISH DETAILS", bg=WHITE, fg=MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 10))
        name_var, price_var = tk.StringVar(), tk.StringVar()
        category_var, image_var = tk.StringVar(value=CATEGORIES[1]), tk.StringVar()
        current = {"name": None}

        def add_field(label, row, variable):
            tk.Label(right, text=label, bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=row, column=0, sticky="w", padx=16, pady=(7, 3))
            entry = tk.Entry(right, textvariable=variable, relief="flat", bg="#F8F6F2", fg=TEXT, highlightbackground=BORDER, highlightthickness=1, font=("Segoe UI", 10))
            entry.grid(row=row + 1, column=0, sticky="ew", padx=16, ipady=8)

        add_field("Dish name", 1, name_var)
        add_field("Price (₹)", 3, price_var)
        tk.Label(right, text="Category", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=5, column=0, sticky="w", padx=16, pady=(7, 3))
        ttk.Combobox(right, textvariable=category_var, values=CATEGORIES[1:], state="readonly").grid(row=6, column=0, sticky="ew", padx=16, ipady=5)
        tk.Label(right, text="Food image", bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold")).grid(row=7, column=0, sticky="w", padx=16, pady=(7, 3))
        image_line = tk.Frame(right, bg=WHITE)
        image_line.grid(row=8, column=0, sticky="ew", padx=16)
        image_line.grid_columnconfigure(0, weight=1)
        tk.Entry(image_line, textvariable=image_var, state="readonly", relief="flat", bg="#F8F6F2", fg=MUTED, highlightbackground=BORDER, highlightthickness=1, font=("Segoe UI", 8)).grid(row=0, column=0, sticky="ew", ipady=8)

        def choose_image():
            path = filedialog.askopenfilename(parent=win, title="Choose a food image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")])
            if path:
                image_var.set(path)

        tk.Button(image_line, text="Browse…", command=choose_image, bg=SOFT, fg=ACCENT, relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8, "bold"), padx=10, pady=8).grid(row=0, column=1, padx=(6, 0))
        image_hint = tk.Label(right, text="Tip: install Pillow for JPEG and WebP images. PNG and GIF work without it.", bg=WHITE, fg=MUTED, font=("Segoe UI", 8), wraplength=300, justify="left")
        image_hint.grid(row=9, column=0, sticky="w", padx=16, pady=(4, 2))

        def populate():
            for iid in listing.get_children():
                listing.delete(iid)
            for item in self.menu_items:
                listing.insert("", "end", iid=item["name"], text=item["name"], values=(item["category"], money(item["price"])))

        def load_selected(_event=None):
            sel = listing.selection()
            if not sel:
                return
            item = next((i for i in self.menu_items if i["name"] == sel[0]), None)
            if item:
                current["name"] = item["name"]
                name_var.set(item["name"])
                price_var.set(str(item["price"]))
                category_var.set(item["category"])
                image_var.set(item.get("image", ""))

        listing.bind("<<TreeviewSelect>>", load_selected)

        def new_item():
            listing.selection_remove(listing.selection())
            current["name"] = None
            name_var.set("")
            price_var.set("")
            category_var.set(CATEGORIES[1])
            image_var.set("")

        def save_item():
            name = name_var.get().strip()
            try:
                price = float(price_var.get().strip())
                if price <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Check the price", "Enter a price greater than zero.", parent=win)
                return
            if not name:
                messagebox.showerror("Add a dish name", "Enter a name for this menu item.", parent=win)
                return
            old_name = current["name"]
            duplicate = any(i["name"].casefold() == name.casefold() and i["name"] != old_name for i in self.menu_items)
            if duplicate:
                messagebox.showerror("Dish already exists", "Each menu item needs a unique name.", parent=win)
                return
            chosen = image_var.get().strip()
            saved_image = ""
            if chosen:
                source = Path(chosen)
                if not source.is_absolute():
                    source = BASE_DIR / source
                if source.exists():
                    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(name).stem).strip("_") or "dish"
                    target = ASSETS_DIR / f"{safe}{source.suffix.lower()}"
                    if source.resolve() != target.resolve():
                        shutil.copy2(source, target)
                    saved_image = str(target.relative_to(BASE_DIR))
                elif not Path(chosen).is_absolute():
                    saved_image = chosen
            old_item = next((i for i in self.menu_items if i["name"] == old_name), None) if old_name else None
            emoji = old_item.get("emoji", "🍽️") if old_item else "🍽️"
            new_data = {"name": name, "price": price, "category": category_var.get(), "emoji": emoji, "image": saved_image}
            if old_item:
                self.menu_items[self.menu_items.index(old_item)] = new_data
                if old_name in self.cart:
                    self.cart[name] = self.cart.pop(old_name)
                    self.cart[name]["price"] = price
            else:
                self.menu_items.append(new_data)
            if self._save_menu():
                current["name"] = name
                populate()
                listing.selection_set(name)
                self.refresh_menu()
                self._refresh_order()
                self._notify(f"{name} saved to menu")

        def delete_item():
            name = current["name"]
            if not name:
                messagebox.showinfo("Choose a dish", "Select a menu item to remove.", parent=win)
                return
            if name in self.cart:
                messagebox.showwarning("Dish is in current order", "Remove this dish from the current order before deleting it from the menu.", parent=win)
                return
            if not messagebox.askyesno("Delete menu item", f"Remove {name} from the menu?", parent=win):
                return
            self.menu_items[:] = [i for i in self.menu_items if i["name"] != name]
            current["name"] = None
            self._save_menu()
            populate()
            new_item()
            self.refresh_menu()

        buttons = tk.Frame(right, bg=WHITE)
        buttons.grid(row=10, column=0, sticky="ew", padx=16, pady=14)
        buttons.grid_columnconfigure((0, 1), weight=1)
        tk.Button(buttons, text="＋  New item", command=new_item, bg="#F8F6F2", fg=TEXT, relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8, "bold"), pady=10).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        tk.Button(buttons, text="Save item", command=save_item, bg=ACCENT, fg=WHITE, activebackground=ACCENT_HOVER, relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8, "bold"), pady=10).grid(row=0, column=1, sticky="ew", padx=(5, 0))
        tk.Button(buttons, text="Delete selected dish", command=delete_item, bg=WHITE, fg="#A74840", relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 8, "bold"), pady=7).grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        populate()
        if selected_name and listing.exists(selected_name):
            listing.selection_set(selected_name)
            load_selected()

    def _on_mousewheel(self, event):
        if self.menu_canvas.winfo_exists():
            self.menu_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def filter_category(self, category):
        self.category = category
        for name, button in self.category_buttons.items():
            button.set_colors(PRIMARY if name == category else "#F1F4F1",
                              WHITE if name == category else MUTED)
        self.refresh_menu()

    def search_menu(self):
        self.refresh_menu()

    def refresh_menu(self):
        if not hasattr(self, "menu_inner"):
            return
        for child in self.menu_inner.winfo_children():
            child.destroy()
        term = self.search_var.get().strip().casefold()
        self.menu_photos.clear()
        matches = [item for item in self.menu_items if (self.category == "All" or item["category"] == self.category) and term in item["name"].casefold()]
        for col in range(2):
            self.menu_inner.grid_columnconfigure(col, weight=1, uniform="food")
        for idx, item in enumerate(matches):
            name, price, emoji = item["name"], item["price"], item["emoji"]
            row, col = divmod(idx, 2)
            card = tk.Canvas(self.menu_inner, bg=WHITE, height=112, highlightthickness=0, bd=0)
            card.grid(row=row, column=col, sticky="ew", padx=(0 if col == 0 else 7, 7 if col == 0 else 0), pady=(0, 10))
            card_content = tk.Frame(card, bg=WHITE)
            card_window = card.create_window(3, 3, anchor="nw", window=card_content)

            def draw_card(event, canvas=card, window=card_window):
                canvas.delete("card_surface")
                rounded_rectangle(canvas, 1, 1, event.width - 2, event.height - 2, 14,
                                  WHITE, BORDER, tags="card_surface")
                canvas.coords(window, 3, 3)
                canvas.itemconfigure(window, width=max(1, event.width - 6), height=max(1, event.height - 6))

            card.bind("<Configure>", draw_card)
            card_content.grid_columnconfigure(1, weight=1)
            photo = self._load_food_photo(item.get("image", ""), (60, 60))
            if photo:
                self.menu_photos.append(photo)
            art = tk.Label(card_content, text="" if photo else emoji, image=photo if photo else "", bg=SOFT, fg=ACCENT, font=("Segoe UI Emoji", 22), width=60 if photo else 3, height=60 if photo else 2)
            if photo:
                art.image = photo
            art.grid(row=0, column=0, rowspan=2, padx=(9, 11), pady=9)
            tk.Label(card_content, text=name, bg=WHITE, fg=TEXT, font=("Segoe UI", 9, "bold"), anchor="w", wraplength=150).grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=(13, 3))
            tk.Label(card_content, text=money(price), bg=WHITE, fg=ACCENT, font=("Segoe UI", 9, "bold")).grid(row=1, column=1, sticky="w", padx=(0, 5), pady=(0, 12))
            self._flat_button(card_content, "＋ Add", lambda n=name, p=price: self.add_item(n, p), MINT, PRIMARY, hover_bg="#DDEBE3", font=("Segoe UI", 8, "bold"), padx=10, pady=7).grid(row=0, column=2, rowspan=2, padx=9)
        if not matches:
            tk.Label(self.menu_inner, text="No dishes match your search.", bg=WHITE, fg=MUTED, font=("Segoe UI", 10), pady=30).grid(row=0, column=0, columnspan=2)

    def create_order_section(self, parent):
        panel = self._panel(parent, 1)
        panel.grid_rowconfigure(2, weight=1)
        self._section_title(panel, "CURRENT ORDER", "Review and adjust your selection")
        meta = tk.Frame(panel, bg=WHITE)
        meta.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        tk.Label(meta, textvariable=self.order_id_var, bg=MINT, fg=PRIMARY, font=("Segoe UI", 9, "bold"), padx=9, pady=6).pack(side="left")
        self.item_count_label = tk.Label(meta, text="0 items", bg=WHITE, fg=MUTED, font=("Segoe UI", 9))
        self.item_count_label.pack(side="right")
        table_frame = tk.Frame(panel, bg=WHITE)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=18)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(table_frame, columns=("item", "qty", "price", "total"), show="headings", selectmode="browse")
        for col, label, width, anchor in [("item", "ITEM", 160, "w"), ("qty", "QTY", 46, "center"), ("price", "PRICE", 78, "e"), ("total", "TOTAL", 85, "e")]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor=anchor, stretch=(col == "item"))
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_selection)
        self.empty_label = tk.Label(table_frame, text="Your order is waiting\n\nAdd a dish from the menu to get started.", bg=WHITE, fg=MUTED, font=("Segoe UI", 11), justify="center")
        self.empty_label.place(relx=.5, rely=.5, anchor="center")
        controls = tk.Frame(panel, bg=WHITE)
        controls.grid(row=3, column=0, sticky="ew", padx=18, pady=12)
        controls.grid_columnconfigure((0, 1, 2), weight=1)
        self._small_button(controls, "−  Decrease", self.decrease_quantity).grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._small_button(controls, "+  Increase", self.increase_quantity).grid(row=0, column=1, sticky="ew", padx=5)
        self._small_button(controls, "Remove", self.remove_item, fg="#A74840").grid(row=0, column=2, sticky="ew", padx=(5, 0))
        tk.Label(panel, text="Order date  ·  " + datetime.now().strftime("%d %b %Y"), bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).grid(row=4, column=0, sticky="w", padx=20, pady=(0, 16))

    def _small_button(self, parent, text, command, fg=MUTED):
        return self._flat_button(parent, text, command, "#F1F4F1", fg, hover_bg=MINT, font=("Segoe UI", 8, "bold"), pady=9)

    def _flat_button(self, parent, text, command, bg, fg, hover_bg=None, border=None,
                     font=("Segoe UI", 9, "bold"), padx=10, pady=10):
        """Draw a rounded, cross-platform button without a native square bevel."""
        font_obj = tkfont.Font(root=parent, font=font)
        width = font_obj.measure(text) + 2 * padx + 8
        height = font_obj.metrics("linespace") + 2 * pady + 6
        button = tk.Canvas(parent, width=width, height=height, bg=parent.cget("bg"),
                           highlightthickness=0, bd=0, takefocus=1, cursor="hand2")
        state = {"bg": bg, "fg": fg, "hover": False}
        label_id = button.create_text(width / 2, height / 2, text=text, fill=fg, font=font)

        def redraw(event=None):
            w = event.width if event else button.winfo_width()
            h = event.height if event else button.winfo_height()
            button.delete("button_shape")
            fill = (hover_bg or bg) if state["hover"] else state["bg"]
            if border:
                rounded_rectangle(button, 1, 1, w - 1, h - 1, min(14, h / 2),
                                  border, border, tags="button_shape")
                rounded_rectangle(button, 2, 2, w - 2, h - 2, min(13, h / 2),
                                  fill, fill, tags="button_shape")
            else:
                rounded_rectangle(button, 1, 1, w - 1, h - 1, min(14, h / 2),
                                  fill, fill, tags="button_shape")
            button.coords(label_id, w / 2, h / 2)
            button.tag_raise(label_id)

        def set_colors(new_bg, new_fg):
            state["bg"], state["fg"] = new_bg, new_fg
            button.itemconfigure(label_id, fill=new_fg)
            redraw()

        button.set_colors = set_colors
        button.bind("<Configure>", redraw)
        button.bind("<Enter>", lambda _e: (state.update(hover=True), redraw()))
        button.bind("<Leave>", lambda _e: (state.update(hover=False), redraw()))
        button.bind("<Button-1>", lambda _e: command())
        button.bind("<Return>", lambda _e: command())
        button.bind("<space>", lambda _e: command())
        redraw()
        return button

    def _selected_item(self):
        selected = self.tree.selection()
        return selected[0] if selected else None

    def on_selection(self, _event=None):
        pass

    def add_item(self, name, price):
        if name in self.cart:
            self.cart[name]["qty"] += 1
        else:
            self.cart[name] = {"price": price, "qty": 1}
        self._refresh_order()
        self._notify(f"{name} added to order")

    def increase_quantity(self):
        name = self._selected_item()
        if not name:
            messagebox.showinfo("Select an item", "Choose an order row before changing its quantity.")
            return
        self.cart[name]["qty"] += 1
        self._refresh_order()
        self.tree.selection_set(name)

    def decrease_quantity(self):
        name = self._selected_item()
        if not name:
            messagebox.showinfo("Select an item", "Choose an order row before changing its quantity.")
            return
        if self.cart[name]["qty"] > 1:
            self.cart[name]["qty"] -= 1
            self._refresh_order()
            self.tree.selection_set(name)
        else:
            messagebox.showinfo("Minimum quantity", "Quantity cannot go below 1. Use Remove to delete this item.")

    def remove_item(self):
        name = self._selected_item()
        if not name:
            messagebox.showinfo("Select an item", "Choose an order row before removing it.")
            return
        del self.cart[name]
        self._refresh_order()

    def _refresh_order(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        count = 0
        for name, data in self.cart.items():
            count += data["qty"]
            self.tree.insert("", "end", iid=name, values=(name, data["qty"], money(data["price"]), money(data["price"] * data["qty"])))
        self.item_count_label.config(text=f"{count} item{'s' if count != 1 else ''}")
        self.order_status_var.set("●  IN PROGRESS" if self.cart else "●  NEW ORDER")
        self.empty_label.place_forget() if self.cart else self.empty_label.place(relx=.5, rely=.5, anchor="center")
        self.update_bill()

    def _discount_percent(self, show_error=False):
        raw = self.discount_var.get().strip()
        if not raw:
            return 0.0
        try:
            value = float(raw)
        except ValueError:
            if show_error:
                messagebox.showerror("Invalid discount", "Enter a discount percentage from 0 to 100.")
            return None
        if not 0 <= value <= 100:
            if show_error:
                messagebox.showerror("Invalid discount", "Discount must be between 0% and 100%.")
            return None
        return value

    def calculate_total(self):
        subtotal = sum(item["price"] * item["qty"] for item in self.cart.values())
        gst = subtotal * 0.05
        percent = self._discount_percent()
        discount = subtotal * (percent or 0) / 100 if percent is not None else 0
        return subtotal, gst, discount, subtotal + gst - discount

    def update_bill(self):
        if not hasattr(self, "subtotal_value"):
            return
        subtotal, gst, discount, total = self.calculate_total()
        self.subtotal_value.config(text=money(subtotal))
        self.gst_value.config(text=money(gst))
        self.discount_value.config(text=f"− {money(discount)}")
        self.grand_total_value.config(text=money(total))

    def create_billing_section(self, parent):
        panel = self._panel(parent, 2)
        self._section_title(panel, "BILL SUMMARY", "A clear breakdown of this order")
        card = tk.Frame(panel, bg=BG)
        rounded_surface(card, "#FBFCFA", BORDER, 14)
        card.grid(row=1, column=0, sticky="new", padx=16, pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)
        self.subtotal_value = self._summary_row(card, "Subtotal")
        self.gst_value = self._summary_row(card, "GST  ·  5%")
        discount_line = tk.Frame(card, bg="#FBFCFA")
        discount_line.pack(fill="x", padx=15, pady=(12, 2))
        tk.Label(discount_line, text="Discount", bg="#FBFCFA", fg=TEXT, font=("Segoe UI", 10)).pack(side="left")
        tk.Label(discount_line, text="%", bg="#FBFCFA", fg=MUTED, font=("Segoe UI", 9)).pack(side="right", padx=(0, 5))
        self.discount_entry = tk.Entry(discount_line, textvariable=self.discount_var, width=6, justify="right", relief="flat", bg=WHITE, fg=TEXT, highlightbackground=BORDER, highlightthickness=1, font=("Segoe UI", 10))
        self.discount_entry.pack(side="right", ipady=5, padx=(0, 6))
        self.discount_value = self._summary_row(card, "Discount amount", fg=ACCENT)
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=15, pady=12)
        total_box = tk.Frame(card, bg=BG)
        rounded_surface(total_box, MINT, MINT, 12)
        total_box.pack(fill="x", padx=10, pady=(0, 12))
        tk.Label(total_box, text="GRAND TOTAL", bg=MINT, fg=PRIMARY, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(10, 2))
        self.grand_total_value = tk.Label(total_box, text=money(0), bg=MINT, fg=TEXT, font=("Segoe UI", 22, "bold"))
        self.grand_total_value.pack(anchor="w", padx=12, pady=(0, 10))
        self.discount_entry.bind("<FocusOut>", self._validate_discount_on_exit)
        actions = tk.Frame(panel, bg=WHITE)
        actions.grid(row=2, column=0, sticky="new", padx=16, pady=3)
        actions.grid_columnconfigure(0, weight=1)
        self._action_button(actions, "GENERATE BILL", self.generate_bill, PRIMARY, WHITE).pack(fill="x", pady=(0, 9), ipady=5)
        self._action_button(actions, "SAVE RECEIPT", self.save_receipt, "#F1F4F1", TEXT).pack(fill="x", pady=(0, 9), ipady=5)
        self._action_button(actions, "CLEAR ORDER", self.clear_order, WHITE, ACCENT, border=ACCENT).pack(fill="x", ipady=5)
        tk.Label(panel, text="Secure checkout  ·  Thank you for dining with us", bg=WHITE, fg=MUTED, font=("Segoe UI", 8), wraplength=240).grid(row=3, column=0, sticky="s", padx=12, pady=16)

    def _summary_row(self, parent, label, fg=TEXT):
        row = tk.Frame(parent, bg="#FBFCFA")
        row.pack(fill="x", padx=15, pady=(13, 0))
        tk.Label(row, text=label, bg="#FBFCFA", fg=fg, font=("Segoe UI", 10)).pack(side="left")
        value = tk.Label(row, text=money(0), bg="#FBFCFA", fg=fg, font=("Segoe UI", 10, "bold"))
        value.pack(side="right")
        return value

    def _action_button(self, parent, text, command, bg, fg, border=None):
        return self._flat_button(parent, text, command, bg, fg,
                                 hover_bg=ACCENT_HOVER if bg == ACCENT else PRIMARY_HOVER if bg == PRIMARY else SOFT,
                                 border=border, font=("Segoe UI", 9, "bold"), pady=11)

    def _validate_discount_on_exit(self, _event=None):
        if self._discount_percent(show_error=True) is None:
            self.discount_var.set("0")
            self.discount_entry.focus_set()

    def _notify(self, text):
        if hasattr(self, "toast") and self.toast.winfo_exists():
            self.toast.destroy()
        self.toast = tk.Label(self.root, text="✓  " + text, bg="#2E4737", fg=WHITE, font=("Segoe UI", 9, "bold"), padx=16, pady=10)
        self.toast.place(relx=.5, rely=.965, anchor="s")
        self.root.after(1600, lambda: self.toast.destroy() if self.toast.winfo_exists() else None)

    def generate_bill(self):
        if not self.cart:
            messagebox.showwarning("Empty order", "Add at least one dish before generating a bill.")
            return
        percent = self._discount_percent(show_error=True)
        if percent is None:
            self.discount_entry.focus_set()
            return
        self.current_receipt = self._build_receipt()
        win = tk.Toplevel(self.root)
        win.title("DINEFLOW | Receipt")
        win.geometry("520x700")
        win.minsize(460, 580)
        win.configure(bg=BG)
        top = tk.Frame(win, bg=WHITE)
        top.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(top, text="DINEFLOW", bg=WHITE, fg=ACCENT, font=("Segoe UI", 20, "bold")).pack(pady=(18, 0))
        tk.Label(top, text="Restaurant Billing Management System", bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(0, 12))
        text = tk.Text(top, wrap="none", bg=WHITE, fg=TEXT, font=("Courier New", 10), relief="flat", padx=20, pady=10)
        text.pack(fill="both", expand=True)
        text.insert("1.0", self.current_receipt)
        text.configure(state="disabled")
        tk.Button(top, text="SAVE RECEIPT AS .TXT", command=self.save_receipt, bg=ACCENT, fg=WHITE, relief="flat", cursor="hand2", font=("Segoe UI", 9, "bold"), pady=11).pack(fill="x", padx=18, pady=15)

    def _build_receipt(self):
        subtotal, gst, discount, total = self.calculate_total()
        stamp = datetime.now()
        bill_no = f"BILL-{stamp:%y%m%d-%H%M%S}"
        lines = ["=" * 44, "                 DINEFLOW", "       Restaurant Billing Management System", "=" * 44,
                 f"Bill No : {bill_no}", f"Order   : {self.order_id_var.get()}", f"Date    : {stamp:%d %b %Y  %I:%M %p}", "-" * 44,
                 f"{'ITEM':<22}{'QTY':>4}{'PRICE':>9}{'TOTAL':>9}", "-" * 44]
        for name, data in self.cart.items():
            lines.append(f"{name[:21]:<22}{data['qty']:>4}{data['price']:>9.2f}{data['qty']*data['price']:>9.2f}")
        lines.extend(["-" * 44, f"{'Subtotal':<30}{subtotal:>14.2f}", f"{'GST (5%)':<30}{gst:>14.2f}",
                      f"{'Discount':<30}{discount:>14.2f}", "=" * 44, f"{'GRAND TOTAL':<30}{total:>14.2f}",
                      "=" * 44, "          Thank you for dining with us!", "          We hope to see you again.", ""])
        return "\n".join(lines)

    def save_receipt(self):
        if not self.cart:
            messagebox.showwarning("Empty order", "Add items and generate a bill before saving a receipt.")
            return
        percent = self._discount_percent(show_error=True)
        if percent is None:
            return
        self.current_receipt = self._build_receipt()
        try:
            RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
            default_name = f"DINEFLOW_{datetime.now():%Y%m%d_%H%M%S}.txt"
            path = filedialog.asksaveasfilename(title="Save DINEFLOW receipt", initialdir=str(RECEIPTS_DIR), initialfile=default_name, defaultextension=".txt", filetypes=[("Text receipt", "*.txt")])
            if not path:
                return
            Path(path).write_text(self.current_receipt, encoding="utf-8")
            messagebox.showinfo("Receipt saved", f"Receipt saved successfully:\n{path}")
        except OSError as exc:
            messagebox.showerror("Save failed", f"Could not save the receipt.\n{exc}")

    def clear_order(self):
        if not self.cart:
            messagebox.showinfo("Order is empty", "There are no items to clear.")
            return
        if not messagebox.askyesno("Clear order", "Remove all items and start a new order?"):
            return
        self.cart.clear()
        self.order_number += 1
        self.order_id_var.set(self.order_id())
        self.current_receipt = ""
        self.discount_var.set("0")
        self._refresh_order()

    def show_about(self):
        win = tk.Toplevel(self.root)
        win.title("About DINEFLOW")
        win.geometry("430x470")
        win.resizable(False, False)
        win.configure(bg=BG)
        card = tk.Frame(win, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="DINEFLOW", bg=WHITE, fg=ACCENT, font=("Segoe UI", 22, "bold")).pack(pady=(24, 4))
        tk.Label(card, text="Restaurant Billing Management System", bg=WHITE, fg=MUTED, font=("Segoe UI", 10)).pack()
        tk.Label(card, text="Smart Billing. Seamless Dining.", bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "italic")).pack(pady=16)
        tk.Label(card, text="Developed by", bg=WHITE, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(pady=(5, 10))
        people = [("Srishti", "RA2511030010319"), ("Radhika", "RA2511030010348"), ("Manthan", "RA2511030010333")]
        for name, reg in people:
            tk.Label(card, text=name, bg=WHITE, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(pady=(3, 0))
            tk.Label(card, text=f"Registration Number: {reg}", bg=WHITE, fg=MUTED, font=("Segoe UI", 9)).pack(pady=(0, 4))


def main():
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    RestaurantBillingSystem(root)
    root.mainloop()


if __name__ == "__main__":
    main()
