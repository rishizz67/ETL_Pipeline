import pandas as pd
import json
import random
from faker import Faker

fake = Faker('en_IN')
random.seed(42)

# ── Generate users.csv ──
users = []
for i in range(1, 51):
    user = {
        "user_id": f"U{i:03d}",
        "name": fake.name() if random.random() > 0.1 else "",
        "email": fake.email() if random.random() > 0.15 else "bad@",
        "age": random.randint(18, 60) if random.random() > 0.1 else None,
        "city": fake.city() if random.random() > 0.1 else None,
        "phone": fake.phone_number(),
        "status": random.choice(["active", "active", "active", "inactive", "pending"]),
        "signup_date": str(fake.date_between(start_date='-2y', end_date='today'))
    }
    users.append(user)

# Add 5 deliberate duplicates
for _ in range(5):
    users.append(random.choice(users[:20]))

df = pd.DataFrame(users)
df.to_csv("data/users.csv", index=False)
print(f"✓ users.csv created — {len(df)} rows")

# ── Generate orders.json ──
orders = []
for i in range(1, 81):
    order = {
        "order_id": f"O{i:04d}",
        "user_id": f"U{random.randint(1, 55):03d}",
        "product_id": f"P{random.randint(1, 10):02d}",
        "amount": round(random.uniform(199, 9999), 2) if random.random() > 0.1 else None,
        "quantity": random.randint(1, 5),
        "order_date": str(fake.date_between(start_date='-1y', end_date='today')),
        "payment_method": random.choice(["UPI", "Card", "COD", "Netbanking"])
    }
    orders.append(order)

with open("data/orders.json", "w") as f:
    json.dump(orders, f, indent=2)
print(f"✓ orders.json created — {len(orders)} records")
