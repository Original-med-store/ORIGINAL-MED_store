import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os
import shutil
import subprocess
import time

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, 'scripts', 'products.js')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
# Radical Log Isolation: Move logs out of the workspace to avoid Git/File-Lock deadlocks
TEMP_LOG_DIR = os.path.join(os.environ.get('TEMP', BASE_DIR), 'original-med-logs')
if not os.path.exists(TEMP_LOG_DIR): os.makedirs(TEMP_LOG_DIR)
LOG_FILE = os.path.join(TEMP_LOG_DIR, 'publish_last.log')

if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

class StoreManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("مدير متجر ORIGINAL_MED - لوحة التحكم الاحترافية")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f1f5f9")

        # Professional Color Palette
        self.colors = {
            "bg": "#f1f5f9",
            "card": "#ffffff",
            "header": "#1e293b",
            "primary": "#4f46e5",
            "secondary": "#6366f1",
            "danger": "#ef4444",
            "success": "#10b981",
            "text_main": "#1e293b",
            "text_muted": "#64748b",
            "border": "#e2e8f0"
        }

        # Global Variables
        self.products = []
        self.categories = []
        self.selected_images = []
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_product_table())

        # Styling
        self.setup_styles()

        # Global Keyboard Bindings (Intelligent handling)
        # Global Keyboard Bindings (Direct and Robust)
        self.root.bind_all("<Control-v>", lambda e: self.handle_paste())
        self.root.bind_all("<Control-V>", lambda e: self.handle_paste())
        self.root.bind_all("<Control-c>", lambda e: self.handle_copy())
        self.root.bind_all("<Control-C>", lambda e: self.handle_copy())
        self.root.bind_all("<Control-x>", lambda e: self.handle_cut())
        self.root.bind_all("<Control-X>", lambda e: self.handle_cut())
        self.root.bind_all("<Control-a>", lambda e: self.handle_select_all())
        self.root.bind_all("<Control-A>", lambda e: self.handle_select_all())

        # Build UI
        self.create_header()
        self.create_body()
        
        # Initial Load
        self.load_data()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook Styling
        self.style.configure("TNotebook", background=self.colors["bg"], padding=0)
        self.style.configure("TNotebook.Tab", font=("Cairo", 11, "bold"), padding=[20, 10])
        
        # Treeview Styling
        self.style.configure("Treeview", font=("Cairo", 10), rowheight=35, background="white", fieldbackground="white")
        self.style.configure("Treeview.Heading", font=("Cairo", 10, "bold"), background="#e2e8f0")
        self.style.map("Treeview", background=[('selected', self.colors["primary"])])

    def create_header(self):
        header = tk.Frame(self.root, bg=self.colors["header"], height=70)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="لوحة تحكم ORIGINAL-MED", font=("Cairo", 18, "bold"), bg=self.colors["header"], fg="white").pack(side="right", padx=30, pady=15)

        btn_publish = tk.Button(header, text="نشر التعديلات الحالية", command=self.publish_changes, 
                              bg=self.colors["success"], fg="white", font=("Cairo", 10, "bold"), 
                              relief="flat", padx=20, cursor="hand2")
        btn_publish.pack(side="left", padx=30, pady=15)

    def create_body(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # Tabs
        self.products_tab = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.categories_tab = tk.Frame(self.notebook, bg=self.colors["bg"])

        self.notebook.add(self.products_tab, text=" إدارة المخزون ")
        self.notebook.add(self.categories_tab, text=" إدارة الأقسام ")

        self.setup_inventory_ui()
        self.setup_categories_ui()

    def setup_inventory_ui(self):
        pane = tk.PanedWindow(self.products_tab, orient=tk.HORIZONTAL, bg=self.colors["bg"], sashwidth=4, relief="flat")
        pane.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Left: List & Search ---
        left_side = tk.Frame(pane, bg=self.colors["bg"])
        
        # Search Box
        search_f = tk.Frame(left_side, bg=self.colors["bg"], pady=10)
        search_f.pack(fill="x")
        tk.Label(search_f, text="بحث:", font=("Cairo", 10), bg=self.colors["bg"]).pack(side="right", padx=5)
        ent_s = tk.Entry(search_f, textvariable=self.search_var, font=("Cairo", 10), relief="flat", highlightthickness=1, highlightbackground=self.colors["border"])
        ent_s.pack(side="right", fill="x", expand=True, padx=(0, 10))
        self.attach_context_menu(ent_s)

        # Table
        tbl_f = tk.Frame(left_side, bg="white", highlightthickness=1, highlightbackground=self.colors["border"])
        tbl_f.pack(fill="both", expand=True)
        
        cols = ("id", "name", "price", "stock", "category")
        self.tree = ttk.Treeview(tbl_f, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="اسم المنتج")
        self.tree.heading("price", text="السعر")
        self.tree.heading("stock", text="المخزون")
        self.tree.heading("category", text="القسم")
        
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=200, anchor="e")
        self.tree.column("price", width=80, anchor="center")
        self.tree.column("stock", width=80, anchor="center")
        self.tree.column("category", width=100, anchor="center")
        
        sb = ttk.Scrollbar(tbl_f, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_product_click)

        # --- Right: Form ---
        right_side = tk.Frame(pane, bg=self.colors["bg"])
        
        # Scrollable Area for Form
        self.p_canvas = tk.Canvas(right_side, bg=self.colors["bg"], highlightthickness=0)
        self.p_scroll = ttk.Scrollbar(right_side, orient="vertical", command=self.p_canvas.yview)
        self.p_frame = tk.Frame(self.p_canvas, bg=self.colors["bg"])

        self.p_frame.bind("<Configure>", lambda e: self.p_canvas.configure(scrollregion=self.p_canvas.bbox("all")))
        self.p_canvas.create_window((0, 0), window=self.p_frame, anchor="nw", width=420)
        self.p_canvas.configure(yscrollcommand=self.p_scroll.set)

        self.p_canvas.pack(side="left", fill="both", expand=True, padx=5)
        self.p_scroll.pack(side="right", fill="y")

        self.build_product_form(self.p_frame)

        pane.add(left_side, width=600)
        pane.add(right_side, width=450)

    def build_product_form(self, target):
        def section_head(text):
            f = tk.Frame(target, bg=self.colors["bg"])
            f.pack(fill="x", pady=(15, 5), padx=10)
            tk.Label(f, text=text, font=("Cairo", 11, "bold"), bg=self.colors["bg"], fg=self.colors["primary"]).pack(side="right")
            ttk.Separator(target, orient='horizontal').pack(fill='x', padx=10)

        # Basic Info
        section_head(" المعلومات الأساسية ")
        tk.Label(target, text="اسم المنتج:", font=("Cairo", 10), bg=self.colors["bg"]).pack(anchor="e", padx=15)
        self.name_var = tk.StringVar()
        en = tk.Entry(target, textvariable=self.name_var, justify="right", font=("Cairo", 10), highlightthickness=1, borderwidth=0, highlightbackground=self.colors["border"])
        en.pack(fill="x", padx=15, pady=5)
        self.attach_context_menu(en)

        tk.Label(target, text="القسم:", font=("Cairo", 10), bg=self.colors["bg"]).pack(anchor="e", padx=15)
        self.cat_var = tk.StringVar()
        self.cat_box = ttk.Combobox(target, textvariable=self.cat_var, state="readonly", font=("Cairo", 10), justify="right")
        self.cat_box.pack(fill="x", padx=15, pady=5)

        # Pricing & Stock
        section_head(" السعر والمخزون ")
        g = tk.Frame(target, bg=self.colors["bg"])
        g.pack(fill="x", padx=10, pady=5)
        
        for i, lbl in enumerate(["المخزون", "السعر السابق", "السعر الحالي"]):
             tk.Label(g, text=lbl, font=("Cairo", 9, "bold"), bg=self.colors["bg"]).grid(row=0, column=i, sticky="e", padx=5)
        
        self.stock_var = tk.StringVar()
        self.old_p_var = tk.StringVar()
        self.curr_p_var = tk.StringVar()

        ef_s = tk.Entry(g, textvariable=self.stock_var, width=10, justify="center", highlightthickness=1, borderwidth=0, highlightbackground=self.colors["border"])
        ef_o = tk.Entry(g, textvariable=self.old_p_var, width=10, justify="center", highlightthickness=1, borderwidth=0, highlightbackground=self.colors["border"])
        ef_c = tk.Entry(g, textvariable=self.curr_p_var, width=10, justify="center", highlightthickness=1, borderwidth=0, highlightbackground=self.colors["border"])

        ef_s.grid(row=1, column=0, padx=5, pady=5)
        ef_o.grid(row=1, column=1, padx=5, pady=5)
        ef_c.grid(row=1, column=2, padx=5, pady=5)
        for e in [ef_s, ef_o, ef_c]: self.attach_context_menu(e)

        # Description
        section_head(" وصف المنتج ")
        self.desc_box = tk.Text(target, height=5, font=("Cairo", 10), highlightthickness=1, borderwidth=0, highlightbackground=self.colors["border"])
        self.desc_box.pack(fill="x", padx=15, pady=5)
        self.attach_context_menu(self.desc_box)

        # Media
        section_head(" الصور والوسائط ")
        tk.Button(target, text=" إضافة صور منتج ", command=self.add_imgs, bg=self.colors["secondary"], fg="white", font=("Cairo", 9, "bold"), relief="flat").pack(fill="x", padx=15, pady=5)
        self.img_list = tk.Listbox(target, height=4, font=("Segoe UI", 9), borderwidth=0, highlightthickness=1, highlightbackground=self.colors["border"])
        self.img_list.pack(fill="x", padx=15, pady=5)
        tk.Button(target, text="حذف الصورة المختارة", command=self.del_img, bg=self.colors["danger"], fg="white", font=("Cairo", 8)).pack(anchor="w", padx=15)

        # Actions
        tk.Frame(target, height=20, bg=self.colors["bg"]).pack()
        tk.Button(target, text="حفظ التعديلات", command=self.save_p, bg=self.colors["primary"], fg="white", font=("Cairo", 11, "bold"), relief="flat", pady=10).pack(fill="x", padx=15, pady=5)
        tk.Button(target, text="إضافة كمنتج جديد", command=self.add_p, bg=self.colors["success"], fg="white", font=("Cairo", 11, "bold"), relief="flat", pady=8).pack(fill="x", padx=15, pady=5)
        
        b_f = tk.Frame(target, bg=self.colors["bg"])
        b_f.pack(fill="x", padx=15, pady=10)
        tk.Button(b_f, text="حذف المنتج", command=self.del_p, bg="#94a3b8", fg="white", relief="flat", width=15).pack(side="left")
        tk.Button(b_f, text="تفريغ الحقول", command=self.clear_p, bg="#64748b", fg="white", relief="flat", width=15).pack(side="right")

        # Global Mousewheel
        def bind_rec(w):
            w.bind("<MouseWheel>", self.on_mw)
            for c in w.winfo_children(): bind_rec(c)
        bind_rec(self.p_canvas)
        bind_rec(target)

    def setup_categories_ui(self):
        # Similar logic for categories
        pane = tk.PanedWindow(self.categories_tab, orient=tk.HORIZONTAL, bg=self.colors["bg"], sashwidth=4, relief="flat")
        pane.pack(fill="both", expand=True, padx=5, pady=5)

        l_f = tk.Frame(pane, bg="white", highlightthickness=1, highlightbackground=self.colors["border"])
        r_f = tk.Frame(pane, bg=self.colors["bg"])
        
        pane.add(l_f, width=300)
        pane.add(r_f, width=500)

        self.cat_list = tk.Listbox(l_f, font=("Cairo", 10), borderwidth=0, highlightthickness=0)
        self.cat_list.pack(fill="both", expand=True, padx=10, pady=10)
        self.cat_list.bind("<<ListboxSelect>>", self.on_cat_click)

        tk.Label(r_f, text="بيانات القسم", font=("Cairo", 12, "bold"), bg=self.colors["bg"], fg=self.colors["primary"]).pack(anchor="e", padx=25, pady=20)
        self.cat_name_v = tk.StringVar()
        tk.Entry(r_f, textvariable=self.cat_name_v, justify="right", font=("Cairo", 10)).pack(fill="x", padx=25)
        
        self.cat_img_l = tk.Label(r_f, text="لم يتم اختيار صورة", bg="white", height=3, highlightthickness=1, highlightbackground=self.colors["border"])
        self.cat_img_l.pack(fill="x", padx=25, pady=10)
        tk.Button(r_f, text="اختيار صورة القسم", command=self.pick_cat_img, bg=self.colors["secondary"], fg="white").pack(fill="x", padx=25)

        tk.Button(r_f, text="حفظ القسم", command=self.save_cat, bg=self.colors["primary"], fg="white", font=("Cairo", 11, "bold"), pady=8).pack(fill="x", padx=25, pady=(20,5))
        
        c_b_f = tk.Frame(r_f, bg=self.colors["bg"])
        c_b_f.pack(fill="x", padx=25, pady=5)
        tk.Button(c_b_f, text="حذف القسم", command=self.del_cat, bg="#94a3b8", fg="white", width=15).pack(side="left")
        tk.Button(c_b_f, text="تفريغ الحقول", command=self.clear_cat, bg="#64748b", fg="white", width=15).pack(side="right")

    # --- Logic ---
    def load_data(self):
        if not os.path.exists(PRODUCTS_FILE): return
        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            p_m = re.search(r'var products = (\[.*?\]);', content, re.DOTALL)
            c_m = re.search(r'var categories = (\[.*?\]);', content, re.DOTALL)
            
            def parse_js(js):
                js = re.sub(r'(\w+):\s', r'"\1": ', js)
                js = re.sub(r',\s*]', ']', js)
                js = re.sub(r',\s*}', '}', js)
                return json.loads(js)

            if p_m: self.products = parse_js(p_m.group(1))
            if c_m: self.categories = parse_js(c_m.group(1))
            
            self.refresh_product_table()
            self.refresh_cat_list()
        except Exception as e:
            messagebox.showerror("Error", f"Loading failed: {e}")

    def refresh_product_table(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.search_var.get().lower()
        for p in self.products:
            if q and q not in p["name"].lower() and q not in str(p["id"]): continue
            cn = next((c["name"] for c in self.categories if c["id"] == p.get("category_id")), "-")
            self.tree.insert("", "end", values=(p["id"], p["name"], p["price"], p.get("stock",0), cn))

    def refresh_cat_list(self):
        self.cat_list.delete(0, tk.END)
        for c in self.categories: self.cat_list.insert(tk.END, c["name"])
        self.cat_box['values'] = [c["name"] for c in self.categories]

    def on_product_click(self, e):
        sel = self.tree.focus()
        if not sel: return
        pid = int(self.tree.item(sel, 'values')[0])
        p = next((x for x in self.products if x["id"] == pid), None)
        if p:
            self.name_var.set(p["name"])
            self.curr_p_var.set(p["price"])
            self.old_p_var.set(p.get("old_price", ""))
            self.stock_var.set(p.get("stock", ""))
            self.desc_box.delete("1.0", tk.END)
            self.desc_box.insert("1.0", p["description"])
            c_n = next((c["name"] for c in self.categories if c["id"] == p.get("category_id")), "")
            self.cat_var.set(c_n)
            self.selected_images = p.get("images", [])
            self.img_list.delete(0, tk.END)
            for img in self.selected_images: self.img_list.insert(tk.END, os.path.basename(img))

    def get_data(self):
        name = self.name_var.get().strip()
        price = self.curr_p_var.get().strip()
        if not name or not price:
            messagebox.showwarning("تنبيه", "الاسم والسعر مطلوبان")
            return None
        
        # Numeric cleanup
        try:
            p = int(re.sub(r'[^\d]', '', price))
            o = int(re.sub(r'[^\d]', '', self.old_p_var.get())) if self.old_p_var.get() else None
            s = int(re.sub(r'[^\d]', '', self.stock_var.get())) if self.stock_var.get() else 0
        except:
            messagebox.showerror("خطأ", "يجب إدخال أرقام صحيحة للسعر والمخزون")
            return None

        cid = next((c["id"] for c in self.categories if c["name"] == self.cat_var.get()), None)
        
        # Process Media
        final_imgs = []
        for img in self.selected_images:
            if img.startswith("http") or img.startswith("assets/"):
                final_imgs.append(img)
            else:
                try:
                    fn = os.path.basename(img)
                    dst = os.path.join(ASSETS_DIR, fn)
                    if not os.path.samefile(img, dst): shutil.copy(img, dst)
                    final_imgs.append(f"assets/{fn}")
                except: final_imgs.append(img)
        
        return {
            "name": name, "price": p, "old_price": o, "stock": s,
            "description": self.desc_box.get("1.0", tk.END).strip(),
            "category_id": cid, "images": final_imgs, "image": final_imgs[0] if final_imgs else ""
        }

    def save_p(self):
        sel = self.tree.focus()
        if not sel: return
        data = self.get_data()
        if not data: return
        pid = int(self.tree.item(sel, 'values')[0])
        p = next((x for x in self.products if x["id"] == pid), None)
        if p:
            p.update(data)
            self.final_save()
            messagebox.showinfo("نجاح", "تم الحفظ بنجاح")

    def add_p(self):
        data = self.get_data()
        if not data: return
        data["id"] = max([x["id"] for x in self.products] or [0]) + 1
        self.products.append(data)
        self.final_save()
        messagebox.showinfo("نجاح", "تمت الإضافة")

    def del_p(self):
        sel = self.tree.focus()
        if not sel: return
        if messagebox.askyesno("تأكيد", "حذف المنتج؟"):
            pid = int(self.tree.item(sel, 'values')[0])
            self.products = [x for x in self.products if x["id"] != pid]
            self.final_save()

    def final_save(self):
        # Update File
        js = f"// Data\nvar products = {json.dumps(self.products, ensure_ascii=False, indent=4)};\n"
        js += f"var categories = {json.dumps(self.categories, ensure_ascii=False, indent=4)};"
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f: f.write(js)
        
        # Update Cache Busters
        try:
             idx = os.path.join(BASE_DIR, 'index.html')
             with open(idx, 'r', encoding='utf-8') as f: c = f.read()
             nc = re.sub(r'src="scripts/products\.js(\?v=\d+)?"', f'src="scripts/products.js?v={int(time.time())}"', c)
             with open(idx, 'w', encoding='utf-8') as f: f.write(nc)
        except: pass

        self.refresh_product_table()
        self.clear_p()

    def clear_p(self):
        self.name_var.set(""); self.curr_p_var.set(""); self.old_p_var.set(""); self.stock_var.set("")
        self.desc_box.delete("1.0", tk.END); self.selected_images = []; self.img_list.delete(0, tk.END)
        self.cat_var.set("")

    # --- Interaction Utils ---
    def on_mw(self, event):
        self.p_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def handle_paste(self):
        try:
            w = self.root.focus_get()
            if isinstance(w, (tk.Entry, tk.Text)):
                # Use Tcl's built-in clipboard selection for maximum compatibility
                try:
                    txt = self.root.selection_get(selection='CLIPBOARD')
                    if isinstance(w, tk.Entry):
                        w.insert(tk.INSERT, txt)
                    else:
                        w.insert(tk.INSERT, txt)
                except:
                    # Fallback to root.clipboard_get()
                    txt = self.root.clipboard_get()
                    w.insert(tk.INSERT, txt)
        except: pass
        return "break"

    def handle_copy(self):
        try:
            w = self.root.focus_get()
            if isinstance(w, (tk.Entry, tk.Text)):
                w.event_generate("<<Copy>>")
        except: pass
        return "break"

    def handle_cut(self):
        try:
            w = self.root.focus_get()
            if isinstance(w, (tk.Entry, tk.Text)):
                w.event_generate("<<Cut>>")
        except: pass
        return "break"

    def handle_select_all(self):
        try:
            w = self.root.focus_get()
            if isinstance(w, tk.Entry):
                w.selection_range(0, tk.END)
                w.icursor(tk.END)
            elif isinstance(w, tk.Text):
                w.tag_add(tk.SEL, "1.0", tk.END)
        except: pass
        return "break"

    def attach_context_menu(self, w):
        m = tk.Menu(w, tearoff=0, font=("Cairo", 10))
        m.add_command(label="نسخ (Copy)", command=lambda: w.event_generate("<<Copy>>"))
        m.add_command(label="قص (Cut)", command=lambda: w.event_generate("<<Cut>>"))
        m.add_command(label="لصق (Paste)", command=self.handle_paste)
        m.add_separator()
        m.add_command(label="تحديد الكل (Select All)", command=self.handle_select_all)
        
        def show_m(e):
            w.focus_set()
            m.post(e.x_root, e.y_root)
        
        w.bind("<Button-3>", show_m)

    def publish_changes(self):
        self.root.config(cursor="wait"); self.root.update()
        sh = os.path.join(BASE_DIR, 'publish_store_silent.bat')
        
        self.final_save()
        
        # Radical recovery: Deleting any old log before starting
        if os.path.exists(LOG_FILE):
            try: os.remove(LOG_FILE)
            except: pass

        r = subprocess.run([sh], capture_output=True, text=True, creationflags=0x08000000)
        self.root.config(cursor="")
        
        log_content = ""
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    log_content = f.read()
        except: pass

        if r.returncode == 0:
            messagebox.showinfo("نجاح", "تم الحفظ والنشر بنجاح على الموقع!")
        else:
            err_msg = r.stderr if r.stderr.strip() else (log_content if log_content.strip() else r.stdout)
            messagebox.showerror("خطأ في النشر الجذري", f"تعذر النشر التلقائي. تفاصيل العملية:\n\n{err_msg}")

    def on_cat_click(self, e):
        sel = self.cat_list.curselection()
        if not sel: return
        name = self.cat_list.get(sel[0])
        cat = next((c for c in self.categories if c["name"] == name), None)
        if cat:
            self.cat_name_v.set(cat["name"])
            self.cur_cat_img = cat.get("image", "")
            self.cat_img_l.config(text=os.path.basename(self.cur_cat_img) if self.cur_cat_img else "لا توجد صورة")

    def pick_cat_img(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.webp")])
        if f:
            self.cur_cat_img = f
            self.cat_img_l.config(text=os.path.basename(f))

    def save_cat(self):
        name = self.cat_name_v.get().strip()
        if not name: return
        
        # Process Category Image
        img_url = "https://via.placeholder.com/150"
        if hasattr(self, 'cur_cat_img') and self.cur_cat_img:
            if self.cur_cat_img.startswith("http") or self.cur_cat_img.startswith("assets/"):
                img_url = self.cur_cat_img
            else:
                try:
                    fn = os.path.basename(self.cur_cat_img)
                    dst = os.path.join(ASSETS_DIR, fn)
                    shutil.copy(self.cur_cat_img, dst)
                    img_url = f"assets/{fn}"
                except: img_url = self.cur_cat_img

        sel = self.cat_list.curselection()
        if sel: # Update
            old_name = self.cat_list.get(sel[0])
            cat = next((c for c in self.categories if c["name"] == old_name), None)
            if cat:
                cat["name"] = name
                cat["image"] = img_url
        else: # Add New
            new_id = max([c["id"] for c in self.categories] or [0]) + 1
            self.categories.append({"id": new_id, "name": name, "image": img_url})

        self.final_save()
        self.refresh_cat_list()
        messagebox.showinfo("نجاح", "تم حفظ القسم بنجاح")

    def del_cat(self):
        sel = self.cat_list.curselection()
        if not sel: return
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا القسم؟"):
            name = self.cat_list.get(sel[0])
            self.categories = [c for c in self.categories if c["name"] != name]
            self.final_save()
            self.refresh_cat_list()

    def clear_cat(self):
        self.cat_name_v.set("")
        self.cur_cat_img = None
        self.cat_img_l.config(text="لم يتم اختيار صورة")
        self.cat_list.selection_clear(0, tk.END)
    def add_imgs(self):
        fs = filedialog.askopenfilenames(filetypes=[("Images", "*.jpg;*.png;*.jpeg;*.webp")])
        for f in fs:
            if f not in self.selected_images:
                self.selected_images.append(f)
                self.img_list.insert(tk.END, os.path.basename(f))
    def del_img(self):
        s = self.img_list.curselection()
        if s: self.selected_images.pop(s[0]); self.img_list.delete(s[0])

if __name__ == "__main__":
    r = tk.Tk()
    app = StoreManagerApp(r)
    r.mainloop()
