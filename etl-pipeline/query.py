import pandas as pd
from sqlalchemy import create_engine

engine = create_engine("sqlite:///output/pipeline.db")

print("\n── Users by Segment ──")
print(pd.read_sql("SELECT segment, COUNT(*) as count FROM users GROUP BY segment", engine))

print("\n── Top 5 Cities ──")
print(pd.read_sql("SELECT city, COUNT(*) as users FROM users GROUP BY city ORDER BY users DESC LIMIT 5", engine))

print("\n── Orders by Payment Method ──")
print(pd.read_sql("SELECT payment_method, COUNT(*) as orders, ROUND(SUM(amount),2) as revenue FROM orders GROUP BY payment_method", engine))

print("\n── Premium Users Count ──")
print(pd.read_sql("SELECT is_premium, COUNT(*) as count FROM users GROUP BY is_premium", engine))

print("\n── ETL Summary ──")
print(pd.read_sql("SELECT * FROM etl_summary", engine))
