import fitz  # PyMuPDF
import os
from tqdm import tqdm
import uuid
from pathlib import Path

def split_invoices(input_pdf_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    pdf = fitz.open(input_pdf_path)
    invoice_count = 0
    start_page = None
    saved_pdf_paths = []
    
    # Extract original PDF name without extension
    original_pdf_name = Path(input_pdf_path).stem
    
    # Generate unique ID for this batch
    unique_id = uuid.uuid4().hex[:8]  # 8-character unique ID

    print(f"📄 Processing '{input_pdf_path}' ({pdf.page_count} pages)...\n")

    for page_num in tqdm(range(pdf.page_count), desc="Splitting invoices", unit="page"):
        page = pdf.load_page(page_num)
        text = page.get_text("text")

        # Detect start of an invoice
        if start_page is None and "Tax Invoice" in text:
            start_page = page_num

        # Detect end of an invoice
        if start_page is not None and "This is a Computer Generated Invoice" in text:
            end_page = page_num
            invoice_count += 1

            # Create new PDF with the invoice pages
            new_pdf = fitz.open()
            new_pdf.insert_pdf(pdf, from_page=start_page, to_page=end_page)
            
            # Create filename with format: <original_name>_<unique_id>_<count>.pdf
            output_filename = f"{original_pdf_name}_{unique_id}_{invoice_count}.pdf"
            output_path = os.path.join(output_folder, output_filename)
            
            new_pdf.save(output_path)
            new_pdf.close()
            
            # Add to list of saved paths
            saved_pdf_paths.append(output_path)

            # Reset for next invoice
            start_page = None

    pdf.close()
    print(f"\n✅ Done! Extracted {invoice_count} invoices into '{output_folder}'.")
    
    return saved_pdf_paths

