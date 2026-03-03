import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os
import shutil
import subprocess
import time
import threading

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, 'scripts', 'products.js')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
LOG_FILE = os.path.join(BASE_DIR, 'sync_status.log')

if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

class PremiumStoreManager:
    def __init__(self, root):
        self.root = root
        self.root.title("ORIGINAL-MED | Premium Dashboard")
        self.root.geometry("1100x800")
        self.root.configure(bg="#0f172a") # Deep Slate

        # Premium Palette
        self.colors = {
            "bg": "#0f172a",
            "sidebar": "#1e293b",
            "sidebar_active": "#334155",
            "card": "#ffffff",
            "primary": "#6366f1", # Indigo
            "secondary": "#818cf8",
            "success": "#10b981",
            "danger": "#ef4444",
            "text_main": "#1e293b",
            "text_muted": "#64748b",
            "text_light": "#f8fafc",
            "border": "#e2e8f0"
        }

        # App State
        self.products = []
        self.categories = []
        self.selected_images = []
        self.current_page = "inventory" # or "categories"
        self.sync_status = "Cloud Ready"
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_product_table())

        self.setup_styles()
        self.create_layout()
        self.setup_bindings()
        self.load_data()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Modern Treeview
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=35, background="white", fieldbackground="white", borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#f1f5f9", foreground="#1e293b", relief="flat")
        style.map("Treeview", background=[('selected', self.colors["primary"])], foreground=[('selected', 'white')])

        # Custom Scrollbar
        style.configure("TScrollbar", gripcount=0, background=self.colors["sidebar"], bordercolor=self.colors["sidebar"], darkcolor=self.colors["sidebar"], lightcolor=self.colors["sidebar"])

    def create_layout(self):
        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar"], width=240)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar Logo/Title
        tk.Label(self.sidebar, text="ORIGINAL-MED", font=("Segoe UI", 16, "bold"), bg=self.colors["sidebar"], fg="white", pady=30).pack()

        # Nav Buttons
        self.nav_items = {
            "inventory": self.create_nav_btn("📦 إدارة المخزون", "inventory"),
            "categories": self.create_nav_btn("📂 إدارة الأقسام", "categories")
        }
        self.update_nav_ui()

        # Cloud Status in Sidebar
        self.status_lbl = tk.Label(self.sidebar, text=f"● {self.sync_status}", font=("Segoe UI", 9), bg=self.colors["sidebar"], fg=self.colors["success"])
        self.status_lbl.pack(side="bottom", pady=20)

        # Main Content Area
        self.main_content = tk.Frame(self.root, bg=self.colors["bg"])
        self.main_content.pack(side="right", fill="both", expand=True)

        self.show_page("inventory")

    def create_nav_btn(self, text, code):
        btn = tk.Button(self.sidebar, text=text, font=("Segoe UI", 11), bg=self.colors["sidebar"], fg="#94a3b8", relief="flat", anchor="w", padx=30, pady=12, cursor="hand2", activebackground=self.colors["sidebar_active"], activeforeground="white", command=lambda: self.show_page(code))
        btn.pack(fill="x")
        return btn

    def update_nav_ui(self):
        for code, btn in self.nav_items.items():
            if code == self.current_page:
                btn.config(bg=self.colors["sidebar_active"], fg="white")
            else:
                btn.config(bg=self.colors["sidebar"], fg="#94a3b8")

    def show_page(self, page_code):
        self.current_page = page_code
        self.update_nav_ui()
        
        for w in self.main_content.winfo_children(): w.destroy()

        if page_code == "inventory":
            self.render_inventory()
        else:
            self.render_categories()

    def render_inventory(self):
        # Header / Search Bar
        top_bar = tk.Frame(self.main_content, bg=self.colors["bg"], pady=10, padx=20)
        top_bar.pack(fill="x")
        
        tk.Label(top_bar, text="قائمة المنتجات", font=("Segoe UI Arabic", 14, "bold"), bg=self.colors["bg"], fg="white").pack(side="right")
        
        s_f = tk.Frame(top_bar, bg="white", padx=10, pady=5)
        s_f.pack(side="left", fill="x", expand=True, padx=(0, 40))
        tk.Label(s_f, text="🔍", bg="white").pack(side="left")
        ent_s = tk.Entry(s_f, textvariable=self.search_var, font=("Segoe UI", 10), borderwidth=0, relief="flat", width=40)
        ent_s.pack(side="left", padx=10, fill="x", expand=True)
        self.attach_context_menu(ent_s)

        # Content Split (Table on Left, Form Card on Right)
        container = tk.Frame(self.main_content, bg=self.colors["bg"], padx=20, pady=5)
        container.pack(fill="both", expand=True)

        pane = tk.PanedWindow(container, orient=tk.HORIZONTAL, bg=self.colors["bg"], sashwidth=6, relief="flat")
        pane.pack(fill="both", expand=True)

        # Table Section
        tbl_card = tk.Frame(pane, bg="white", highlightthickness=1, highlightbackground="#e2e8f0")
        
        cols = ("id", "name", "price", "stock", "cat")
        self.tree = ttk.Treeview(tbl_card, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="المنتج")
        self.tree.heading("price", text="السعر")
        self.tree.heading("stock", text="المخزون")
        self.tree.heading("cat", text="القسم")
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=220, anchor="e")
        self.tree.column("price", width=80, anchor="center")
        self.tree.column("stock", width=70, anchor="center")
        self.tree.column("cat", width=90, anchor="center")

        sb = ttk.Scrollbar(tbl_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)

        # Form Section (Scrollable Card)
        form_container = tk.Frame(pane, bg=self.colors["bg"])
        form_card = tk.Frame(form_container, bg="white", padx=20, pady=20, highlightthickness=1, highlightbackground="#e2e8f0")
        form_card.pack(fill="both", expand=True, padx=(10, 0))

        # We'll put a canvas inside form_card just in case it's long
        self.f_canvas = tk.Canvas(form_card, bg="white", highlightthickness=0)
        f_sb = ttk.Scrollbar(form_card, orient="vertical", command=self.f_canvas.yview)
        self.inner_form = tk.Frame(self.f_canvas, bg="white")

        self.inner_form.bind("<Configure>", lambda e: self.f_canvas.configure(scrollregion=self.f_canvas.bbox("all")))
        self.f_canvas.create_window((0, 0), window=self.inner_form, anchor="nw", width=400)
        self.f_canvas.configure(yscrollcommand=f_sb.set)

        self.f_canvas.pack(side="left", fill="both", expand=True)
        f_sb.pack(side="right", fill="y")

        self.build_product_fields(self.inner_form)

        pane.add(tbl_card, width=600)
        pane.add(form_container, width=450)
        self.refresh_product_table()

    def build_product_fields(self, target):
        def lbl(txt): tk.Label(target, text=txt, font=("Segoe UI Arabic", 10), bg="white", fg=self.colors["text_muted"]).pack(anchor="e", pady=(10, 2))
        def ent(var): 
            e = tk.Entry(target, textvariable=var, font=("Segoe UI", 10), justify="right", relief="flat", highlightthickness=1, highlightbackground=self.colors["border"])
            e.pack(fill="x", pady=2, ipady=5)
            self.attach_context_menu(e)
            return e

        self.p_name = tk.StringVar(); lbl("اسم المنتج:"); ent(self.p_name)
        
        self.p_cat = tk.StringVar(); lbl("القسم:"); 
        self.p_cat_box = ttk.Combobox(target, textvariable=self.p_cat, state="readonly", font=("Segoe UI", 10), justify="right")
        self.p_cat_box.pack(fill="x", pady=2, ipady=3)
        self.p_cat_box['values'] = [c["name"] for c in self.categories]

        grid_f = tk.Frame(target, bg="white")
        grid_f.pack(fill="x")
        
        self.p_price = tk.StringVar()
        self.p_old_price = tk.StringVar()
        self.p_stock = tk.StringVar()

        tk.Label(grid_f, text="السعر الحالي", bg="white").grid(row=0, column=2, sticky="e", padx=5)
        tk.Entry(grid_f, textvariable=self.p_price, width=12, justify="center", highlightthickness=1, highlightbackground=self.colors["border"]).grid(row=1, column=2, padx=5, pady=5)
        
        tk.Label(grid_f, text="السعر السابق", bg="white").grid(row=0, column=1, sticky="e", padx=5)
        tk.Entry(grid_f, textvariable=self.p_old_price, width=12, justify="center", highlightthickness=1, highlightbackground=self.colors["border"]).grid(row=1, column=1, padx=5, pady=5)

        tk.Label(grid_f, text="المخزون", bg="white").grid(row=0, column=0, sticky="e", padx=5)
        tk.Entry(grid_f, textvariable=self.p_stock, width=12, justify="center", highlightthickness=1, highlightbackground=self.colors["border"]).grid(row=1, column=0, padx=5, pady=5)

        lbl("وصف المنتج:"); 
        self.p_desc = tk.Text(target, height=4, font=("Segoe UI", 10), relief="flat", highlightthickness=1, highlightbackground=self.colors["border"])
        self.p_desc.pack(fill="x", pady=2)
        self.attach_context_menu(self.p_desc)

        lbl("الصور:");
        self.img_box = tk.Listbox(target, height=3, font=("Segoe UI", 9), borderwidth=0, highlightthickness=1)
        self.img_box.pack(fill="x", pady=2)
        
        btn_f = tk.Frame(target, bg="white", pady=10)
        btn_f.pack(fill="x")
        tk.Button(btn_f, text="➕ إضافة صور", command=self.add_imgs, bg=self.colors["secondary"], fg="white", relief="flat", padx=10).pack(side="right")
        tk.Button(btn_f, text="🗑️ حذف صورة", command=self.del_img, bg=self.colors["danger"], fg="white", relief="flat", padx=10).pack(side="left")

        # Massive Save Button
        tk.Button(target, text="تحديث وحفظ التعديلات", command=self.save_product, bg=self.colors["primary"], fg="white", font=("Segoe UI", 11, "bold"), pady=10, relief="flat", cursor="hand2").pack(fill="x", pady=(20, 5))
        tk.Button(target, text="إضافة كمنتج جديد", command=self.add_product, bg=self.colors["success"], fg="white", font=("Segoe UI", 11, "bold"), pady=8, relief="flat", cursor="hand2").pack(fill="x", pady=5)
        
        del_f = tk.Frame(target, bg="white")
        del_f.pack(fill="x", pady=10)
        tk.Button(del_f, text="حذف المنتج", command=self.del_product, bg="#94a3b8", fg="white", relief="flat", width=15).pack(side="left")
        tk.Button(del_f, text="تفريغ الحقول", command=self.clear_fields, bg="#64748b", fg="white", relief="flat", width=15).pack(side="right")

    def render_categories(self):
        container = tk.Frame(self.main_content, bg=self.colors["bg"], padx=40, pady=40)
        container.pack(fill="both", expand=True)

        tk.Label(container, text="إدارة أقسام المتجر", font=("Segoe UI Arabic", 18, "bold"), bg=self.colors["bg"], fg="white").pack(anchor="e")

        main_card = tk.Frame(container, bg="white", padx=30, pady=30, highlightthickness=1, highlightbackground="#e2e8f0")
        main_card.pack(fill="both", expand=True, pady=20)

        split = tk.PanedWindow(main_card, orient=tk.HORIZONTAL, bg="white", sashwidth=4, relief="flat")
        split.pack(fill="both", expand=True)

        # Left List
        l_side = tk.Frame(split, bg="white")
        self.cat_list = tk.Listbox(l_side, font=("Segoe UI", 11), borderwidth=0, highlightthickness=1, highlightbackground="#f1f5f9")
        self.cat_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.cat_list.bind("<<ListboxSelect>>", self.on_cat_select)
        
        # Right Form
        r_side = tk.Frame(split, bg="white", padx=40)
        
        tk.Label(r_side, text="اسم القسم:", bg="white").pack(anchor="e")
        self.cat_name_var = tk.StringVar()
        tk.Entry(r_side, textvariable=self.cat_name_var, font=("Segoe UI", 12), justify="right").pack(fill="x", pady=10)
        
        self.cat_img_label = tk.Label(r_side, text="لا توجد صورة", bg="#f8fafc", height=5, highlightthickness=1)
        self.cat_img_label.pack(fill="x", pady=20)
        tk.Button(r_side, text="📷 تغيير الصورة", command=self.pick_cat_img, bg=self.colors["secondary"], fg="white", relief="flat").pack(fill="x")

        tk.Button(r_side, text="حفظ التغييرات في القسم", command=self.save_category, bg=self.colors["primary"], fg="white", font=("Segoe UI", 11, "bold"), pady=10).pack(fill="x", pady=(40, 5))
        
        cb_f = tk.Frame(r_side, bg="white")
        cb_f.pack(fill="x")
        tk.Button(cb_f, text="حذف القسم", command=self.del_category, bg="#94a3b8", fg="white", width=12).pack(side="left")
        tk.Button(cb_f, text="تفريغ", command=self.clear_cat_fields, bg="#cbd5e1", fg="white", width=12).pack(side="right")

        split.add(l_side, width=250)
        split.add(r_side, width=500)
        self.refresh_cat_list()

    # --- Data Operations ---
    def load_data(self):
        if not os.path.exists(PRODUCTS_FILE): return
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f: content = f.read()
            p_match = re.search(r'var products = (\[.*?\]);', content, re.DOTALL)
            c_match = re.search(r'var categories = (\[.*?\]);', content, re.DOTALL)
            
            def scrub(js):
                js = re.sub(r'(\w+):\s', r'"\1": ', js)
                js = re.sub(r',\s*]', ']', js)
                js = re.sub(r',\s*}', '}', js)
                return json.loads(js)

            if p_match: self.products = scrub(p_match.group(1))
            if c_match: self.categories = scrub(c_match.group(1))
            
            if self.current_page == "inventory": self.refresh_product_table()
        except: pass

    def refresh_product_table(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.search_var.get().lower()
        for p in self.products:
            if q and q not in p["name"].lower() and q not in str(p["id"]): continue
            cn = next((c["name"] for c in self.categories if c["id"] == p.get("category_id")), "-")
            self.tree.insert("", "end", values=(p["id"], p["name"], f"{p['price']} ج.م", p.get("stock",0), cn))

    def on_product_select(self, e):
        sel = self.tree.focus()
        if not sel: return
        pid = int(self.tree.item(sel, 'values')[0])
        p = next((x for x in self.products if x["id"] == pid), None)
        if p:
            self.p_name.set(p["name"])
            self.p_price.set(p["price"])
            self.p_old_price.set(p.get("old_price", ""))
            self.p_stock.set(p.get("stock", "0"))
            self.p_desc.delete("1.0", tk.END); self.p_desc.insert("1.0", p["description"])
            self.selected_images = p.get("images", [])
            self.img_box.delete(0, tk.END)
            for im in self.selected_images: self.img_box.insert(tk.END, os.path.basename(im))
            cn = next((c["name"] for c in self.categories if c["id"] == p.get("category_id")), "")
            self.p_cat.set(cn)

    def get_form_data(self):
        name = self.p_name.get().strip()
        price_str = re.sub(r'[^\d]', '', self.p_price.get())
        if not name or not price_str: return None
        
        try:
            p = int(price_str)
            o = int(re.sub(r'[^\d]', '', self.p_old_price.get())) if self.p_old_price.get() else None
            s = int(re.sub(r'[^\d]', '', self.p_stock.get())) if self.p_stock.get() else 0
        except: return None

        cid = next((c["id"] for c in self.categories if c["name"] == self.p_cat.get()), None)
        
        final_imgs = []
        for im in self.selected_images:
            if im.startswith("http") or im.startswith("assets/"):
                final_imgs.append(im)
            else:
                try:
                    fn = os.path.basename(im)
                    dst = os.path.join(ASSETS_DIR, fn)
                    if not (os.path.exists(dst) and os.path.samefile(im, dst)):
                        shutil.copy(im, dst)
                    final_imgs.append(f"assets/{fn}")
                except: final_imgs.append(im)

        return {
            "name": name, "price": p, "old_price": o, "stock": s,
            "description": self.p_desc.get("1.0", tk.END).strip(),
            "category_id": cid, "images": final_imgs, "image": final_imgs[0] if final_imgs else ""
        }

    def save_product(self):
        sel = self.tree.focus()
        if not sel: return
        data = self.get_form_data()
        if not data: return
        pid = int(self.tree.item(sel, 'values')[0])
        p = next((x for x in self.products if x["id"] == pid), None)
        if p:
            p.update(data)
            self.finish_operation("تم تحديث المنتج")

    def add_product(self):
        data = self.get_form_data()
        if not data: return
        data["id"] = max([x["id"] for x in self.products] or [0]) + 1
        self.products.append(data)
        self.finish_operation("تمت إضافة منتج جديد")

    def del_product(self):
        sel = self.tree.focus()
        if not sel: return
        if messagebox.askyesno("تأكيد", "هل تريد حذف هذا المنتج؟"):
            pid = int(self.tree.item(sel, 'values')[0])
            self.products = [x for x in self.products if x["id"] != pid]
            self.finish_operation("تم حذف المنتج")

    def finish_operation(self, msg):
        self.commit_to_js()
        self.refresh_product_table()
        self.trigger_auto_sync()
        messagebox.showinfo("نجاح", msg)

    def commit_to_js(self):
        js = f"var products = {json.dumps(self.products, ensure_ascii=True, indent=4)};\n"
        js += f"var categories = {json.dumps(self.categories, ensure_ascii=True, indent=4)};"
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f: f.write(js)
        
        # Cache Bust index.html
        try:
            idx = os.path.join(BASE_DIR, 'index.html')
            with open(idx, 'r', encoding='utf-8') as f: c = f.read()
            new_c = re.sub(r'src="scripts/products\.js(\?v=\d+)?"', f'src="scripts/products.js?v={int(time.time())}"', c)
            with open(idx, 'w', encoding='utf-8') as f: f.write(new_c)
        except: pass

    # --- Sync Engine ---
    def trigger_auto_sync(self):
        self.sync_status = "Syncing..."
        self.status_lbl.config(text=f"● {self.sync_status}", fg="#fbbf24")
        threading.Thread(target=self.run_sync_task, daemon=True).start()

    def run_sync_task(self):
        sh = os.path.join(BASE_DIR, 'publish_store_silent.bat')
        res = subprocess.run([sh], capture_output=True, text=True, creationflags=0x08000000)
        
        def update_ui():
            if res.returncode == 0:
                self.sync_status = "Online & Synced"
                self.status_lbl.config(text=f"● {self.sync_status}", fg=self.colors["success"])
            else:
                self.sync_status = "Sync Failed"
                self.status_lbl.config(text=f"● {self.sync_status}", fg=self.colors["danger"])
                # Only show error if explicitly requested or critical
        self.root.after(0, update_ui)

    # --- Categories Logic ---
    def refresh_cat_list(self):
        self.cat_list.delete(0, tk.END)
        for c in self.categories: self.cat_list.insert(tk.END, c["name"])

    def on_cat_select(self, e):
        sel = self.cat_list.curselection()
        if not sel: return
        name = self.cat_list.get(sel[0])
        cat = next((c for c in self.categories if c["name"] == name), None)
        if cat:
            self.cat_name_var.set(cat["name"])
            self.cur_cat_img = cat.get("image", "")
            self.cat_img_label.config(text=os.path.basename(self.cur_cat_img) if self.cur_cat_img else "لا توجد صورة")

    def pick_cat_img(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.webp")])
        if f:
            self.cur_cat_img = f
            self.cat_img_label.config(text=os.path.basename(f))

    def save_category(self):
        name = self.cat_name_var.get().strip()
        if not name: return
        
        img_url = "https://via.placeholder.com/150"
        if hasattr(self, 'cur_cat_img') and self.cur_cat_img:
            if self.cur_cat_img.startswith("http") or self.cur_cat_img.startswith("assets/"):
                img_url = self.cur_cat_img
            else:
                fn = os.path.basename(self.cur_cat_img)
                shutil.copy(self.cur_cat_img, os.path.join(ASSETS_DIR, fn))
                img_url = f"assets/{fn}"

        sel = self.cat_list.curselection()
        if sel:
            old = self.cat_list.get(sel[0])
            cat = next((c for c in self.categories if c["name"] == old), None)
            if cat: cat["name"] = name; cat["image"] = img_url
        else:
            nid = max([c["id"] for c in self.categories] or [0]) + 1
            self.categories.append({"id": nid, "name": name, "image": img_url})
        
        self.commit_to_js()
        self.refresh_cat_list()
        self.trigger_auto_sync()
        messagebox.showinfo("نجاح", "تم حفظ القسم")

    def del_category(self):
        sel = self.cat_list.curselection()
        if not sel: return
        if messagebox.askyesno("تأكيد", "حذف القسم؟"):
            name = self.cat_list.get(sel[0])
            self.categories = [c for c in self.categories if c["name"] != name]
            self.commit_to_js()
            self.refresh_cat_list()
            self.trigger_auto_sync()

    def clear_cat_fields(self):
        self.cat_name_var.set(""); self.cat_img_label.config(text="لا توجد صورة"); self.cur_cat_img = None

    # --- Utilities ---
    def setup_bindings(self):
        self.root.bind_all("<Control-v>", lambda e: self.handle_paste())
        self.root.bind_all("<Control-V>", lambda e: self.handle_paste())
        self.root.bind_all("<Control-c>", lambda e: self.handle_copy())
        self.root.bind_all("<Control-C>", lambda e: self.handle_copy())
        self.root.bind_all("<Control-x>", lambda e: self.handle_cut())
        self.root.bind_all("<Control-X>", lambda e: self.handle_cut())
        self.root.bind_all("<Control-a>", lambda e: self.handle_select_all())
        self.root.bind_all("<Control-A>", lambda e: self.handle_select_all())

    def handle_paste(self):
        w = self.root.focus_get()
        if not isinstance(w, (tk.Entry, tk.Text)): return "break"
        try:
            txt = self.root.selection_get(selection='CLIPBOARD')
        except:
            try: txt = self.root.clipboard_get()
            except: 
                w.event_generate("<<Paste>>")
                return "break"
        if txt:
            try:
                if w.selection_present(): w.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except: pass
            w.insert(tk.INSERT, txt)
        return "break"

    def handle_copy(self):
        w = self.root.focus_get()
        if isinstance(w, (tk.Entry, tk.Text)): w.event_generate("<<Copy>>")
        return "break"

    def handle_cut(self):
        w = self.root.focus_get()
        if isinstance(w, (tk.Entry, tk.Text)): w.event_generate("<<Cut>>")
        return "break"

    def handle_select_all(self):
        w = self.root.focus_get()
        if isinstance(w, tk.Entry): w.selection_range(0, tk.END); w.icursor(tk.END)
        elif isinstance(w, tk.Text): w.tag_add(tk.SEL, "1.0", tk.END)
        return "break"

    def attach_context_menu(self, w):
        m = tk.Menu(w, tearoff=0)
        m.add_command(label="نسخ (Copy)", command=lambda: w.event_generate("<<Copy>>"))
        m.add_command(label="قص (Cut)", command=lambda: w.event_generate("<<Cut>>"))
        m.add_command(label="لصق (Paste)", command=self.handle_paste)
        m.add_separator()
        m.add_command(label="تحديد الكل", command=self.handle_select_all)
        w.bind("<Button-3>", lambda e: [w.focus_set(), m.post(e.x_root, e.y_root)])

    def add_imgs(self):
        fs = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.webp")])
        for f in fs:
            if f not in self.selected_images:
                self.selected_images.append(f)
                self.img_box.insert(tk.END, os.path.basename(f))

    def del_img(self):
        s = self.img_box.curselection()
        if s: self.selected_images.pop(s[0]); self.img_box.delete(s[0])

    def clear_fields(self):
        self.p_name.set(""); self.p_price.set(""); self.p_old_price.set(""); self.p_stock.set("")
        self.p_desc.delete("1.0", tk.END); self.selected_images = []; self.img_box.delete(0, tk.END)
        self.p_cat.set("")

if __name__ == "__main__":
    r = tk.Tk()
    app = PremiumStoreManager(r)
    r.mainloop()
