"""Portfolio Analyzer — multi-sheet Excel reader with diversification metrics
 and charts.
 This handles all 5 sheets from your Excel file:

  Metrics computed:
  - Per-holding: current value, weight, gain/loss (absolute + %), top/bottom performers
  - Diversification: Herfindahl-Hirschman Index (HHI), effective number of holdings, top-5 concentration, largest
  holding weight, sector count
  - Sector/Asset allocation: value and weight per sector and asset type
  - Transaction summary: total count, date range, most traded tickers, buy/sell breakdown
  - Snapshot risk metrics: total return, max drawdown, daily/annualized volatility, portfolio value timeline

  Charts generated (7 PNGs):
  1. Holdings pie chart (small holdings grouped as "Others")
  2. Sector allocation pie chart
  3. Asset type allocation pie chart
  4. Gain/loss bar chart per holding
  5. Top performers horizontal bar
  6. Portfolio value over time (line chart from snapshots)
  7. Diversification summary (HHI gauge + top-5 concentration)

  Usage:

  python portfolio_analyzer.py my_portfolio.xlsx charts/
 
 
 
 
 """

import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def load_all_sheets(file_path: str) -> dict[str, pd.DataFrame]:
    """Load all sheets from an Excel file into a dict of DataFrames."""
    ext = Path(file_path).suffix.lower()
    if ext in (".xlsx", ".xls"):
        xls = pd.ExcelFile(file_path, engine="openpyxl")
        sheets = {}
        for name in xls.sheet_names:
            sheets[name.lower().strip().replace(" ", "_")] = xls.parse(name)
        return sheets
    elif ext == ".csv":
        return {"holdings": pd.read_csv(file_path)}
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _safe_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Find first matching column name (case-insensitive)."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c.lower() in cols_lower:
            return cols_lower[c.lower()]
    return None


# ---------------------------------------------------------------------------
# Metrics calculations
# ---------------------------------------------------------------------------

def calc_holdings_metrics(holdings: pd.DataFrame) -> dict:
    """Compute per-holding and portfolio-level metrics from the holdings sheet."""
    results = {}

    ticker_col = _safe_col(holdings, ["ticker", "symbol", "stock", "name", "holding", "instrument"])
    qty_col = _safe_col(holdings, ["quantity", "shares", "units", "qty"])
    buy_col = _safe_col(holdings, ["buy_price", "avg_cost", "cost_basis", "purchase_price", "cost_price", "cost"])
    cur_col = _safe_col(holdings, ["current_price", "market_price", "price", "ltp", "close", "last_price"])
    sector_col = _safe_col(holdings, ["sector", "industry", "category", "segment", "asset_class"])
    asset_type_col = _safe_col(holdings, ["asset_type", "type", "asset_class", "instrument_type"])

    if ticker_col is None:
        raise ValueError("Cannot find ticker/symbol column in holdings sheet.")

    tickers = holdings[ticker_col].astype(str).tolist()
    quantities = holdings[qty_col].astype(float).tolist() if qty_col else [1.0] * len(tickers)
    buy_prices = holdings[buy_col].astype(float).tolist() if buy_col else None
    cur_prices = holdings[cur_col].astype(float).tolist() if cur_col else None

    # --- Current values ---
    if cur_prices:
        current_values = [q * p for q, p in zip(quantities, cur_prices)]
    elif buy_prices:
        current_values = [q * p for q, p in zip(quantities, buy_prices)]
    else:
        current_values = quantities

    invested_values = [q * p for q, p in zip(quantities, buy_prices)] if buy_prices else None
    total_value = sum(current_values)
    total_invested = sum(invested_values) if invested_values else None

    results["tickers"] = tickers
    results["current_values"] = dict(zip(tickers, current_values))
    results["total_portfolio_value"] = total_value
    results["total_invested"] = total_invested
    results["num_holdings"] = len(tickers)

    # --- Weight of each holding ---
    weights = [v / total_value for v in current_values] if total_value > 0 else [0] * len(tickers)
    results["weights"] = dict(zip(tickers, weights))

    # --- Gain / Loss ---
    if buy_prices and cur_prices:
        gain_loss = [q * (c - b) for q, b, c in zip(quantities, buy_prices, cur_prices)]
        gain_loss_pct = [((c - b) / b * 100) if b != 0 else 0.0 for b, c in zip(buy_prices, cur_prices)]
        results["gain_loss"] = dict(zip(tickers, gain_loss))
        results["gain_loss_pct"] = dict(zip(tickers, gain_loss_pct))
        results["total_gain_loss"] = sum(gain_loss)
        results["total_return_pct"] = (total_value - total_invested) / total_invested * 100 if total_invested else 0

        sorted_perf = sorted(zip(tickers, gain_loss_pct), key=lambda x: x[1], reverse=True)
        results["top_performers"] = sorted_perf[:5]
        results["bottom_performers"] = sorted_perf[-5:]

    # --- Sector allocation ---
    if sector_col:
        sector_values = {}
        for sector, val in zip(holdings[sector_col].astype(str), current_values):
            sector_values[sector] = sector_values.get(sector, 0.0) + val
        results["sector_allocation"] = sector_values
        results["sector_weights"] = {s: v / total_value for s, v in sector_values.items()}

    # --- Asset type allocation ---
    if asset_type_col:
        asset_values = {}
        for atype, val in zip(holdings[asset_type_col].astype(str), current_values):
            asset_values[atype] = asset_values.get(atype, 0.0) + val
        results["asset_type_allocation"] = asset_values

    # --- Diversification metrics ---
    w = np.array(weights)
    hhi = float(np.sum(w ** 2))  # Herfindahl-Hirschman Index (0-1, lower = more diversified)
    effective_n = 1.0 / hhi if hhi > 0 else 0  # equivalent number of equal-weight holdings
    top5_concentration = sum(sorted(weights, reverse=True)[:5])

    results["diversification"] = {
        "herfindahl_index": round(hhi, 4),
        "effective_num_holdings": round(effective_n, 2),
        "top5_concentration": round(top5_concentration * 100, 2),
        "num_sectors": len(results.get("sector_allocation", {})),
        "largest_holding_weight": round(max(weights) * 100, 2) if weights else 0,
        "largest_holding": tickers[weights.index(max(weights))] if weights else None,
    }

    return results


def calc_transaction_metrics(transactions: pd.DataFrame) -> dict:
    """Compute metrics from the transactions sheet."""
    results = {}

    date_col = _safe_col(transactions, ["date", "trade_date", "transaction_date", "timestamp"])
    action_col = _safe_col(transactions, ["action", "type", "side", "transaction_type", "buy_sell"])
    amount_col = _safe_col(transactions, ["amount", "total", "value", "net_amount"])
    ticker_col = _safe_col(transactions, ["ticker", "symbol", "stock", "name"])

    if date_col:
        transactions[date_col] = pd.to_datetime(transactions[date_col], errors="coerce")
        results["first_transaction"] = str(transactions[date_col].min().date())
        results["last_transaction"] = str(transactions[date_col].max().date())
        results["total_transactions"] = len(transactions)

    if action_col:
        action_counts = transactions[action_col].value_counts().to_dict()
        results["transaction_breakdown"] = action_counts

    if amount_col:
        results["total_invested_via_transactions"] = float(transactions[amount_col].sum())

    if ticker_col:
        results["unique_tickers_traded"] = transactions[ticker_col].nunique()
        results["most_traded"] = transactions[ticker_col].value_counts().head(5).to_dict()

    return results


def calc_snapshot_metrics(snapshots: pd.DataFrame) -> dict:
    """Compute metrics from portfolio snapshots (value over time)."""
    results = {}

    date_col = _safe_col(snapshots, ["date", "snapshot_date", "timestamp", "period"])
    value_col = _safe_col(snapshots, ["value", "portfolio_value", "total_value", "nav", "amount"])

    if date_col and value_col:
        snapshots = snapshots.sort_values(date_col)
        snapshots[date_col] = pd.to_datetime(snapshots[date_col], errors="coerce")
        values = snapshots[value_col].astype(float)

        results["start_value"] = float(values.iloc[0])
        results["end_value"] = float(values.iloc[-1])
        results["total_return_pct"] = round((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100, 2)
        results["max_value"] = float(values.max())
        results["min_value"] = float(values.min())

        # Max drawdown
        cummax = values.cummax()
        drawdown = (values - cummax) / cummax
        results["max_drawdown_pct"] = round(float(drawdown.min()) * 100, 2)

        # Volatility (daily returns std annualized)
        returns = values.pct_change().dropna()
        if len(returns) > 1:
            results["daily_volatility"] = round(float(returns.std()) * 100, 4)
            results["annualized_volatility"] = round(float(returns.std() * np.sqrt(252)) * 100, 2)

        results["snapshot_dates"] = snapshots[date_col].dt.strftime("%Y-%m-%d").tolist()
        results["snapshot_values"] = values.tolist()

    return results


# ---------------------------------------------------------------------------
# Chart generation
# ---------------------------------------------------------------------------

def _save(fig, path):
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


def generate_charts(results: dict, output_dir: str = "charts") -> dict[str, str]:
    """Generate all relevant charts and return {name: file_path}."""
    os.makedirs(output_dir, exist_ok=True)
    charts = {}

    # 1. Holdings pie chart (by value)
    cv = results.get("current_values", {})
    if cv:
        fig, ax = plt.subplots(figsize=(9, 7))
        labels = list(cv.keys())
        values = list(cv.values())
        # Group small holdings (<3%) into "Others"
        total = sum(values)
        main_labels, main_values, others = [], [], 0
        for l, v in zip(labels, values):
            if v / total >= 0.03:
                main_labels.append(l)
                main_values.append(v)
            else:
                others += v
        if others > 0:
            main_labels.append("Others")
            main_values.append(others)
        ax.pie(main_values, labels=main_labels, autopct="%1.1f%%", startangle=140)
        ax.set_title("Portfolio Composition by Holding")
        charts["holdings_pie"] = _save(fig, os.path.join(output_dir, "holdings_pie.png"))

    # 2. Sector allocation pie chart
    sa = results.get("sector_allocation", {})
    if sa:
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.pie(sa.values(), labels=sa.keys(), autopct="%1.1f%%", startangle=140)
        ax.set_title("Sector Allocation")
        charts["sector_pie"] = _save(fig, os.path.join(output_dir, "sector_pie.png"))

    # 3. Asset type pie chart
    at = results.get("asset_type_allocation", {})
    if at:
        fig, ax = plt.subplots(figsize=(9, 7))
        ax.pie(at.values(), labels=at.keys(), autopct="%1.1f%%", startangle=140)
        ax.set_title("Asset Type Allocation")
        charts["asset_type_pie"] = _save(fig, os.path.join(output_dir, "asset_type_pie.png"))

    # 4. Gain/loss bar chart
    gl = results.get("gain_loss", {})
    if gl:
        fig, ax = plt.subplots(figsize=(max(8, len(gl) * 0.6), 6))
        colors = ["green" if v >= 0 else "red" for v in gl.values()]
        ax.bar(gl.keys(), gl.values(), color=colors)
        ax.set_title("Gain / Loss per Holding")
        ax.set_ylabel("Gain / Loss")
        ax.axhline(0, color="black", linewidth=0.8)
        plt.xticks(rotation=45, ha="right")
        charts["gain_loss_bar"] = _save(fig, os.path.join(output_dir, "gain_loss_bar.png"))

    # 5. Top performers horizontal bar
    top = results.get("top_performers", [])
    if top:
        names = [t[0] for t in top]
        pcts = [t[1] for t in top]
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = ["green" if v >= 0 else "red" for v in pcts]
        ax.barh(names[::-1], pcts[::-1], color=colors[::-1])
        ax.set_title("Top Performers (% Change)")
        ax.set_xlabel("% Change")
        charts["top_performers"] = _save(fig, os.path.join(output_dir, "top_performers.png"))

    # 6. Portfolio value over time (from snapshots)
    dates = results.get("snapshot_dates", [])
    vals = results.get("snapshot_values", [])
    if dates and vals:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(pd.to_datetime(dates), vals, color="steelblue", linewidth=2)
        ax.set_title("Portfolio Value Over Time")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45, ha="right")
        charts["portfolio_value_timeline"] = _save(fig, os.path.join(output_dir, "portfolio_timeline.png"))

    # 7. Diversification summary bar
    div = results.get("diversification", {})
    if div:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        # HHI gauge
        ax = axes[0]
        hhi = div["herfindahl_index"]
        color = "green" if hhi < 0.15 else "orange" if hhi < 0.25 else "red"
        label = "Well Diversified" if hhi < 0.15 else "Moderate" if hhi < 0.25 else "Concentrated"
        ax.barh(["HHI"], [hhi], color=color, height=0.4)
        ax.set_xlim(0, 1)
        ax.set_title(f"Concentration Index: {label}")
        ax.set_xlabel("HHI (lower = more diversified)")

        # Top 5 concentration
        ax = axes[1]
        t5 = div["top5_concentration"]
        ax.barh(["Top 5 Holdings"], [t5], color="steelblue", height=0.4)
        ax.set_xlim(0, 100)
        ax.set_title(f"Top 5 Concentration: {t5:.1f}%")
        ax.set_xlabel("% of Portfolio")

        plt.tight_layout()
        charts["diversification_summary"] = _save(fig, os.path.join(output_dir, "diversification.png"))

    return charts


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def analyze_portfolio(file_path: str, output_dir: str = "charts") -> dict:
    """Analyze a multi-sheet portfolio Excel file.

    Expected sheets: Portfolio, Holdings, Transactions, Market_Data, Portfolio_Snapshots
    (auto-detected, case-insensitive)

    Returns dict with all metrics + chart file paths.
    """
    sheets = load_all_sheets(file_path)

    results = {"sheets_found": list(sheets.keys())}

    # --- Holdings ---
    holdings_key = None
    for key in sheets:
        if "holding" in key:
            holdings_key = key
            break
    if holdings_key:
        holdings_metrics = calc_holdings_metrics(sheets[holdings_key])
        results.update(holdings_metrics)

    # --- Transactions ---
    txn_key = None
    for key in sheets:
        if "transaction" in key:
            txn_key = key
            break
    if txn_key:
        txn_metrics = calc_transaction_metrics(sheets[txn_key])
        results["transactions"] = txn_metrics

    # --- Portfolio Snapshots ---
    snap_key = None
    for key in sheets:
        if "snapshot" in key:
            snap_key = key
            break
    if snap_key:
        snap_metrics = calc_snapshot_metrics(sheets[snap_key])
        results.update(snap_metrics)

    # --- Market Data (merge current prices into holdings if available) ---
    market_key = None
    for key in sheets:
        if "market" in key:
            market_key = key
            break
    if market_key:
        results["market_data_available"] = True

    # --- Generate charts ---
    charts = generate_charts(results, output_dir)
    results["chart_paths"] = charts

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python portfolio_analyzer.py <file_path> [output_dir]")
        sys.exit(1)

    result = analyze_portfolio(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "charts")

    print(f"\nPortfolio Analysis Results")
    print(f"{'=' * 50}")
    print(f"Sheets found: {result['sheets_found']}")
    print(f"Holdings: {result.get('num_holdings', 'N/A')}")
    print(f"Total portfolio value: {result.get('total_portfolio_value', 0):,.2f}")
    print(f"Total invested: {result.get('total_invested', 0):,.2f}")

    if result.get("total_gain_loss") is not None:
        print(f"Total gain/loss: {result['total_gain_loss']:,.2f}")
        print(f"Total return: {result.get('total_return_pct', 0):+.2f}%")

    div = result.get("diversification", {})
    if div:
        print(f"\nDiversification Metrics:")
        print(f"  HHI (Herfindahl Index): {div['herfindahl_index']} (lower = better)")
        print(f"  Effective # holdings: {div['effective_num_holdings']}")
        print(f"  Top 5 concentration: {div['top5_concentration']}%")
        print(f"  # Sectors: {div['num_sectors']}")
        print(f"  Largest holding: {div['largest_holding']} ({div['largest_holding_weight']}%)")

    if result.get("sector_allocation"):
        print(f"\nSector Allocation:")
        for s, v in result["sector_allocation"].items():
            pct = result["sector_weights"][s] * 100
            print(f"  {s}: {v:,.2f} ({pct:.1f}%)")

    if result.get("top_performers"):
        print(f"\nTop Performers:")
        for name, pct in result["top_performers"]:
            print(f"  {name}: {pct:+.2f}%")

    if result.get("max_drawdown_pct") is not None:
        print(f"\nRisk Metrics (from snapshots):")
        print(f"  Max drawdown: {result['max_drawdown_pct']}%")
        print(f"  Annualized volatility: {result.get('annualized_volatility', 'N/A')}%")

    if result.get("transactions"):
        t = result["transactions"]
        print(f"\nTransaction Summary:")
        print(f"  Total transactions: {t.get('total_transactions', 'N/A')}")
        print(f"  Period: {t.get('first_transaction', '?')} to {t.get('last_transaction', '?')}")
        print(f"  Unique tickers traded: {t.get('unique_tickers_traded', 'N/A')}")