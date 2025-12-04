import fitz  # PyMuPDF
import json

def extract_invoice_table(pdf_path):
    """
    Extract table data between start and end markers.
    Table rows are wide blocks (>80% page width).
    Returns detailed information about blocks, lines, text, and coordinates.
    """
    doc = fitz.open(pdf_path)
    
    table_start = "S.No."
    table_end = "Amount Chargable(in words)"
    
    all_table_rows = []
    
    # First, find which page has the start and end markers
    start_page = None
    end_page = None
    start_y = None
    end_y = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                
                if table_start in block_text and start_page is None:
                    start_page = page_num
                    start_y = block["bbox"][3]  # Bottom of start block
                    
                if table_end in block_text and end_page is None:
                    end_page = page_num
                    end_y = block["bbox"][1]  # Top of end block
    
    # If we didn't find start marker, return empty
    if start_page is None:
        doc.close()
        return all_table_rows
    
    # Process pages based on start and end positions
    for page_num in range(start_page, len(doc)):
        # Stop if we've passed the end page
        if end_page is not None and page_num > end_page:
            break
            
        page = doc[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        
        # Get text blocks
        blocks = page.get_text("dict")["blocks"]
        
        # Determine extraction range for this page
        if page_num == start_page and page_num == end_page:
            # Start and end on same page
            range_start = start_y
            range_end = end_y
        elif page_num == start_page:
            # First page: from start marker to bottom of page
            range_start = start_y
            range_end = page_height
        elif page_num == end_page:
            # Last page: from top of page to end marker
            range_start = 0
            range_end = end_y
        else:
            # Middle pages: entire page
            range_start = 0
            range_end = page_height
        
        # Extract table rows (wide blocks in range)
        for block in blocks:
            if "lines" not in block:
                continue
            
            block_y = block["bbox"][1]  # Top of block
            block_width = block["bbox"][2] - block["bbox"][0]
            
            # Check if block is in range
            in_range = range_start < block_y < range_end
            
            # Check if block is wide enough (>80% page width)
            is_wide = (block_width / page_width) > 0.8
            
            if in_range and is_wide:
                # Extract complete text from block
                row_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        row_text += span["text"] + " "
                
                row_text = row_text.strip()
                
                if "Rounded Off (-)" not in row_text and row_text:
                    # Extract detailed line data
                    lines_data = []
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"]
                        
                        lines_data.append({
                            "text": line_text.strip(),
                            "bbox": line["bbox"],
                            "x0": line["bbox"][0],
                            "y0": line["bbox"][1],
                            "x1": line["bbox"][2],
                            "y1": line["bbox"][3]
                        })
                    
                    all_table_rows.append({
                        "page": page_num + 1,
                        "lines": lines_data
                    })
    
    doc.close()
    # print(all_table_rows)
    return all_table_rows


def parse_items(table_rows):
    """
    Parse table rows into structured item data based on x0 coordinates.
    Range increased to 8px for each field.
    """
    items = []
    
    for row in table_rows:
        item = {
            "sno": None,
            "items": None,
            "hsna": None,
            "Qnty": None,
            "price": None,
            "unit": None,
            "discount": None,
            "total": None
        }
        
        # Collect all Quantity candidates (for finding the one with least y0)
        quantity_candidates = []
        name_candidates = []
        
        for line in row["lines"]:
            x0 = line["x0"]
            y0 = line["y0"]
            text = line["text"]
            
            # S.No (x0 between 31-42, center: 36.5, range: 8px)
            if 31 <= x0 <= 42:
                item["sno"] = text
            
            # Description of Goods (x0 between 61-69, center: 65, range: 8px)
            elif 61 <= x0 <= 69:
                # item["items"] = text
                name_candidates.append(text)
            
            # HSN/SAC (x0 between 241-251, center: 246, range: 8px)
            elif 241 <= x0 <= 251:
                item["hsna"] = text
            
            # Quantity (x0 between 325-333, center: 329, range: 8px) - collect all candidates
            elif 325 <= x0 <= 333:
                quantity_candidates.append({"text": text, "y0": y0})
            
            # Rate (x0 between 377-385, center: 381, range: 8px)
            elif 377 <= x0 <= 385:
                item["price"] = text
                price = float(item['price'])
                item['price'] = price
            
            # Per (x0 between 415-423, center: 419, range: 8px)
            elif 415 <= x0 <= 423:
                item["unit"] = text.replace(".", "")
            
            # Discount percentage (x0 between 478-486, center: 482, range: 8px)
            elif 470 <= x0 <= 486:
                item["discount"] = text
                discount = float(item['discount'].split(" ")[0])
                item['discount'] = discount
            
            # Amount (x0 between 521-529, center: 525, range: 8px)
            elif 510 <= x0 <= 599:
                item["total"] = text
                total = float(item['total'].replace(",", ""))
                item['total'] = total
        
        # Select Quantity with least y0 (topmost)
        if quantity_candidates:
            quantity_candidates.sort(key=lambda x: x["y0"])
            item["Qnty"] = quantity_candidates[0]["text"]
            qnty = float(item['Qnty'].split(" ")[0])
            item['Qnty'] = qnty
        
        if name_candidates:
            name = " ".join(name_candidates)
            item["items"] = name


        
        items.append(item)
    
    return {"items": items}

def process_items(pdf_path):
    # Extract table rows
    rows = extract_invoice_table(pdf_path)
    # Parse into structured JSON
    result = parse_items(rows)
    return result


# if __name__ == "__main__":
#     pdf_path = "individual_invoice\invoice_5c606b88_3.pdf"
#     data = process_items(pdf_path)
#     print(json.dumps(data, indent=2))

