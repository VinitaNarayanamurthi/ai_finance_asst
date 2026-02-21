"""
Create sample portfolio data files (CSV and manually build XLSX structure)
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

# Create output directory
output_dir = Path("sample_data")
output_dir.mkdir(exist_ok=True)

# ===== HOLDINGS CSV =====
holdings_file = output_dir / "holdings.csv"
holdings_headers = ["Type", "Symbol", "Quantity", "Average Cost", "Current Price", "Asset Type"]
holdings_data = [
    ["Holding", "AAPL", 50, 145.50, 185.30, "Stock"],
    ["Holding", "MSFT", 30, 310.25, 380.15, "Stock"],
    ["Holding", "GOOGL", 20, 2800.75, 3100.25, "Stock"],
    ["Holding", "AMZN", 25, 3200.50, 3450.75, "Stock"],
    ["Holding", "TSLA", 15, 850.00, 920.50, "Stock"],
    ["Holding", "META", 40, 250.00, 280.25, "Stock"],
]

with open(holdings_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(holdings_headers)
    writer.writerows(holdings_data)

print(f"✅ Created: {holdings_file}")

# ===== TRANSACTIONS CSV =====
transactions_file = output_dir / "transactions.csv"
transactions_headers = ["Type", "Date", "Symbol", "Transaction Type", "Quantity", "Price", "Amount"]
base_date = datetime(2024, 1, 1)
transactions_data = [
    ["Transaction", "2024-01-01", "AAPL", "Buy", 10, 145.50, 1455.00],
    ["Transaction", "2024-01-11", "MSFT", "Buy", 5, 310.25, 1551.25],
    ["Transaction", "2024-01-21", "GOOGL", "Buy", 2, 2800.75, 5601.50],
    ["Transaction", "2024-01-31", "AMZN", "Buy", 5, 3200.50, 16002.50],
    ["Transaction", "2024-02-10", "AAPL", "Sell", 8, 185.30, 1482.40],
    ["Transaction", "2024-02-20", "TSLA", "Buy", 3, 850.00, 2550.00],
    ["Transaction", "2024-03-01", "META", "Buy", 10, 280.25, 2802.50],
    ["Transaction", "2024-03-11", "GOOGL", "Sell", 1, 3100.25, 3100.25],
]

with open(transactions_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(transactions_headers)
    writer.writerows(transactions_data)

print(f"✅ Created: {transactions_file}")

# ===== PORTFOLIO SUMMARY CSV =====
summary_file = output_dir / "portfolio_summary.csv"
summary_headers = ["Metric", "Value", "Details"]
summary_data = [
    ["Total Holdings Value", 85532.50, "Current market value of all holdings"],
    ["Total Cost Basis", 71747.75, "Total amount invested"],
    ["Total Gains/Losses", 13784.75, "Unrealized gains"],
    ["Gain/Loss %", "19.21%", "Return on investment"],
    ["Number of Holdings", 6, "Total unique stocks"],
    ["Largest Position", "AAPL", "By value"],
    ["Average Gain %", "3.20%", "Average gain per holding"],
    ["Best Performer", "META", "Highest return"],
]

with open(summary_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(summary_headers)
    writer.writerows(summary_data)

print(f"✅ Created: {summary_file}")

# ===== ASSET ALLOCATION CSV =====
allocation_file = output_dir / "asset_allocation.csv"
allocation_headers = ["Asset Class", "Symbol", "Allocation %", "Value", "Holdings Count"]
allocation_data = [
    ["Technology", "AAPL", 10.78, 9226.50, 1],
    ["Technology", "MSFT", 13.23, 11404.50, 1],
    ["Cloud Computing", "GOOGL", 7.25, 6210.50, 1],
    ["E-commerce", "AMZN", 11.04, 9456.88, 1],
    ["Electric Vehicles", "TSLA", 4.03, 3450.75, 1],
    ["Social Media", "META", 13.05, 11210.00, 1],
]

with open(allocation_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(allocation_headers)
    writer.writerows(allocation_data)

print(f"✅ Created: {allocation_file}")

# ===== PERFORMANCE CSV =====
performance_file = output_dir / "performance.csv"
performance_headers = ["Month", "Portfolio Value", "Monthly Return %", "YTD Return %", "Cash Balance"]
performance_data = [
    ["2024-01", 71747.75, "0.00%", "0.00%", 5000.00],
    ["2024-02", 75432.25, "5.14%", "5.14%", 4200.00],
    ["2024-03", 79850.50, "5.86%", "11.27%", 3500.00],
    ["2024-04", 82340.75, "3.11%", "14.67%", 3200.00],
    ["2024-05", 85532.50, "3.88%", "19.21%", 2800.00],
]

with open(performance_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(performance_headers)
    writer.writerows(performance_data)

print(f"✅ Created: {performance_file}")

# ===== CREATE COMBINED XLSX FILE =====
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    
    # Create workbook
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    
    # Add Holdings sheet
    holdings_ws = wb.create_sheet("Holdings")
    holdings_ws.append(holdings_headers)
    for row in holdings_data:
        holdings_ws.append(row)
    
    # Style header
    for cell in holdings_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Add Transactions sheet
    transactions_ws = wb.create_sheet("Transactions")
    transactions_ws.append(transactions_headers)
    for row in transactions_data:
        transactions_ws.append(row)
    
    # Style header
    for cell in transactions_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    
    # Add Portfolio Summary sheet
    summary_ws = wb.create_sheet("Portfolio Summary")
    summary_ws.append(summary_headers)
    for row in summary_data:
        summary_ws.append(row)
    
    # Style header
    for cell in summary_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
    
    # Add Asset Allocation sheet
    allocation_ws = wb.create_sheet("Asset Allocation")
    allocation_ws.append(allocation_headers)
    for row in allocation_data:
        allocation_ws.append(row)
    
    # Style header
    for cell in allocation_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")
    
    # Add Performance sheet
    performance_ws = wb.create_sheet("Performance")
    performance_ws.append(performance_headers)
    for row in performance_data:
        performance_ws.append(row)
    
    # Style header
    for cell in performance_ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="C65911", end_color="C65911", fill_type="solid")
    
    # Adjust column widths
    for ws in [holdings_ws, transactions_ws, summary_ws, allocation_ws, performance_ws]:
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save workbook
    xlsx_file = "sample_portfolio_data.xlsx"
    wb.save(xlsx_file)
    print(f"\n✅ Created: {xlsx_file}")
    
except ImportError:
    print("\n⚠️ openpyxl not installed - XLSX file not created")
    print("   Install with: pip install openpyxl")
    xlsx_file = None

# Summary
print(f"\n" + "="*60)
print("📊 SAMPLE PORTFOLIO DATA FILES CREATED")
print("="*60)
print(f"\n📁 CSV Files (in sample_data/ directory):")
print(f"  • holdings.csv           - Current holdings")
print(f"  • transactions.csv       - Transaction history")
print(f"  • portfolio_summary.csv  - Summary metrics")
print(f"  • asset_allocation.csv   - Asset allocation")
print(f"  • performance.csv        - Performance data")

if xlsx_file:
    print(f"\n📊 XLSX File:")
    print(f"  • {xlsx_file} - All sheets combined")

print(f"\n💡 Usage with portfolio_analyzer.py:")
print(f"   Holdings: Type column identifies 'Holding' vs 'Transaction'")
print(f"   Calculations: Total Value = Quantity * Current Price")
print(f"                 Total Cost = Quantity * Average Cost")
print(f"                 Gain/Loss = Total Value - Total Cost")

print(f"\n✨ Ready to analyze!")
