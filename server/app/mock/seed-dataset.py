"""
Database seeding script for generating mock dataset records.
This script populates the database with realistic business data for testing purposes.
"""

import random

from sqlalchemy.orm import Session

from app.db.database import SessionLocal, engine
from app.models.test_dataset import Base, Dataset

# Sample product names for realistic data
PRODUCT_NAMES = [
  "Product Alpha",
  "Product Beta",
  "Product Gamma",
  "Product Delta",
  "Product Epsilon",
  "Product Zeta",
  "Product Theta",
  "Product Lambda",
  "Product Sigma",
  "Product Omega",
  "Enterprise Suite",
  "Professional Edition",
  "Standard Package",
  "Premium Service",
  "Basic Plan",
  "Advanced Analytics",
  "Cloud Solution",
  "Mobile App",
  "Web Platform",
  "API Gateway",
]

# Month names for consistent data
MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
]

# Years to generate data for
YEARS = ["2020", "2021", "2022", "2023", "2024"]


def generate_realistic_metrics(product_index: int, year_index: int, month_index: int) -> dict:
  """Generate realistic revenue, expenses, and employee data with some patterns."""

  # Base values that vary by product (some products are more successful)
  base_multipliers = [
    1.0,
    1.5,
    0.8,
    2.0,
    1.2,
    0.9,
    1.8,
    1.1,
    1.6,
    0.7,
    2.5,
    2.2,
    1.3,
    1.9,
    0.6,
    1.7,
    2.1,
    1.4,
    1.0,
    0.85,
  ]

  base_multiplier = base_multipliers[product_index % len(base_multipliers)]

  # Year-over-year growth (newer years tend to have higher values)
  year_growth = 1.0 + (year_index * 0.15)  # 15% growth per year

  # Seasonal patterns (Q4 typically higher, summer months lower)
  seasonal_multipliers = [
    0.9,
    0.85,
    1.0,
    1.05,
    1.1,
    0.95,  # Jan-Jun
    0.8,
    0.75,
    0.9,
    1.0,
    1.15,
    1.3,
  ]  # Jul-Dec
  seasonal_multiplier = seasonal_multipliers[month_index]

  # Base revenue calculation
  base_revenue = 50000 + random.randint(-10000, 20000)
  revenue = int(base_revenue * base_multiplier * year_growth * seasonal_multiplier)

  # Expenses are typically 60-80% of revenue
  expense_ratio = random.uniform(0.6, 0.8)
  expenses = int(revenue * expense_ratio)

  # Employee count correlates with business size and grows over time
  base_employees = max(5, int(20 * base_multiplier))
  employee_growth = 1.0 + (year_index * 0.1)  # 10% employee growth per year
  current_employees = int(base_employees * employee_growth) + random.randint(-2, 5)
  current_employees = max(1, current_employees)  # Ensure at least 1 employee

  return {
    "revenue": max(10000, revenue),  # Minimum revenue
    "expenses": max(5000, expenses),  # Minimum expenses
    "current_employees": current_employees,
  }


def generate_mock_dataset(db: Session, num_products: int = 10):
  """Generate mock dataset records with realistic business data."""
  print(f"Generating dataset records for {num_products} products across {len(YEARS)} years...")

  total_records = 0

  for product_idx in range(num_products):
    product_name = PRODUCT_NAMES[product_idx % len(PRODUCT_NAMES)]

    for year_idx, year in enumerate(YEARS):
      for month_idx, month in enumerate(MONTHS):
        metrics = generate_realistic_metrics(product_idx, year_idx, month_idx)

        dataset_record = Dataset(
          product_name=product_name,
          year=year,
          month=month,
          revenue=metrics["revenue"],
          expenses=metrics["expenses"],
          current_employees=metrics["current_employees"],
        )

        db.add(dataset_record)
        total_records += 1

    print(f"✓ Created data for {product_name}")

  db.commit()
  print(f"✅ Successfully created {total_records} dataset records!")
  return total_records


def clear_existing_data(db: Session):
  """Clear existing data from dataset table."""
  print("Clearing existing dataset data...")

  deleted_records = db.query(Dataset).delete()
  db.commit()

  print(f"✓ Deleted {deleted_records} dataset records")


def get_data_summary(db: Session):
  """Get summary statistics of the generated data."""
  total_records = db.query(Dataset).count()

  if total_records == 0:
    return "No data found in dataset table."

  # Get some sample statistics
  products = db.query(Dataset.product_name).distinct().count()
  years = db.query(Dataset.year).distinct().count()

  # Calculate totals
  total_revenue = db.query(Dataset.revenue).all()
  total_expenses = db.query(Dataset.expenses).all()

  avg_revenue = sum(r[0] for r in total_revenue) / len(total_revenue)
  avg_expenses = sum(e[0] for e in total_expenses) / len(total_expenses)

  summary = f"""
📊 Dataset Summary:
   Total records: {total_records:,}
   Unique products: {products}
   Years covered: {years}
   Average monthly revenue: ${avg_revenue:,.0f}
   Average monthly expenses: ${avg_expenses:,.0f}
   Records per product: {total_records // products}
"""
  return summary


def seed_dataset(num_products: int = 10, clear_first: bool = True):
  """Main seeding function for dataset."""
  print("🌱 Starting dataset seeding process...")

  # Create database session
  db = SessionLocal()

  try:
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    if clear_first:
      clear_existing_data(db)

    total_records = generate_mock_dataset(db, num_products)

    # Display summary
    summary = get_data_summary(db)
    print(summary)

    return total_records

  except Exception as e:
    print(f"❌ Error during dataset seeding: {e}")
    db.rollback()
    raise
  finally:
    db.close()


if __name__ == "__main__":
  # Seed with 10 products by default (10 products * 5 years * 12 months = 600 records)
  seed_dataset(num_products=10, clear_first=True)
