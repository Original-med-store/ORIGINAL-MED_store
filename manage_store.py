import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import re
import os
import shutil
import subprocess

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PRODUCTS_FILE = os.path.join(BASE_DIR, 'scripts', 'products.js')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# Ensure assets directory exists
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

class StoreManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("مدير متجر ORIGINAL_MED - النسخة المطورة")
        self.root.geometry("1000x700") # Increased size
        self.root.configure(bg="#f8fafc")

        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Cairo", 11), background="#f8fafc")
        self.style.configure("TButton", font=("Cairo", 10, "bold"))
        self.style.configure("Treeview.Heading", font=("Cairo", 11, "bold"))
        self.style.configure("Treeview", font=("Cairo", 10), rowheight=35)

        self.categories = []

        # UI Components
        self.create_header()
        self.create_main_layout()
        
        # Load Data
        self.load_data()

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#0d9488", pady=15)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="لوحة تحكم المنتجات الاحترافية", bg="#0d9488", fg="white", font=("Cairo", 18, "bold"))
        title_label.pack()

    def create_main_layout(self):
        # Notebook for Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Tabs
        self.products_tab = tk.Frame(self.notebook, bg="#f8fafc")
        self.categories_tab = tk.Frame(self.notebook, bg="#f8fafc")

        self.notebook.add(self.products_tab, text="  إدارة المنتجات  ")
        self.notebook.add(self.categories_tab, text="  إدارة الأقسام  ")

        self.setup_products_tab()
        self.setup_categories_tab()

    # ==========================
    # Products Tab
    # ==========================
    def setup_products_tab(self):
        main_pane = tk.PanedWindow(self.products_tab, orient=tk.HORIZONTAL, bg="#f8fafc")
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        table_frame = tk.Frame(main_pane, bg="white")
        form_frame = tk.Frame(main_pane, bg="#f8fafc")
        
        main_pane.add(table_frame, width=500)
        main_pane.add(form_frame, width=450)

        self.create_product_table(table_frame)
        self.create_product_form(form_frame)

    def create_product_table(self, parent):
        columns = ("ID", "الاسم", "السعر", "السعر القديم", "القسم")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("الاسم", text="اسم المنتج")
        self.tree.heading("السعر", text="السعر الحالي")
        self.tree.heading("السعر القديم", text="السعر السابق")
        self.tree.heading("القسم", text="القسم")
        
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("الاسم", width=150, anchor="e")
        self.tree.column("السعر", width=80, anchor="center")
        self.tree.column("السعر القديم", width=80, anchor="center")
        self.tree.column("القسم", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_product_select)

    def create_product_form(self, parent):
        # Scrollable Form
        canvas = tk.Canvas(parent, bg="#f8fafc", highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f8fafc")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=430)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Content
        font_lbl = ("Cairo", 11, "bold")
        font_ent = ("Cairo", 10)

        # Name
        tk.Label(scrollable_frame, text="اسم المنتج:", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(10,0), padx=10)
        self.name_var = tk.StringVar()
        tk.Entry(scrollable_frame, textvariable=self.name_var, justify="right", font=font_ent).pack(fill="x", padx=10)

        # Category
        tk.Label(scrollable_frame, text="القسم:", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(10,0), padx=10)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(scrollable_frame, textvariable=self.category_var, state="readonly", font=font_ent, justify="right")
        self.category_combo.pack(fill="x", padx=10)

        # Prices Row
        price_frame = tk.Frame(scrollable_frame, bg="#f8fafc")
        price_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(price_frame, text="السعر الحالي:", font=font_lbl, bg="#f8fafc").pack(side="right")
        self.price_var = tk.StringVar()
        tk.Entry(price_frame, textvariable=self.price_var, justify="center", font=font_ent, width=10).pack(side="right", padx=5)

        tk.Label(price_frame, text="السعر السابق (للخصم):", font=font_lbl, bg="#f8fafc", fg="#dc2626").pack(side="right", padx=(10,0))
        self.old_price_var = tk.StringVar()
        tk.Entry(price_frame, textvariable=self.old_price_var, justify="center", font=font_ent, width=10).pack(side="right", padx=5)

        # Description
        tk.Label(scrollable_frame, text="الوصف:", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(10,0), padx=10)
        self.desc_text = tk.Text(scrollable_frame, height=4, font=font_ent)
        self.desc_text.pack(fill="x", padx=10)

        # Images
        tk.Label(scrollable_frame, text="صور المنتج (يمكن اختيار أكثر من صورة):", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(10,0), padx=10)
        btn_img = tk.Button(scrollable_frame, text="إضافة صور", command=self.choose_images, bg="#3b82f6", fg="white", font=("Cairo", 10))
        btn_img.pack(anchor="e", padx=10, pady=5)
        
        self.images_listbox = tk.Listbox(scrollable_frame, height=4, font=("Segoe UI", 9))
        self.images_listbox.pack(fill="x", padx=10)
        
        btn_del_img = tk.Button(scrollable_frame, text="حذف الصورة المحددة", command=self.remove_selected_image, bg="#ef4444", fg="white", font=("Cairo", 9))
        btn_del_img.pack(anchor="w", padx=10, pady=2)

        # Separator
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', pady=20, padx=10)

        # Action Buttons
        btn_save = tk.Button(scrollable_frame, text="حفظ التعديلات ونشر", command=self.save_products, bg="#0d9488", fg="white", font=("Cairo", 12, "bold"), pady=5)
        btn_save.pack(fill="x", padx=10, pady=5)

        btn_add = tk.Button(scrollable_frame, text="إضافة منتج جديد", command=self.add_product, bg="#10b981", fg="white", font=("Cairo", 11, "bold"))
        btn_add.pack(fill="x", padx=10, pady=5)

        sub_btn_frame = tk.Frame(scrollable_frame, bg="#f8fafc")
        sub_btn_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Button(sub_btn_frame, text="حذف المنتج", command=self.delete_product, bg="#dc2626", fg="white").pack(side="left", fill="x", expand=True, padx=2)
        tk.Button(sub_btn_frame, text="تفريغ الحقول", command=self.clear_product_form, bg="#64748b", fg="white").pack(side="right", fill="x", expand=True, padx=2)

    # ==========================
    # Categories Tab
    # ==========================
    def setup_categories_tab(self):
        pane = tk.PanedWindow(self.categories_tab, orient=tk.HORIZONTAL, bg="#f8fafc")
        pane.pack(fill="both", expand=True, padx=10, pady=10)

        list_frame = tk.Frame(pane, bg="white")
        form_frame = tk.Frame(pane, bg="#f8fafc")
        
        pane.add(list_frame, width=300)
        pane.add(form_frame, width=500)

        # Category List
        self.cat_listbox = tk.Listbox(list_frame, font=("Cairo", 11), selectmode=tk.SINGLE)
        self.cat_listbox.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.cat_listbox.yview)
        self.cat_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.cat_listbox.bind("<<ListboxSelect>>", self.on_category_select)

        # Category Form
        font_lbl = ("Cairo", 11, "bold")
        font_ent = ("Cairo", 10)

        tk.Label(form_frame, text="اسم القسم:", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(20,0), padx=20)
        self.cat_name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.cat_name_var, justify="right", font=font_ent).pack(fill="x", padx=20)

        tk.Label(form_frame, text="صورة القسم:", font=font_lbl, bg="#f8fafc").pack(anchor="e", pady=(20,0), padx=20)
        self.cat_img_path = None
        self.cat_img_label = tk.Label(form_frame, text="لم يتم اختيار صورة", bg="#e2e8f0", height=2)
        self.cat_img_label.pack(fill="x", padx=20, pady=5)
        tk.Button(form_frame, text="اختار صورة", command=self.choose_cat_image, bg="#3b82f6", fg="white").pack(fill="x", padx=20)

        ttk.Separator(form_frame, orient='horizontal').pack(fill='x', pady=30, padx=20)

        tk.Button(form_frame, text="حفظ القسم", command=self.save_category, bg="#0d9488", fg="white", font=("Cairo", 12, "bold")).pack(fill="x", padx=20, pady=5)
        tk.Button(form_frame, text="حذف القسم", command=self.delete_category, bg="#ef4444", fg="white").pack(fill="x", padx=20, pady=5)
        tk.Button(form_frame, text="جديد / تفريغ", command=self.clear_cat_form, bg="#64748b", fg="white").pack(fill="x", padx=20, pady=5)


    # ==========================
    # Logic
    # ==========================
    def load_data(self):
        if not os.path.exists(PRODUCTS_FILE):
            return

        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            # Load Products
            p_match = re.search(r'var products = (\[.*?\]);', content, re.DOTALL)
            if p_match:
                json_str = p_match.group(1)
                json_str = re.sub(r'(\w+):\s', r'"\1": ', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                self.products = json.loads(json_str)

            # Load Categories
            c_match = re.search(r'var categories = (\[.*?\]);', content, re.DOTALL)
            if c_match:
                json_str = c_match.group(1)
                json_str = re.sub(r'(\w+):\s', r'"\1": ', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                self.categories = json.loads(json_str)
            
            self.refresh_product_table()
            self.refresh_cat_list()
            self.update_cat_combo()

        except Exception as e:
            messagebox.showerror("خطأ", f"Error loading data: {e}")

    def refresh_product_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        for product in self.products:
            old_p = product.get("old_price", "")
            cat_name = next((c["name"] for c in self.categories if c["id"] == product.get("category_id")), "غير محدد")
            self.tree.insert("", "end", values=(product.get("id"), product.get("name"), product.get("price"), old_p, cat_name))

    def refresh_cat_list(self):
        self.cat_listbox.delete(0, tk.END)
        for cat in self.categories:
            self.cat_listbox.insert(tk.END, cat["name"])

    def update_cat_combo(self):
        cat_names = [c["name"] for c in self.categories]
        self.category_combo['values'] = cat_names

    # --- Product Logic ---
    def on_product_select(self, event):
        selected = self.tree.focus()
        if not selected: return
        
        values = self.tree.item(selected, 'values')
        product_id = int(values[0])
        
        product = next((p for p in self.products if p["id"] == product_id), None)
        if product:
            self.name_var.set(product["name"])
            self.price_var.set(product["price"])
            self.old_price_var.set(product.get("old_price", ""))
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", product["description"])
            
            # Select Category
            cat_name = next((c["name"] for c in self.categories if c["id"] == product.get("category_id")), "")
            self.category_var.set(cat_name)

            # Handle Images
            self.selected_images = []
            self.images_listbox.delete(0, tk.END)
            
            if "images" in product and isinstance(product["images"], list):
                self.selected_images = product["images"]
            elif "image" in product:
                self.selected_images = [product["image"]]
            
            for img in self.selected_images:
                self.images_listbox.insert(tk.END, os.path.basename(img))

    def choose_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.jpg;*.png;*.jpeg;*.webp")])
        if file_paths:
            for path in file_paths:
                if path not in self.selected_images:
                    self.selected_images.append(path)
                    self.images_listbox.insert(tk.END, os.path.basename(path))

    def remove_selected_image(self):
        selection = self.images_listbox.curselection()
        if selection:
            idx = selection[0]
            self.images_listbox.delete(idx)
            del self.selected_images[idx]

    def clear_product_form(self):
        self.name_var.set("")
        self.price_var.set("")
        self.old_price_var.set("")
        self.category_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.selected_images = []
        self.images_listbox.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def get_product_form_data(self):
        name = self.name_var.get().strip()
        price = self.price_var.get().strip()
        old_price = self.old_price_var.get().strip()
        desc = self.desc_text.get("1.0", tk.END).strip()
        cat_name = self.category_var.get()
        
        if not name or not price:
            messagebox.showwarning("تنبيه", "الاسم والسعر مطلوبان")
            return None

        # Resolve Category ID
        cat_id = next((c["id"] for c in self.categories if c["name"] == cat_name), None)

        final_images = self.process_images(self.selected_images)
        main_image = final_images[0] if final_images else "https://via.placeholder.com/300"
        
        data = {
            "name": name,
            "price": int(price),
            "old_price": int(old_price) if old_price else None,
            "description": desc,
            "category_id": cat_id,
            "image": main_image,
            "images": final_images
        }
        return data

    def add_product(self):
        data = self.get_product_form_data()
        if not data: return

        new_id = max([p["id"] for p in self.products] or [0]) + 1
        data["id"] = new_id
        
        self.products.append(data)
        self.refresh_product_table()
        self.save_to_file()
        self.clear_product_form()
        messagebox.showinfo("نجاح", "تم إضافة المنتج بنجاح")

    def save_products(self):
        selected = self.tree.focus()
        if not selected: return

        product_id = int(self.tree.item(selected, 'values')[0])
        product = next((p for p in self.products if p["id"] == product_id), None)
        
        if product:
            data = self.get_product_form_data()
            if not data: return
            
            product.update(data)
            
            self.refresh_product_table()
            self.save_to_file()
            self.publish_changes()

    def delete_product(self):
        selected = self.tree.focus()
        if not selected: return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا المنتج؟"):
            product_id = int(self.tree.item(selected, 'values')[0])
            self.products = [p for p in self.products if p["id"] != product_id]
            self.refresh_product_table()
            self.save_to_file()
            self.clear_product_form()

    # --- Category Logic ---
    def on_category_select(self, event):
        selection = self.cat_listbox.curselection()
        if not selection: return
        
        cat_name = self.cat_listbox.get(selection[0])
        category = next((c for c in self.categories if c["name"] == cat_name), None)
        
        if category:
            self.cat_name_var.set(category["name"])
            self.cat_img_path = category["image"]
            self.cat_img_label.config(text=os.path.basename(category["image"]))

    def choose_cat_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png;*.jpeg;*.webp")])
        if path:
            self.cat_img_path = path
            self.cat_img_label.config(text=os.path.basename(path))

    def clear_cat_form(self):
        self.cat_name_var.set("")
        self.cat_img_path = None
        self.cat_img_label.config(text="لم يتم اختيار صورة")
        self.cat_listbox.selection_clear(0, tk.END)

    def save_category(self):
        name = self.cat_name_var.get().strip()
        if not name:
            messagebox.showwarning("تنبيه", "اسم القسم مطلوب")
            return

        # Process Image
        final_img = "https://via.placeholder.com/150"
        if self.cat_img_path:
             images = self.process_images([self.cat_img_path])
             if images: final_img = images[0]

        # Check if updating or adding
        selection = self.cat_listbox.curselection()
        if selection:
            # Update
            old_name = self.cat_listbox.get(selection[0])
            category = next((c for c in self.categories if c["name"] == old_name), None)
            if category:
                category["name"] = name
                category["image"] = final_img
        else:
            # Add New
            new_id = max([c["id"] for c in self.categories] or [0]) + 1
            self.categories.append({
                "id": new_id,
                "name": name,
                "image": final_img
            })

        self.refresh_cat_list()
        self.update_cat_combo()
        self.save_to_file()
        self.clear_cat_form()
        messagebox.showinfo("نجاح", "تم حفظ القسم")

    def delete_category(self):
        selection = self.cat_listbox.curselection()
        if not selection: return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا القسم؟"):
            name = self.cat_listbox.get(selection[0])
            self.categories = [c for c in self.categories if c["name"] != name]
            self.refresh_cat_list()
            self.update_cat_combo()
            self.save_to_file()
            self.clear_cat_form()

    # --- Common ---
    def process_images(self, image_list):
        processed_images = []
        for img_path in image_list:
            if img_path.startswith("http") or img_path.startswith("assets/"):
                processed_images.append(img_path)
            else:
                try:
                    filename = os.path.basename(img_path)
                    dest_path = os.path.join(ASSETS_DIR, filename)
                    shutil.copy(img_path, dest_path)
                    processed_images.append(f"assets/{filename}")
                except Exception as e:
                    print(f"Error copying image {img_path}: {e}")
        
        if not processed_images:
             processed_images.append("https://via.placeholder.com/300")
        return processed_images

    def save_to_file(self):
        js_content = "// ==========================================\n"
        js_content += "//  ملف بيانات المنتجات (محدث)\n"
        js_content += "// ==========================================\n"
        js_content += "var products = " + json.dumps(self.products, ensure_ascii=False, indent=4) + ";\n\n"
        js_content += "var categories = " + json.dumps(self.categories, ensure_ascii=False, indent=4) + ";"
        
        # Update index.html version for caching
        import time
        try:
            index_path = os.path.join(BASE_DIR, 'index.html')
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r'scripts/products.js(\?v=\d+)?', f'scripts/products.js?v={int(time.time())}', content)
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except: pass

        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            f.write(js_content)

if __name__ == "__main__":
    root = tk.Tk()
    app = StoreManagerApp(root)
    root.mainloop()
