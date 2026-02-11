import os
from dotenv import load_dotenv

result = load_dotenv("C:\\Users\\vinit\\Documents\\agentic_ai\\capstone_project\\ai_finance_asst\\.env")




DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://2326:postgres@localhost:5432/postgres")
SCHEMA = "finance_asst"