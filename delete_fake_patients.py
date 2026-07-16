import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.core.db import SessionLocal, text

def delete_fake():
    db = SessionLocal()
    try:
        res = db.execute(text("SELECT count(*) FROM patients WHERE patient_code ~ '^AKR[0-9]{7}$'"))
        count = res.scalar()
        print(f"Deleting {count} fake patients...")
        db.execute(text("DELETE FROM patients WHERE patient_code ~ '^AKR[0-9]{7}$'"))
        db.commit()
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_fake()
