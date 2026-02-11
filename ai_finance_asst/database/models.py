from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

SCHEMA = "finance_asst"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": SCHEMA}

    user_id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(100))
    phone = Column(String(20))
    risk_profile = Column(String(20))
    preferences = Column(JSONB, default={})
    investment_goals = Column(JSONB, default={})
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    portfolios = relationship("Portfolio", back_populates="user")


class Portfolio(Base):
    __tablename__ = "portfolios"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey(f"{SCHEMA}.users.user_id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default="Main Portfolio")
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("Holding", back_populates="portfolio")
    transactions = relationship("Transaction", back_populates="portfolio")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio")


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey(f"{SCHEMA}.portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    asset_type = Column(String(20))
    quantity = Column(Numeric(18, 8), nullable=False)
    average_cost = Column(Numeric(18, 4), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey(f"{SCHEMA}.portfolios.id", ondelete="CASCADE"), nullable=False)
    symbol = Column(String(20), nullable=False)
    type = Column(String(10))
    quantity = Column(Numeric(18, 8), nullable=False)
    price = Column(Numeric(18, 4), nullable=False)
    transaction_date = Column(Date, nullable=False)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")


class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = {"schema": SCHEMA}

    symbol = Column(String(20), primary_key=True)
    current_price = Column(Numeric(18, 4))
    day_change_percent = Column(Numeric(8, 4))
    beta = Column(Numeric(8, 4), default=1.0)
    updated_at = Column(DateTime, server_default=func.now())


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"
    __table_args__ = {"schema": SCHEMA}

    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey(f"{SCHEMA}.portfolios.id", ondelete="CASCADE"), nullable=False)
    snapshot_date = Column(Date, nullable=False)
    total_value = Column(Numeric(18, 4))
    total_cost = Column(Numeric(18, 4))

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
