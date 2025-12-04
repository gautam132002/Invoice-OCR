import fitz 

def extract_invoice_data(pdf_path):
    """
    Extract invoice data from a PDF file using PyMuPDF.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing invoice_number, date, customer, and dealer
    """

    # params =ITEM_NAME	QUANTITY	UNIT	PRICE	DISCOUNT_PERCENT	LIST_PRICE_ALT_UNIT 	LIST_PRICE	AMOUNT						


    result = {
        'VCH_SERIES' : 'Main',
        'SALE/PURC_TYPE' : 'L/GST-ItemWise',
        'MC_NAME' : 'Main Store',
        'VCH/BILL_NO': None,
        'VCH/BILL_DATE': None,
        'PARTY_NAME': None,
        'dealer': None
    }
    
    keywords = {
        'VCH/BILL_NO': 'Invoice No.',
        'VCH/BILL_DATE': 'Dated',
        'PARTY_NAME': 'Consignee',
        'dealer': 'Authorised Signatory'
    }
    
    try:
        
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                block_text = ""
                for line in block["lines"]:
                    for span in line["spans"]:
                        block_text += span["text"]
                for key, keyword in keywords.items():
                    if keyword in block_text:
                        bold_text = extract_bold_text_from_block(block)
                        if bold_text and result[key] is None:
                            result[key] = bold_text
        
        doc.close()
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
    
    return result


def extract_bold_text_from_block(block):
    """
    Extract bold text from a block.
    
    Args:
        block: PyMuPDF block dictionary
        
    Returns:
        str: Concatenated bold text found in the block
    """
    bold_texts = []
    
    if "lines" not in block:
        return None
    
    for line in block["lines"]:
        for span in line["spans"]:
            # Check if the font indicates bold
            font_name = span.get("font", "").lower()
            font_flags = span.get("flags", 0)
            
            is_bold = (
                'bold' in font_name or 
                'heavy' in font_name or 
                'black' in font_name or
                (font_flags & (1 << 16))  # Bold flag
            )
            
            if is_bold:
                text = span["text"].strip()
                if text:
                    bold_texts.append(text)
    
    # Join all bold text pieces
    result = " ".join(bold_texts).strip()
    return result if result else None


# # Example usage
# if __name__ == "__main__":
#     # Replace with your PDF file path
#     pdf_path = "individual_invoice/invoice_1.pdf"
    
#     # Parse the invoice
#     data = extract_invoice_data(pdf_path)
#     print(data)