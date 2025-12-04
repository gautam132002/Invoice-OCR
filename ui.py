import pandas as pd
from custom_modules import invoice_splitter, dataocr, table_extractor
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg_color, hover_color, text_color="white", width=100, height=36, corner_radius=6):
        tk.Canvas.__init__(self, parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.width = width
        self.height = height
        self.text = text
        
        self.draw_button(self.bg_color)
        self.bind("<Button-1>", self.on_click)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        
    def draw_button(self, color):
        self.delete("all")
        w, h = self.width, self.height

        # Draw simple rectangle (no radius)
        self.create_rectangle(
            0, 0, w, h,
            fill=color,
            outline=color
        )

        # Draw text
        self.create_text(
            w/2, h/2,
            text=self.text,
            fill=self.text_color,
            font=("Segoe UI", 8, "bold")
        )
    
    def on_enter(self, event):
        self.draw_button(self.hover_color)
        self.config(cursor="hand2")
    
    def on_leave(self, event):
        self.draw_button(self.bg_color)
        self.config(cursor="")
    
    def on_click(self, event):
        if self.command:
            self.command()

class RoundedEntry(tk.Frame):
    def __init__(self, parent, textvariable, bg_color, fg_color, border_color, focus_color, corner_radius=6):
        tk.Frame.__init__(self, parent, bg=border_color)
        self.corner_radius = corner_radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.focus_color = focus_color
        
        # Inner frame for padding
        inner_frame = tk.Frame(self, bg=bg_color)
        inner_frame.pack(padx=1, pady=1, fill=tk.BOTH, expand=True)
        
        self.entry = tk.Entry(
            inner_frame,
            textvariable=textvariable,
            font=("Segoe UI", 10),
            bg=bg_color,
            fg=fg_color,
            relief=tk.FLAT,
            insertbackground=fg_color,
            bd=0
        )
        self.entry.pack(padx=8, pady=6, fill=tk.BOTH, expand=True)
        
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)
    
    def on_focus_in(self, event):
        self.config(bg=self.focus_color)
    
    def on_focus_out(self, event):
        self.config(bg=self.border_color)

class InvoiceExporterUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Data Exporter")
        self.root.geometry("900x750")
        self.root.resizable(False, False)
        
        # GitHub-inspired color scheme
        self.bg_dark = "#0d1117"  # GitHub dark background
        self.bg_medium = "#161b22"  # GitHub card background
        self.bg_light = "#21262d"  # GitHub input background
        self.border_color = "#30363d"  # GitHub border
        self.blue = "#1f6feb"  # GitHub blue
        self.blue_hover = "#388bfd"  # GitHub blue hover
        self.green = "#238636"  # GitHub green
        self.green_hover = "#2ea043"
        self.text_color = "#c9d1d9"  # GitHub text
        self.text_dim = "#8b949e"  # GitHub dim text
        
        self.root.configure(bg=self.bg_dark)
        
        # Variables
        self.input_file = tk.StringVar()
        self.output_folder = tk.StringVar(value="individual_invoice")
        self.output_filename = tk.StringVar(value="invoice_data")
        self.file_format = tk.StringVar(value="excel")
        self.mode = tk.StringVar(value="write")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        container = tk.Frame(self.root, bg=self.bg_dark)
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header section
        header_frame = tk.Frame(container, bg=self.bg_dark)
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        title = tk.Label(
            header_frame, 
            text="Invoice OCR",
            font=("Segoe UI", 28, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
        )
        title.pack(anchor="w")
        
        # subtitle = tk.Label(
        #     header_frame,
        #     text="Extract and export invoice data to Excel or CSV",
        #     font=("Segoe UI", 11),
        #     bg=self.bg_dark,
        #     fg=self.text_dim
        # )
        # subtitle.pack(anchor="w", pady=(5, 0))
        
        # Card for main content
        card = tk.Frame(container, bg=self.bg_medium)
        card.pack(fill=tk.BOTH, expand=True)
        
        # Add padding inside card
        card_inner = tk.Frame(card, bg=self.bg_medium)
        card_inner.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Input file section
        self.create_section(card_inner, "Input PDF File", 0)
        input_frame = tk.Frame(card_inner, bg=self.bg_medium)
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        input_frame.columnconfigure(0, weight=1)
        
        self.input_entry = RoundedEntry(
            input_frame, self.input_file, self.bg_light, 
            self.text_color, self.border_color, self.blue
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_btn = RoundedButton(
            input_frame, "Browse", self.browse_input,
            self.blue, self.blue_hover, width=90, height=36
        )
        browse_btn.grid(row=0, column=1)
        
        # Output folder section
        self.create_section(card_inner, "Output Folder", 2)
        output_folder_frame = tk.Frame(card_inner, bg=self.bg_medium)
        output_folder_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        output_folder_frame.columnconfigure(0, weight=1)
        
        self.output_folder_entry = RoundedEntry(
            output_folder_frame, self.output_folder, self.bg_light,
            self.text_color, self.border_color, self.blue
        )
        self.output_folder_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        browse_folder_btn = RoundedButton(
            output_folder_frame, "Browse", self.browse_output_folder,
            self.blue, self.blue_hover, width=90, height=36
        )
        browse_folder_btn.grid(row=0, column=1)
        
        # Output filename section
        self.create_section(card_inner, "Output Filename", 4)
        filename_frame = tk.Frame(card_inner, bg=self.bg_medium)
        filename_frame.grid(row=5, column=0, sticky="ew", pady=(0, 20))
        
        self.filename_entry = RoundedEntry(
            filename_frame, self.output_filename, self.bg_light,
            self.text_color, self.border_color, self.blue
        )
        self.filename_entry.pack(fill=tk.X)
        
        # Format and mode section
        options_frame = tk.Frame(card_inner, bg=self.bg_medium)
        options_frame.grid(row=6, column=0, sticky="ew", pady=(0, 20))
        
        # Format
        format_frame = tk.Frame(options_frame, bg=self.bg_dark)
        format_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(
            format_frame,
            text="Output Format",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        radio_frame1 = tk.Frame(format_frame, bg=self.bg_dark)
        radio_frame1.pack(anchor="w", padx=15, pady=(0, 12))
        
        self.create_radio(radio_frame1, "Excel (.xlsx)", "excel", self.file_format).pack(anchor="w", pady=2)
        self.create_radio(radio_frame1, "CSV (.csv)", "csv", self.file_format).pack(anchor="w", pady=2)
        
        # Mode
        mode_frame = tk.Frame(options_frame, bg=self.bg_dark)
        mode_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            mode_frame,
            text="Write Mode",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_dark,
            fg=self.text_color
        ).pack(anchor="w", padx=15, pady=(12, 8))
        
        radio_frame2 = tk.Frame(mode_frame, bg=self.bg_dark)
        radio_frame2.pack(anchor="w", padx=15, pady=(0, 12))
        
        self.create_radio(radio_frame2, "Overwrite existing", "write", self.mode).pack(anchor="w", pady=2)
        self.create_radio(radio_frame2, "Append to existing", "append", self.mode).pack(anchor="w", pady=2)
        
        # Progress section
        progress_frame = tk.Frame(card_inner, bg=self.bg_dark)
        progress_frame.grid(row=7, column=0, sticky="ew", pady=(0, 20))
        
        self.status_label = tk.Label(
            progress_frame,
            text="Ready to process",
            font=("Segoe UI", 10),
            bg=self.bg_dark,
            fg=self.text_dim,
            anchor="w"
        )
        self.status_label.pack(fill=tk.X, padx=15, pady=(15, 8))
        
        # Progress bar container
        progress_container = tk.Frame(progress_frame, bg=self.border_color, height=8)
        progress_container.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.progress_bar = tk.Canvas(progress_container, height=6, bg=self.bg_light, highlightthickness=0)
        self.progress_bar.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Process button
        button_frame = tk.Frame(card_inner, bg=self.bg_medium)
        button_frame.grid(row=8, column=0, pady=(10, 0))
        
        self.process_btn = RoundedButton(
            button_frame,
            "Start Processing",
            self.start_processing,
            self.green,
            self.green_hover,
            width=180,
            height=40
        )
        self.process_btn.pack()
        
        # Configure grid
        card_inner.columnconfigure(0, weight=1)
        
    def update_progress_bar(self, percent):
        self.progress_bar.delete("all")
        if percent > 0:
            width = self.progress_bar.winfo_width()
            fill_width = int(width * percent / 100)
            self.progress_bar.create_rectangle(
                0, 0, fill_width, 6,
                fill=self.green, outline=""
            )
        
    def create_section(self, parent, text, row):
        label = tk.Label(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_medium,
            fg=self.text_color,
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", pady=(0, 8))
    
    def create_radio(self, parent, text, value, variable):
        radio = tk.Radiobutton(
            parent,
            text=text,
            value=value,
            variable=variable,
            font=("Segoe UI", 9),
            bg=self.bg_dark,
            fg=self.text_color,
            selectcolor=self.bg_light,
            activebackground=self.bg_dark,
            activeforeground=self.text_color,
            cursor="hand2",
            borderwidth=0,
            highlightthickness=0
        )
        return radio
    
    def browse_input(self):
        filename = filedialog.askopenfilename(
            title="Select PDF file",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
    
    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)
    
    def start_processing(self):
        if not self.input_file.get():
            messagebox.showerror("Error", "Please select an input PDF file")
            return
        
        # Disable button during processing
        self.process_btn.config(state=tk.DISABLED)
        self.process_btn.draw_button(self.text_dim)
        
        # Start processing in a separate thread
        thread = threading.Thread(target=self.process_invoices, daemon=True)
        thread.start()
    
    def process_invoices(self):
        try:
            input_pdf = self.input_file.get()
            output_folder = self.output_folder.get()
            filename = self.output_filename.get()
            file_format = self.file_format.get()
            mode = self.mode.get()
            
            # Add appropriate extension
            if file_format == 'excel':
                output_file = f"{filename}.xlsx"
            else:
                output_file = f"{filename}.csv"
            
            # Update status
            self.update_status("Splitting invoices...", 10)
            
            # Process invoices
            paths = invoice_splitter.split_invoices(input_pdf, output_folder)
            total_invoices = len(paths)
            all_rows = []
            
            for idx, path in enumerate(paths, 1):
                progress = 10 + (idx / total_invoices) * 70
                self.update_status(f"Processing invoice {idx}/{total_invoices}...", progress)
                
                doc_data = dataocr.extract_invoice_data(path)
                table_data = table_extractor.process_items(path)
                doc_data["items"] = table_data
                
                rows = self.process_invoice_to_rows(doc_data)
                all_rows.extend(rows)
            
            # Export data
            self.update_status("Exporting data...", 85)
            df = self.export_data(all_rows, output_file, file_format, mode)
            
            self.update_status(f"✓ Complete! Processed {len(all_rows)} records from {total_invoices} invoices", 100)
            
            # Show success message
            self.root.after(0, lambda: messagebox.showinfo(
                "Success",
                f"Successfully processed {total_invoices} invoices!\n"
                f"Total records: {len(all_rows)}\n"
                f"Output file: {output_file}"
            ))
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", 0)
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        
        finally:
            # Re-enable button
            self.root.after(0, lambda: [
                self.process_btn.config(state=tk.NORMAL),
                self.process_btn.draw_button(self.green)
            ])
    
    def update_status(self, message, progress):
        self.root.after(0, lambda: self.status_label.config(text=message))
        self.root.after(0, lambda: self.update_progress_bar(progress))
        self.root.update_idletasks()
    
    def calculate_price_after_discount(self, price, discount_percent):
        if discount_percent is None or discount_percent == 0:
            return price
        discount_amount = price * (discount_percent / 100)
        return price - discount_amount
    
    def calculate_amount(self, quantity, price_after_discount):
        return quantity * price_after_discount
    
    def process_invoice_to_rows(self, doc_data):
        rows = []
        items = doc_data.get("items", {}).get("items", [])
        
        for idx, item in enumerate(items):
            item_name = item.get("items", "")
            quantity = item.get("Qnty", 0)
            unit = item.get("unit", "")
            list_price = item.get("price", 0)
            discount_percent = item.get("discount", "") or ""
            
            if discount_percent != "":
                price_after_discount = self.calculate_price_after_discount(list_price, discount_percent)
            else:
                price_after_discount = list_price
            
            amount = self.calculate_amount(quantity, price_after_discount)
            
            row = {
                "VCH_SERIES": doc_data.get("VCH_SERIES", "") if idx == 0 else "",
                "SALE/PURC_TYPE": doc_data.get("SALE/PURC_TYPE", "") if idx == 0 else "",
                "MC_NAME": doc_data.get("MC_NAME", "") if idx == 0 else "",
                "VCH/BILL_DATE": doc_data.get("VCH/BILL_DATE", "") if idx == 0 else "",
                "VCH/BILL_NO": doc_data.get("VCH/BILL_NO", "") if idx == 0 else "",
                "PARTY_NAME": doc_data.get("PARTY_NAME", "") if idx == 0 else "",
                "ITEM_NAME": item_name,
                "QUANTITY": quantity,
                "UNIT": unit,
                "PRICE": round(price_after_discount, 2),
                "DISCOUNT_PERCENT": discount_percent,
                "LIST_PRICE_ALT_UNIT": list_price,
                "LIST_PRICE": list_price,
                "AMOUNT": round(amount, 2)
            }
            rows.append(row)
        
        return rows
    
    def export_data(self, all_rows, output_file, file_format, mode='write'):
        df = pd.DataFrame(all_rows)
        
        column_order = [
            "VCH_SERIES", "SALE/PURC_TYPE", "MC_NAME", "VCH/BILL_DATE", 
            "VCH/BILL_NO", "PARTY_NAME", "ITEM_NAME", "QUANTITY", "UNIT", 
            "PRICE", "DISCOUNT_PERCENT", "LIST_PRICE_ALT_UNIT", "LIST_PRICE", "AMOUNT"
        ]
        df = df[column_order]
        
        if file_format.lower() == 'excel':
            if mode == 'append' and os.path.exists(output_file):
                existing_df = pd.read_excel(output_file)
                df = pd.concat([existing_df, df], ignore_index=True)
            
            df.to_excel(output_file, index=False, engine='openpyxl')
            
        elif file_format.lower() == 'csv':
            if mode == 'append' and os.path.exists(output_file):
                df.to_csv(output_file, mode='a', header=False, index=False)
            else:
                df.to_csv(output_file, index=False)
        
        return df

def main():
    root = tk.Tk()
    app = InvoiceExporterUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()