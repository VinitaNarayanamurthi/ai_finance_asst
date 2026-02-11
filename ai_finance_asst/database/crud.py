
# =============================================
# crud.py - Database Operations
# =============================================

from sqlalchemy.orm import Session
from models import User, Portfolio, Holding, Transaction, MarketData, PortfolioSnapshot
from decimal import Decimal
from typing import List, Optional


# ============ USERS ============

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def get_all_users(db: Session) -> List[User]:
    return db.query(User).all()

def create_user(db: Session, email: str, name: str, phone: str = None, risk_profile: str = "moderate") -> User:
    user = User(email=email, name=name, phone=phone, risk_profile=risk_profile)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============ PORTFOLIOS ============

def get_portfolio(db: Session, portfolio_id: int) -> Optional[Portfolio]:
    return db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()

def get_user_portfolios(db: Session, user_id: int) -> List[Portfolio]:
    return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

def create_portfolio(db: Session, user_id: int, name: str) -> Portfolio:
    portfolio = Portfolio(user_id=user_id, name=name)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


# ============ HOLDINGS ============

def get_portfolio_holdings(db: Session, portfolio_id: int) -> List[Holding]:
    return db.query(Holding).filter(Holding.portfolio_id == portfolio_id).all()

def add_holding(db: Session, portfolio_id: int, symbol: str, asset_type: str, quantity: Decimal, average_cost:
Decimal) -> Holding:
    holding = Holding(
        portfolio_id=portfolio_id,
        symbol=symbol,
        asset_type=asset_type,
        quantity=quantity,
        average_cost=average_cost
    )
    db.add(holding)
    db.commit()
    db.refresh(holding)
    return holding

def update_holding(db: Session, holding_id: int, quantity: Decimal, average_cost: Decimal) -> Holding:
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if holding:
        holding.quantity = quantity
        holding.average_cost = average_cost
        db.commit()
        db.refresh(holding)
    return holding


# ============ TRANSACTIONS ============

def get_portfolio_transactions(db: Session, portfolio_id: int) -> List[Transaction]:
    return db.query(Transaction).filter(Transaction.portfolio_id == portfolio_id).all()

def add_transaction(db: Session, portfolio_id: int, symbol: str, type: str, quantity: Decimal, price: Decimal,
transaction_date) -> Transaction:
    transaction = Transaction(
        portfolio_id=portfolio_id,
        symbol=symbol,
        type=type,
        quantity=quantity,
        price=price,
        transaction_date=transaction_date
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


# ============ MARKET DATA ============

def get_market_data(db: Session, symbol: str) -> Optional[MarketData]:
    return db.query(MarketData).filter(MarketData.symbol == symbol).first()

def get_all_market_data(db: Session) -> List[MarketData]:
    return db.query(MarketData).all()

def update_market_data(db: Session, symbol: str, current_price: Decimal, day_change_percent: Decimal = None, beta:
Decimal = None) -> MarketData:
    market = db.query(MarketData).filter(MarketData.symbol == symbol).first()
    if market:
        market.current_price = current_price
        if day_change_percent:
            market.day_change_percent = day_change_percent
        if beta:
            market.beta = beta
    else:
        market = MarketData(symbol=symbol, current_price=current_price, day_change_percent=day_change_percent,
beta=beta)
        db.add(market)
    db.commit()
    db.refresh(market)
    return market


# ============ PORTFOLIO VALUE ============

def get_portfolio_value(db: Session, portfolio_id: int) -> dict:
    holdings = get_portfolio_holdings(db, portfolio_id)

    total_cost = Decimal(0)
    total_value = Decimal(0)
    holdings_data = []

    for h in holdings:
        market = get_market_data(db, h.symbol)
        current_price = market.current_price if market else h.average_cost

        cost = h.quantity * h.average_cost
        value = h.quantity * current_price
        gain_loss = value - cost

        total_cost += cost
        total_value += value

        holdings_data.append({
            "symbol": h.symbol,
            "quantity": float(h.quantity),
            "average_cost": float(h.average_cost),
            "current_price": float(current_price),
            "cost": float(cost),
            "value": float(value),
            "gain_loss": float(gain_loss),
            "return_percent": float(gain_loss / cost * 100) if cost > 0 else 0
        })

    return {
        "total_cost": float(total_cost),
        "total_value": float(total_value),
        "total_gain_loss": float(total_value - total_cost),
        "return_percent": float((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0,
        "holdings": holdings_data
    }