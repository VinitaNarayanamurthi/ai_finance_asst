from database import SessionLocal
from models import User, Portfolio, Holding
import crud

# Create session
db = SessionLocal()

# ============ EXAMPLES ============

# Get all users
users = crud.get_all_users(db)
for user in users:
    print(f"{user.user_id}: {user.name} ({user.email})")

# Get user portfolios
portfolios = crud.get_user_portfolios(db, user_id=1)
for p in portfolios:
    print(f"Portfolio: {p.name}")

# Get portfolio value
value = crud.get_portfolio_value(db, portfolio_id=1)
print(f"Total Value: ${value['total_value']:,.2f}")
print(f"Total Gain: ${value['total_gain_loss']:,.2f} ({value['return_percent']:.2f}%)")

# Show holdings
for h in value['holdings']:
    print(f"  {h['symbol']}: ${h['value']:,.2f} ({h['return_percent']:.2f}%)")

# Close session
db.close()