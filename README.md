# Invoice OCR

A small, self-contained toolkit to:

- Split multi-invoice PDFs into individual invoice PDF files
- Extract invoice-level metadata (invoice number, date, consignee, dealer)
- Extract and parse tabular item rows from each invoice
- Aggregate and export all items to CSV or Excel

This repository contains two entry points: `cli.py` (interactive CLI) and `ui.py` (Tkinter GUI). Core logic lives in `custom_modules/`.

Contents
- `cli.py` — interactive command-line processor that prompts for output format and filename.
- `ui.py` — Tkinter-based GUI with file pickers and progress UI.
- `custom_modules/invoice_splitter.py` — PDF splitting logic using PyMuPDF.
- `custom_modules/dataocr.py` — invoice-level extraction (PyMuPDF + bold-span heuristics).
- `custom_modules/table_extractor.py` — table extraction and column parsing by X coordinate.
- `pdfs/` — place source PDFs here (example default used by CLI: `pdfs/invoice.pdf`).
- `individual_invoice/` — default output folder for split PDFs.

Processing steps (full flow)

1) Split PDF into individual invoices
- Module: `custom_modules/invoice_splitter.py`
- How it detects invoices: looks for the text marker `"Tax Invoice"` to detect the start of an invoice and `"This is a Computer Generated Invoice"` to detect the end. When both markers are present the pages between them are saved as a new PDF.
- Output filenames: `<originalname>_<batchid>_<count>.pdf` (batchid is a short unique id).

2) Extract invoice-level fields
- Module: `custom_modules/dataocr.py`
- Implementation: uses PyMuPDF (`fitz`) to walk page text blocks. For specific fields (invoice number, date, consignee, dealer) it looks for known keywords (e.g. `Invoice No.`, `Dated`, `Consignee`, `Authorised Signatory`) and extracts bold spans nearby when available.

3) Extract and parse the items table
- Module: `custom_modules/table_extractor.py`
- It finds the table region using start/end markers (`S.No.` and `Amount Chargable(in words)`) and selects wide text blocks (>80% page width) inside that region.
- It then parses rows by inspecting each line's `x0` coordinates and mapping ranges to columns (S.No, Description, HSN, Quantity, Rate, Per/Unit, Discount, Amount). The output per-invoice is a dict like `{ "items": [ {"items": ..., "Qnty": ..., "price": ..., "unit": ..., "discount": ..., "total": ...}, ... ] }`.

4) Aggregate + Export
- Both `cli.py` and `ui.py` convert parsed invoice data into row dictionaries with columns:

	`VCH_SERIES`, `SALE/PURC_TYPE`, `MC_NAME`, `VCH/BILL_DATE`, `VCH/BILL_NO`, `PARTY_NAME`, `ITEM_NAME`, `QUANTITY`, `UNIT`, `PRICE`, `DISCOUNT_PERCENT`, `LIST_PRICE_ALT_UNIT`, `LIST_PRICE`, `AMOUNT`

- Export uses `pandas.DataFrame` and supports writing to Excel (`.xlsx`, via `openpyxl`) or CSV. Both overwrite and append modes are supported.

Installation

Prerequisites
- Python 3.10+ recommended (project `pyproject.toml` requires >=3.10).
- On Windows `tkinter` is typically included; if not, install the platform packages for Tk support.

Install dependencies (recommended)

Option A — install with `uv` (if you use it for process management):

```powershell
pip install uv
uv sync
```

Option B — plain pip (explicit):

```powershell
pip install pandas pymupdf openpyxl tqdm
# optional: pip install -r requirements.txt
```

If you want, I can add a `requirements.txt` listing these packages so you can use `pip install -r requirements.txt`.

Running the project

CLI (interactive)

```powershell
python cli.py
# or with uv: uv run cli.py
```

Behavior
- `cli.py` default input: `pdfs/invoice.pdf` (change the `input_pdf_file` variable in `main()` to use a different file).
- The CLI prompts for output format (`excel` or `csv`) and output filename (default `invoice_data`).
- If the chosen output file already exists the CLI asks whether to `write` (overwrite) or `append`.

GUI (Tkinter)

```powershell
python ui.py
# or: uv run ui.py
```

The GUI provides file pickers for the input PDF and output folder, options for output filename, format (Excel / CSV) and write mode (overwrite/append). It shows processing progress and a complete/summary dialog on success.

Examples (PowerShell)

Install deps and run GUI:

```powershell
pip install pandas pymupdf openpyxl tqdm
python ui.py
```

Process a PDF and export CSV via CLI:

```powershell
python cli.py
# choose `csv` when prompted and supply filename
```

Configuration and tuning

- Change default input or output paths by editing `cli.py` or by using the GUI.
- If your invoice documents use different start/end markers than the defaults, update them in `custom_modules/invoice_splitter.py` (search for `Tax Invoice` and `This is a Computer Generated Invoice`).
- If parsed table columns are wrong, open `custom_modules/table_extractor.py` and adjust the `x0` ranges used to detect each column. These ranges are specific to your invoice layout and may need calibration.

Troubleshooting

- No data extracted: confirm the PDF contains selectable text. PyMuPDF reads embedded text; scanned images require OCR (e.g., `pytesseract`) and code changes to `dataocr.py`.
- Wrong columns / mis-parsed rows: adjust X-coordinate ranges in `custom_modules/table_extractor.py` and re-run.
- Excel export error: ensure `openpyxl` is installed.
- GUI doesn't start: ensure `tkinter` is available in your Python distribution.





