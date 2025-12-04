import pandas as pd
from custom_modules import invoice_splitter, dataocr, table_extractor
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich import box
from rich.layout import Layout
from rich.live import Live
from datetime import datetime
import sys

console = Console()

class InvoiceExporter:
    def __init__(self):
        self.console = console
        self.all_rows = []
        self.processed_count = 0
        
    def display_banner(self):
        """Display welcome banner"""
        banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║        INVOICE OCR                                        ║
║        Professional Invoice Processing Tool               ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
        """
        self.console.print(banner, style="bold cyan")
        self.console.print(f"[dim]Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")

    def calculate_price_after_discount(self, price, discount_percent):
        """Calculate price after applying discount"""
        if discount_percent is None or discount_percent == 0:
            return price
        discount_amount = price * (discount_percent / 100)
        return price - discount_amount

    def calculate_amount(self, quantity, price_after_discount):
        """Calculate total amount"""
        return quantity * price_after_discount

    def process_invoice_to_rows(self, doc_data):
        """Convert invoice data to Excel rows format"""
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

    def get_user_inputs(self):
        """Get configuration from user with validation"""
        self.console.print(Panel.fit(
            "[bold yellow]⚙️  Configuration Setup[/bold yellow]\n"
            "Please provide the following information:",
            border_style="yellow"
        ))
        
        # File format selection
        self.console.print("\n[cyan]📁 Output Format:[/cyan]")
        file_format = Prompt.ask(
            "  Choose format",
            choices=["excel", "csv"],
            default="excel"
        )
        
        # Output filename
        self.console.print("\n[cyan]📝 Output Filename:[/cyan]")
        output_filename = Prompt.ask(
            "  Enter filename (without extension)",
            default="invoice_data"
        )
        
        # Add appropriate extension
        output_file = f"{output_filename}.{'xlsx' if file_format == 'excel' else 'csv'}"
        
        # Check if file exists
        mode = 'write'
        if os.path.exists(output_file):
            self.console.print(f"\n[yellow]⚠️  File '{output_file}' already exists[/yellow]")
            if Confirm.ask("  Do you want to append to existing file?", default=False):
                mode = 'append'
                self.console.print("[green]  ✓ Data will be appended[/green]")
            else:
                self.console.print("[yellow]  ✓ File will be overwritten[/yellow]")
        
        # Input file selection
        self.console.print("\n[cyan]📂 Input Configuration:[/cyan]")
        input_pdf_file = Prompt.ask(
            "  Enter input PDF path",
            default="pdfs/invoice.pdf"
        )
        
        output_folder = Prompt.ask(
            "  Enter output folder for split invoices",
            default="individual_invoice"
        )
        
        return {
            'file_format': file_format,
            'output_file': output_file,
            'mode': mode,
            'input_pdf_file': input_pdf_file,
            'output_folder': output_folder
        }

    def display_processing_summary(self, total_invoices, total_items):
        """Display processing summary in a panel"""
        summary_table = Table(show_header=False, box=box.SIMPLE)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green bold")
        
        summary_table.add_row("📄 Invoices Processed", str(total_invoices))
        summary_table.add_row("📦 Total Items Extracted", str(total_items))
        summary_table.add_row("⏱️  Completed At", datetime.now().strftime('%H:%M:%S'))
        
        self.console.print("\n")
        self.console.print(Panel(
            summary_table,
            title="[bold green]✅ Processing Complete[/bold green]",
            border_style="green"
        ))

    def display_data_preview(self, df, num_rows=10):
        """Display data preview in a rich table"""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold cyan]📊 Data Preview[/bold cyan]",
            border_style="cyan"
        ))
        
        preview_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        
        # Add columns (showing subset for readability)
        display_cols = ["VCH/BILL_NO", "PARTY_NAME", "ITEM_NAME", "QUANTITY", "PRICE", "AMOUNT"]
        for col in display_cols:
            if col in df.columns:
                preview_table.add_column(col, style="cyan")
        
        # Add rows
        for idx, row in df.head(num_rows).iterrows():
            preview_table.add_row(*[str(row[col]) if col in df.columns else "" for col in display_cols])
        
        if len(df) > num_rows:
            preview_table.add_row(*["..." for _ in display_cols], style="dim")
        
        self.console.print(preview_table)

    def export_data(self, all_rows, output_file, file_format, mode='write'):
        """Export data to Excel or CSV"""
        df = pd.DataFrame(all_rows)
        
        # Reorder columns
        column_order = [
            "VCH_SERIES", "SALE/PURC_TYPE", "MC_NAME", "VCH/BILL_DATE", 
            "VCH/BILL_NO", "PARTY_NAME", "ITEM_NAME", "QUANTITY", "UNIT", 
            "PRICE", "DISCOUNT_PERCENT", "LIST_PRICE_ALT_UNIT", "LIST_PRICE", "AMOUNT"
        ]
        df = df[column_order]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=self.console
        ) as progress:
            task = progress.add_task("[cyan]Exporting data...", total=100)
            
            if file_format.lower() == 'excel':
                if mode == 'append' and os.path.exists(output_file):
                    existing_df = pd.read_excel(output_file)
                    df = pd.concat([existing_df, df], ignore_index=True)
                progress.update(task, advance=50)
                
                df.to_excel(output_file, index=False, engine='openpyxl')
                progress.update(task, advance=50)
                
            elif file_format.lower() == 'csv':
                if mode == 'append' and os.path.exists(output_file):
                    df.to_csv(output_file, mode='a', header=False, index=False)
                else:
                    df.to_csv(output_file, index=False)
                progress.update(task, advance=100)
        
        self.console.print(f"[green]✓ Data exported to {output_file}[/green]")
        return df

    def process_invoices(self, config):
        """Process all invoices with progress tracking"""
        self.console.print("\n")
        self.console.print(Panel.fit(
            "[bold yellow]🔄 Processing Invoices[/bold yellow]",
            border_style="yellow"
        ))
        
        # Split invoices
        with self.console.status("[bold green]Splitting PDF into individual invoices...") as status:
            paths = invoice_splitter.split_invoices(
                config['input_pdf_file'], 
                config['output_folder']
            )
        
        self.console.print(f"[green]✓ Split into {len(paths)} invoices[/green]\n")
        
        # Process each invoice
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task = progress.add_task("[cyan]Processing invoices...", total=len(paths))
            
            for idx, path in enumerate(paths, 1):
                progress.update(task, description=f"[cyan]Processing invoice {idx}/{len(paths)}")
                
                doc_data = dataocr.extract_invoice_data(path)
                table_data = table_extractor.process_items(path)
                doc_data["items"] = table_data
                
                rows = self.process_invoice_to_rows(doc_data)
                self.all_rows.extend(rows)
                
                progress.update(task, advance=1)
        
        self.console.print(f"[green]✓ All invoices processed successfully[/green]")
        return len(paths)

    def run(self):
        """Main execution flow"""
        try:
            # Display banner
            self.display_banner()
            
            # Get user inputs
            config = self.get_user_inputs()
            
            # Process invoices
            total_invoices = self.process_invoices(config)
            
            # Export data
            self.console.print("\n")
            df = self.export_data(
                self.all_rows, 
                config['output_file'], 
                config['file_format'], 
                config['mode']
            )
            
            # Display summary
            self.display_processing_summary(total_invoices, len(self.all_rows))
            
            # Display preview
            self.display_data_preview(df)
            
            # Success message
            self.console.print("\n")
            self.console.print(Panel.fit(
                f"[bold green]🎉 Export Complete![/bold green]\n"
                f"Output file: [cyan]{config['output_file']}[/cyan]\n"
                f"Total records: [yellow]{len(self.all_rows)}[/yellow]",
                border_style="green"
            ))
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            sys.exit(0)
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Error: {str(e)}[/bold red]")
            sys.exit(1)

def main():
    exporter = InvoiceExporter()
    exporter.run()

if __name__ == "__main__":
    main()