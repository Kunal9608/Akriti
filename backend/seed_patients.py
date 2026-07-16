import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
import random
from datetime import date, timedelta
from faker import Faker
from backend.app.core.db import SessionLocal
from backend.app.models.patient import Patient, GenderEnum, CollectionTypeEnum, PatientStatusEnum
from backend.app.models.user import User

fake = Faker('en_IN')

def seed_patients(num=1000):
    db = SessionLocal()
    try:
        # Get a user to act as the collector
        collector = db.query(User).first()
        if not collector:
            print("No user found to act as collector. Please create a user first.")
            return

        patients = []
        for i in range(num):
            gender = random.choice(list(GenderEnum))
            total_amount = round(random.uniform(500, 5000), 2)
            amount_paid = total_amount if random.random() > 0.3 else 0.0
            
            p = Patient(
                id=uuid.uuid4(),
                patient_code=f"AKR{random.randint(1000000, 9999999)}",
                name=fake.name(),
                age=random.randint(1, 90),
                gender=gender,
                mobile=f"{random.choice(['6','7','8','9'])}{random.randint(100000000, 999999999)}",
                collected_by=collector.id,
                collection_type=random.choice(list(CollectionTypeEnum)),
                sample_date=date.today() - timedelta(days=random.randint(0, 30)),
                estimated_report_date=date.today() + timedelta(days=random.randint(1, 3)),
                total_amount=total_amount,
                amount_paid=amount_paid,
                status=random.choice(list(PatientStatusEnum))
            )
            patients.append(p)

        # Batch insert for speed
        db.bulk_save_objects(patients)
        db.commit()
        print(f"Successfully seeded {num} patients!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding patients: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    count = 1000
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    seed_patients(count)
