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

        # Variables
        self.products = []
        self.selected_images = [] # List of paths

        # UI Components
        self.create_header()
        self.create_main_layout()
        
        # Load Data
        self.load_products()

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#0d9488", pady=15)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="لوحة تحكم المنتجات الاحترافية", bg="#0d9488", fg="white", font=("Cairo", 18, "bold"))
        title_label.pack()

    def create_main_layout(self):
        # Split into Left (Form) and Right (Table)
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#f8fafc")
        main_pane.pack(fill="both", expand=True, padx=10, pady=10)

        # Table Side (Right) - stored on left visually due to RTL? No, let's stick to standard layout
        # Let's put Form on Right (since it's Arabic) and Table on Left
        
        table_frame = tk.Frame(main_pane, bg="white")
        form_frame = tk.Frame(main_pane, bg="#f8fafc")
        
        main_pane.add(table_frame, width=500)
        main_pane.add(form_frame, width=450)

        self.create_table(table_frame)
        self.create_form(form_frame)

    def create_table(self, parent):
        columns = ("ID", "الاسم", "السعر", "السعر القديم")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("الاسم", text="اسم المنتج")
        self.tree.heading("السعر", text="السعر الحالي")
        self.tree.heading("السعر القديم", text="السعر السابق")
        
        self.tree.column("ID", width=40, anchor="center")
        self.tree.column("الاسم", width=180, anchor="e")
        self.tree.column("السعر", width=80, anchor="center")
        self.tree.column("السعر القديم", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def create_form(self, parent):
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
        tk.Button(sub_btn_frame, text="تفريغ الحقول", command=self.clear_form, bg="#64748b", fg="white").pack(side="right", fill="x", expand=True, padx=2)


    def load_products(self):
        if not os.path.exists(PRODUCTS_FILE):
            return

        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            match = re.search(r'var products = (\[.*?\]);', content, re.DOTALL)
            if match:
                json_str = match.group(1)
                # Cleaning to ensure valid JSON
                json_str = re.sub(r'(\w+):\s', r'"\1": ', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                
                self.products = json.loads(json_str)
                self.refresh_table()
        except Exception as e:
            messagebox.showerror("خطأ", f"Error loading data: {e}")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        for product in self.products:
            old_p = product.get("old_price", "")
            self.tree.insert("", "end", values=(product.get("id"), product.get("name"), product.get("price"), old_p))

    def on_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        
        values = self.tree.item(selected, 'values')
        product_id = int(values[0])
        
        product = next((p for p in self.products if p["id"] == product_id), None)
        if product:
            self.name_var.set(product["name"])
            self.price_var.set(product["price"])
            self.old_price_var.set(product.get("old_price", ""))
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", product["description"])
            
            # Handle Images
            self.selected_images = []
            self.images_listbox.delete(0, tk.END)
            
            # Support legacy 'image' field or new 'images' list
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

    def clear_form(self):
        self.name_var.set("")
        self.price_var.set("")
        self.old_price_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.selected_images = []
        self.images_listbox.delete(0, tk.END)
        self.tree.selection_remove(self.tree.selection())

    def process_images(self, image_list):
        processed_images = []
        for img_path in image_list:
            if img_path.startswith("http") or img_path.startswith("assets/"):
                processed_images.append(img_path)
            else:
                # Local file needs to be copied
                try:
                    filename = os.path.basename(img_path)
                    dest_path = os.path.join(ASSETS_DIR, filename)
                    shutil.copy(img_path, dest_path)
                    processed_images.append(f"assets/{filename}")
                except Exception as e:
                    print(f"Error copying image {img_path}: {e}")
        
        # Fallback if empty
        if not processed_images:
             processed_images.append("https://via.placeholder.com/300")
             
        return processed_images

    def get_form_data(self):
        name = self.name_var.get().strip()
        price = self.price_var.get().strip()
        old_price = self.old_price_var.get().strip()
        desc = self.desc_text.get("1.0", tk.END).strip()
        
        if not name or not price:
            messagebox.showwarning("تنبيه", "الاسم والسعر مطلوبان")
            return None

        # Determine single image (for backward compatibility) and list
        final_images = self.process_images(self.selected_images)
        main_image = final_images[0] if final_images else "https://via.placeholder.com/300"
        
        data = {
            "name": name,
            "price": int(price),
            "old_price": int(old_price) if old_price else None,
            "description": desc,
            "image": main_image,     # Main image for cards
            "images": final_images   # All images for slider
        }
        return data

    def add_product(self):
        data = self.get_form_data()
        if not data: return

        new_id = max([p["id"] for p in self.products] or [0]) + 1
        data["id"] = new_id
        
        self.products.append(data)
        self.refresh_table()
        self.save_to_file()
        self.clear_form()
        messagebox.showinfo("نجاح", "تم إضافة المنتج بنجاح")

    def delete_product(self):
        selected = self.tree.focus()
        if not selected: return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا المنتج؟"):
            product_id = int(self.tree.item(selected, 'values')[0])
            self.products = [p for p in self.products if p["id"] != product_id]
            self.refresh_table()
            self.save_to_file()
            self.clear_form()

    def save_products(self):
        selected = self.tree.focus()
        if not selected: return

        product_id = int(self.tree.item(selected, 'values')[0])
        product = next((p for p in self.products if p["id"] == product_id), None)
        
        if product:
            data = self.get_form_data()
            if not data: return
            
            product.update(data)
            
            self.refresh_table()
            self.save_to_file()
            self.publish_changes()

    def publish_changes(self):
        def run_publish():
            try:
                publish_script = os.path.join(BASE_DIR, 'publish_store_silent.bat')
                result = subprocess.run([publish_script], shell=True, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.root.after(0, lambda: messagebox.showinfo("نجاح", "تم النشر بنجاح!"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("خطأ", f"فشل النشر:\n{result.stderr}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("خطأ", str(e)))
        
        import threading
        # Run in background to not freeze UI
        threading.Thread(target=run_publish, daemon=True).start()

    def save_to_file(self):
        js_content = "// ==========================================\n"
        js_content += "//  ملف بيانات المنتجات (محدث)\n"
        js_content += "// ==========================================\n"
        js_content += "var products = " + json.dumps(self.products, ensure_ascii=False, indent=4) + ";"
        
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
