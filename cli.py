import pandas as pd
from custom_modules import invoice_splitter, dataocr, table_extractor
import os

def calculate_price_after_discount(price, discount_percent):
    """Calculate price after applying discount"""
    if discount_percent is None or discount_percent == 0:
        return price
    discount_amount = price * (discount_percent / 100)
    return price - discount_amount

def calculate_amount(quantity, price_after_discount):
    """Calculate total amount"""
    return quantity * price_after_discount

def process_invoice_to_rows(doc_data):
    """Convert invoice data to Excel rows format"""
    rows = []
    items = doc_data.get("items", {}).get("items", [])
    
    for idx, item in enumerate(items):
        # Get item data
        item_name = item.get("items", "")
        quantity = item.get("Qnty", 0)
        unit = item.get("unit", "")
        list_price = item.get("price", 0)
        discount_percent = item.get("discount", "") or ""
        
        # Calculate price after discount and amount
        if discount_percent != "":
            price_after_discount = calculate_price_after_discount(list_price, discount_percent)
        else:
            price_after_discount = list_price
        
        amount = calculate_amount(quantity, price_after_discount)
        
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

def export_data(all_rows, output_file, file_format, mode='write'):
    """Export data to Excel or CSV"""
    df = pd.DataFrame(all_rows)
    
    # Reorder columns to match the header order
    column_order = [
        "VCH_SERIES", "SALE/PURC_TYPE", "MC_NAME", "VCH/BILL_DATE", 
        "VCH/BILL_NO", "PARTY_NAME", "ITEM_NAME", "QUANTITY", "UNIT", 
        "PRICE", "DISCOUNT_PERCENT", "LIST_PRICE_ALT_UNIT", "LIST_PRICE", "AMOUNT"
    ]
    df = df[column_order]
    
    if file_format.lower() == 'excel':
        if mode == 'append' and os.path.exists(output_file):
            # Read existing data and append
            existing_df = pd.read_excel(output_file)
            df = pd.concat([existing_df, df], ignore_index=True)
        
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"✓ Data exported to {output_file}")
        
    elif file_format.lower() == 'csv':
        if mode == 'append' and os.path.exists(output_file):
            # Append to existing CSV
            df.to_csv(output_file, mode='a', header=False, index=False)
        else:
            # Write new CSV
            df.to_csv(output_file, index=False)
        print(f"✓ Data exported to {output_file}")
    
    return df

def main():
    # Input parameters
    input_pdf_file = "pdfs/invoice.pdf"
    output_folder = "individual_invoice"
    
    # Get user inputs
    print("\n=== Invoice Data Exporter ===\n")
    
    file_format = input("Enter output format (excel/csv) [default: excel]: ").strip().lower()
    if not file_format or file_format not in ['excel', 'csv']:
        file_format = 'excel'
    
    output_filename = input(f"Enter output filename (without extension) [default: invoice_data]: ").strip()
    if not output_filename:
        output_filename = 'invoice_data'
    
    # Add appropriate extension
    if file_format == 'excel':
        output_file = f"{output_filename}.xlsx"
    else:
        output_file = f"{output_filename}.csv"
    
    # Check if file exists and ask for mode
    mode = 'write'
    if os.path.exists(output_file):
        mode_input = input(f"\n'{output_file}' already exists. Choose mode (write/append) [default: write]: ").strip().lower()
        if mode_input == 'append':
            mode = 'append'
            print(f"→ Data will be appended to existing file")
        else:
            print(f"→ Existing file will be overwritten")
    
    print("\n--- Processing Invoices ---\n")
    
    # Process invoices
    paths = invoice_splitter.split_invoices(input_pdf_file, output_folder)
    all_rows = []
    
    for idx, path in enumerate(paths, 1):
        print(f"Processing invoice {idx}/{len(paths)}: {path}")
        doc_data = dataocr.extract_invoice_data(path)
        table_data = table_extractor.process_items(path)
        doc_data["items"] = table_data
        
        # Convert to rows
        rows = process_invoice_to_rows(doc_data)
        all_rows.extend(rows)
        
        print(f"  ✓ Extracted {len(rows)} items")
    
    # Export data
    print("\n--- Exporting Data ---\n")
    df = export_data(all_rows, output_file, file_format, mode)
    
    print(f"\n✓ Total records processed: {len(all_rows)}")
    print(f"✓ Total invoices processed: {len(paths)}")
    print(f"\n=== Export Complete ===\n")
    
    # Display preview
    print("Preview of exported data:")
    print(df.head(10).to_string())

if __name__ == "__main__":
    main()