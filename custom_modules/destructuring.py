import fitz  # PyMuPDF
import json
import os

def extract_and_annotate_invoice(pdf_path, output_json="invoice_structure.json", padding=5):
    pdf = fitz.open(pdf_path)
    data = {}

    # Prepare output paths
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    annotated_pdf_path = f"{base_name}_annotated.pdf"

    for page_num, page in enumerate(pdf, start=1):
        page_data = []
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            block_rect = fitz.Rect(block["bbox"])
            # Add padding around the block rectangle

            expand_by = padding
            block_rect.x0 -= expand_by
            block_rect.y0 -= expand_by
            block_rect.x1 += expand_by
            block_rect.y1 += expand_by

            # block_rect.inflate(padding)

            block_obj = {
                "block_no": block.get("number", None),
                "bbox": list(block["bbox"]),
                "lines": []
            }

            # Draw red rectangle around the (padded) block
            page.draw_rect(block_rect, color=(1, 0, 0), width=1.5)

            for line in block.get("lines", []):
                line_text = " ".join(
                    [span["text"] for span in line.get("spans", []) if span["text"].strip()]
                )
                line_rect = fitz.Rect(line["bbox"])

                block_obj["lines"].append({
                    "text": line_text,
                    "bbox": list(line["bbox"])
                })

                # Draw green rectangle around the line
                page.draw_rect(line_rect, color=(0, 1, 0), width=0.8)

            page_data.append(block_obj)

        data[f"page_{page_num}"] = page_data

    # Save annotated PDF
    pdf.save(annotated_pdf_path)
    pdf.close()

    # Save JSON structure
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Annotated PDF saved as '{annotated_pdf_path}'")
    print(f"✅ JSON structure saved as '{output_json}'")

# Example usage
if __name__ == "__main__":

    extract_and_annotate_invoice("individual_invoice\invoice_4.pdf")
