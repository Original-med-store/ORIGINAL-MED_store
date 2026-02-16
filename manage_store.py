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
        self.root.title("مدير متجر ORIGINAL_MED")
        self.root.geometry("800x600")
        self.root.configure(bg="#f4f4f4")

        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TLabel", font=("Cairo", 12))
        self.style.configure("TButton", font=("Cairo", 11))
        self.style.configure("Treeview.Heading", font=("Cairo", 11, "bold"))
        self.style.configure("Treeview", font=("Cairo", 10), rowheight=30)

        # Variables
        self.products = []
        self.selected_image_path = None

        # UI Components
        self.create_header()
        self.create_table()
        self.create_form()
        
        # Load Data
        self.load_products()

    def create_header(self):
        header_frame = tk.Frame(self.root, bg="#008080", pady=10)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, text="لوحة تحكم المنتجات", bg="#008080", fg="white", font=("Cairo", 16, "bold"))
        title_label.pack()

    def create_table(self):
        table_frame = tk.Frame(self.root, bg="#f4f4f4", padx=10, pady=10)
        table_frame.pack(fill="both", expand=True)

        columns = ("ID", "الاسم", "السعر", "الوصف")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("ID", text="ID")
        self.tree.heading("الاسم", text="اسم المنتج")
        self.tree.heading("السعر", text="السعر")
        self.tree.heading("الوصف", text="الوصف")
        
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("الاسم", width=200, anchor="e")
        self.tree.column("السعر", width=100, anchor="center")
        self.tree.column("الوصف", width=400, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def create_form(self):
        form_frame = tk.LabelFrame(self.root, text="بيانات المنتج", font=("Cairo", 12), bg="#f4f4f4", padx=10, pady=10)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Grid Layout
        tk.Label(form_frame, text="اسم المنتج:", bg="#f4f4f4").grid(row=0, column=3, sticky="e", padx=5)
        self.name_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.name_var, justify="right", font=("Cairo", 10)).grid(row=0, column=2, sticky="ew", padx=5)

        tk.Label(form_frame, text="السعر (ج.م):", bg="#f4f4f4").grid(row=0, column=1, sticky="e", padx=5)
        self.price_var = tk.StringVar()
        tk.Entry(form_frame, textvariable=self.price_var, justify="center", font=("Cairo", 10)).grid(row=0, column=0, sticky="ew", padx=5)

        tk.Label(form_frame, text="الوصف:", bg="#f4f4f4").grid(row=1, column=3, sticky="ne", padx=5, pady=5)
        self.desc_text = tk.Text(form_frame, height=3, width=40, font=("Cairo", 10))
        self.desc_text.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=5)

        # Image Selection
        tk.Label(form_frame, text="صورة المنتج:", bg="#f4f4f4").grid(row=2, column=3, sticky="e", padx=5)
        self.image_label = tk.Label(form_frame, text="لم يتم اختيار صورة", fg="gray", bg="#f4f4f4")
        self.image_label.grid(row=2, column=2, sticky="w", padx=5)
        tk.Button(form_frame, text="اختر صورة", command=self.choose_image).grid(row=2, column=1, padx=5)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#f4f4f4", pady=10)
        btn_frame.pack(fill="x")

        tk.Button(btn_frame, text="حفظ التعديلات", command=self.save_products, bg="#008080", fg="white", width=15).pack(side="right", padx=10)
        tk.Button(btn_frame, text="إضافة منتج جديد", command=self.add_product, bg="#20c997", fg="white", width=15).pack(side="right", padx=10)
        tk.Button(btn_frame, text="حذف المحدد", command=self.delete_product, bg="#dc3545", fg="white", width=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="تفريغ الحقول", command=self.clear_form, bg="#6c757d", fg="white", width=15).pack(side="left", padx=10)

    def load_products(self):
        if not os.path.exists(PRODUCTS_FILE):
            messagebox.showerror("خطأ", "ملف المنتجات غير موجود!")
            return

        try:
            with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract list using regex because it's a JS file, not pure JSON
            match = re.search(r'var products = (\[.*?\]);', content, re.DOTALL)
            if match:
                json_str = match.group(1)
                # Fix keys to be quoted for valid JSON (e.g. id: 1 -> "id": 1)
                # This is a simple regex fix, might need more robustness for complex strings
                json_str = re.sub(r'(\w+):\s', r'"\1": ', json_str)
                # Cleaning potential trailing commas which JSON doesn't like but JS does
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                
                self.products = json.loads(json_str)
                self.refresh_table()
            else:
                 messagebox.showerror("خطأ", "لم يتم العثور على قائمة المنتجات في الملف.")

        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء قراءة الملف:\n{e}")

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        for product in self.products:
            self.tree.insert("", "end", values=(product.get("id"), product.get("name"), product.get("price"), product.get("description")))

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
            self.desc_text.delete("1.0", tk.END)
            self.desc_text.insert("1.0", product["description"])
            self.selected_image_path = product["image"]
            self.image_label.config(text=os.path.basename(product["image"]))

    def choose_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.png;*.jpeg")])
        if file_path:
            self.selected_image_path = file_path
            self.image_label.config(text=os.path.basename(file_path))

    def clear_form(self):
        self.name_var.set("")
        self.price_var.set("")
        self.desc_text.delete("1.0", tk.END)
        self.selected_image_path = None
        self.image_label.config(text="لم يتم اختيار صورة")
        self.tree.selection_remove(self.tree.selection())

    def add_product(self):
        name = self.name_var.get()
        price = self.price_var.get()
        desc = self.desc_text.get("1.0", tk.END).strip()

        if not name or not price:
            messagebox.showwarning("تنبيه", "يرجى إدخال الاسم والسعر")
            return

        # Image Handling
        final_image_path = "https://via.placeholder.com/300" # Default
        if self.selected_image_path:
            if not self.selected_image_path.startswith("http"):
                # Copy local file
                filename = os.path.basename(self.selected_image_path)
                dest_path = os.path.join(ASSETS_DIR, filename)
                try:
                    shutil.copy(self.selected_image_path, dest_path)
                    final_image_path = f"assets/{filename}"
                except:
                    pass
            else:
                final_image_path = self.selected_image_path

        new_id = max([p["id"] for p in self.products] or [0]) + 1
        new_product = {
            "id": new_id,
            "name": name,
            "price": int(price),
            "image": final_image_path,
            "description": desc
        }
        
        self.products.append(new_product)
        self.refresh_table()
        self.save_to_file()
        self.clear_form()
        messagebox.showinfo("نجاح", "تم إضافة المنتج بنجاح")

    def delete_product(self):
        selected = self.tree.focus()
        if not selected:
            return
        
        if messagebox.askyesno("تأكيد", "هل أنت متأكد من حذف هذا المنتج؟"):
            product_id = int(self.tree.item(selected, 'values')[0])
            self.products = [p for p in self.products if p["id"] != product_id]
            self.refresh_table()
            self.save_to_file()
            self.clear_form()

    def save_products(self):
        # Update existing product
        selected = self.tree.focus()
        if not selected:
            return

        product_id = int(self.tree.item(selected, 'values')[0])
        product = next((p for p in self.products if p["id"] == product_id), None)
        
        if product:
            product["name"] = self.name_var.get()
            product["price"] = int(self.price_var.get())
            product["description"] = self.desc_text.get("1.0", tk.END).strip()
            
            # Update image if changed
            if self.selected_image_path and self.selected_image_path != product["image"]:
                 if not self.selected_image_path.startswith("http") and not self.selected_image_path.startswith("assets/"):
                    filename = os.path.basename(self.selected_image_path)
                    dest_path = os.path.join(ASSETS_DIR, filename)
                    try:
                        shutil.copy(self.selected_image_path, dest_path)
                        product["image"] = f"assets/{filename}"
                    except:
                        pass
                 else:
                     product["image"] = self.selected_image_path

            self.refresh_table()
            self.save_to_file()
            self.publish_changes() # Auto-publish
            messagebox.showinfo("نجاح", "تم حفظ التعديلات ونشرها للموقع!")

    def publish_changes(self):
        def run_publish():
            try:
                publish_script = os.path.join(BASE_DIR, 'publish_store_silent.bat')
                subprocess.run([publish_script], shell=True, check=True)
            except Exception as e:
                print(f"Error publishing: {e}")
        
        import threading
        threading.Thread(target=run_publish).start()

    def save_to_file(self):
        # Convert back to JS format
        js_content = "// ==========================================\n"
        js_content += "//  ملف بيانات المنتجات (يتم تحديثه تلقائيًا)\n"
        js_content += "// ==========================================\n"
        js_content += "var products = " + json.dumps(self.products, ensure_ascii=False, indent=4) + ";"
        
        # simple hack to remove quotes from keys if needed, but JS accepts quotes keys too. 
        # keeping it valid JSON inside JS is safer for this parser.
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            f.write(js_content)

if __name__ == "__main__":
    root = tk.Tk()
    app = StoreManagerApp(root)
    root.mainloop()
