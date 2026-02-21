#!/usr/bin/env python3
"""
Create sample portfolio XLSX file using openpyxl
"""

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    from datetime import datetime, timedelta
except ImportError:
    print("Error: openpyxl not installed. Install with: pip install openpyxl")
    exit(1)

# Create workbook
wb = Workbook()
wb.remove(wb.active)  # Remove default sheet

# ===== HOLDINGS SHEET =====
holdings_ws = wb.create_sheet("Holdings")
holdings_headers = ["Type", "Symbol", "Quantity", "Average Cost", "Current Price", "Asset Type", "Total Value", "Total Cost"]
for col_num, header in enumerate(holdings_headers, 1):
    cell = holdings_ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

holdings_data = [
    ["Holding", "AAPL", 50, 145.50, 185.30, "Stock", "=C2*E2", "=C2*D2"],
    ["Holding", "MSFT", 30, 310.25, 380.15, "Stock", "=C3*E3", "=C3*D3"],
    ["Holding", "GOOGL", 20, 2800.75, 3100.25, "Stock", "=C4*E4", "=C4*D4"],
    ["Holding", "AMZN", 25, 3200.50, 3450.75, "Stock", "=C5*E5", "=C5*D5"],
    ["Holding", "TSLA", 15, 850.00, 920.50, "Stock", "=C6*E6", "=C6*D6"],
    ["Holding", "META", 40, 250.00, 280.25, "Stock", "=C7*E7", "=C7*D7"],
]

for row_num, row_data in enumerate(holdings_data, 2):
    for col_num, value in enumerate(row_data, 1):
        cell = holdings_ws.cell(row=row_num, column=col_num)
        if isinstance(value, str) and value.startswith("="):
            cell.value = value  # Formula
        else:
            cell.value = value

# Set column widths
holdings_ws.column_dimensions['A'].width = 12
holdings_ws.column_dimensions['B'].width = 10
holdings_ws.column_dimensions['C'].width = 12
holdings_ws.column_dimensions['D'].width = 14
holdings_ws.column_dimensions['E'].width = 14
holdings_ws.column_dimensions['F'].width = 12
holdings_ws.column_dimensions['G'].width = 12
holdings_ws.column_dimensions['H'].width = 12

# ===== TRANSACTIONS SHEET =====
transactions_ws = wb.create_sheet("Transactions")
transactions_headers = ["Type", "Date", "Symbol", "Transaction Type", "Quantity", "Price", "Amount"]
for col_num, header in enumerate(transactions_headers, 1):
    cell = transactions_ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

base_date = datetime(2024, 1, 1)
transactions_data = [
    ["Transaction", "2024-01-01", "AAPL", "Buy", 10, 145.50, "=E2*F2"],
    ["Transaction", "2024-01-11", "MSFT", "Buy", 5, 310.25, "=E3*F3"],
    ["Transaction", "2024-01-21", "GOOGL", "Buy", 2, 2800.75, "=E4*F4"],
    ["Transaction", "2024-01-31", "AMZN", "Buy", 5, 3200.50, "=E5*F5"],
    ["Transaction", "2024-02-10", "AAPL", "Sell", 8, 185.30, "=E6*F6"],
    ["Transaction", "2024-02-20", "TSLA", "Buy", 3, 850.00, "=E7*F7"],
    ["Transaction", "2024-03-01", "META", "Buy", 10, 280.25, "=E8*F8"],
    ["Transaction", "2024-03-11", "GOOGL", "Sell", 1, 3100.25, "=E9*F9"],
]

for row_num, row_data in enumerate(transactions_data, 2):
    for col_num, value in enumerate(row_data, 1):
        cell = transactions_ws.cell(row=row_num, column=col_num)
        if isinstance(value, str) and value.startswith("="):
            cell.value = value  # Formula
        else:
            cell.value = value

# Set column widths
transactions_ws.column_dimensions['A'].width = 15
transactions_ws.column_dimensions['B'].width = 12
transactions_ws.column_dimensions['C'].width = 10
transactions_ws.column_dimensions['D'].width = 18
transactions_ws.column_dimensions['E'].width = 12
transactions_ws.column_dimensions['F'].width = 12
transactions_ws.column_dimensions['G'].width = 12

# ===== PORTFOLIO SUMMARY SHEET =====
summary_ws = wb.create_sheet("Portfolio Summary")
summary_headers = ["Metric", "Value", "Details"]
for col_num, header in enumerate(summary_headers, 1):
    cell = summary_ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")

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

for row_num, row_data in enumerate(summary_data, 2):
    for col_num, value in enumerate(row_data, 1):
        cell = summary_ws.cell(row=row_num, column=col_num)
        cell.value = value

# Set column widths
summary_ws.column_dimensions['A'].width = 20
summary_ws.column_dimensions['B'].width = 20
summary_ws.column_dimensions['C'].width = 40

# ===== ASSET ALLOCATION SHEET =====
allocation_ws = wb.create_sheet("Asset Allocation")
allocation_headers = ["Asset Class", "Symbol", "Allocation %", "Value", "Holdings Count"]
for col_num, header in enumerate(allocation_headers, 1):
    cell = allocation_ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="0066CC", end_color="0066CC", fill_type="solid")

allocation_data = [
    ["Technology", "AAPL", 10.78, 9226.50, 1],
    ["Technology", "MSFT", 13.23, 11404.50, 1],
    ["Cloud Computing", "GOOGL", 7.25, 6210.50, 1],
    ["E-commerce", "AMZN", 11.04, 9456.88, 1],
    ["Electric Vehicles", "TSLA", 4.03, 3450.75, 1],
    ["Social Media", "META", 13.05, 11210.00, 1],
]

for row_num, row_data in enumerate(allocation_data, 2):
    for col_num, value in enumerate(row_data, 1):
        cell = allocation_ws.cell(row=row_num, column=col_num)
        cell.value = value

# Set column widths
allocation_ws.column_dimensions['A'].width = 20
allocation_ws.column_dimensions['B'].width = 10
allocation_ws.column_dimensions['C'].width = 15
allocation_ws.column_dimensions['D'].width = 15
allocation_ws.column_dimensions['E'].width = 15

# ===== PERFORMANCE SHEET =====
performance_ws = wb.create_sheet("Performance")
performance_headers = ["Month", "Portfolio Value", "Monthly Return %", "YTD Return %", "Cash Balance"]
for col_num, header in enumerate(performance_headers, 1):
    cell = performance_ws.cell(row=1, column=col_num)
    cell.value = header
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="C65911", end_color="C65911", fill_type="solid")

performance_data = [
    ["2024-01", 71747.75, "0.00%", "0.00%", 5000.00],
    ["2024-02", 75432.25, "5.14%", "5.14%", 4200.00],
    ["2024-03", 79850.50, "5.86%", "11.27%", 3500.00],
    ["2024-04", 82340.75, "3.11%", "14.67%", 3200.00],
    ["2024-05", 85532.50, "3.88%", "19.21%", 2800.00],
]

for row_num, row_data in enumerate(performance_data, 2):
    for col_num, value in enumerate(row_data, 1):
        cell = performance_ws.cell(row=row_num, column=col_num)
        cell.value = value

# Set column widths
performance_ws.column_dimensions['A'].width = 12
performance_ws.column_dimensions['B'].width = 18
performance_ws.column_dimensions['C'].width = 18
performance_ws.column_dimensions['D'].width = 15
performance_ws.column_dimensions['E'].width = 15

# Save workbook
output_file = "sample_portfolio_data.xlsx"
wb.save(output_file)

print(f"✅ Sample XLSX file created: {output_file}")
print(f"\n📊 File contains 5 sheets:")
print(f"  1. Holdings        - Current portfolio holdings (6 stocks)")
print(f"  2. Transactions    - Historical transactions (8 records)")
print(f"  3. Portfolio Summary - Overall metrics and stats")
print(f"  4. Asset Allocation - Asset class breakdown")
print(f"  5. Performance     - Monthly portfolio performance")
print(f"\n💡 Ready to analyze with portfolio_analyzer.py!")
