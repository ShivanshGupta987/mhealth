# insert_targets.py

from app.sql_db import SessionLocal
from app.models import Targets 
from sqlalchemy.exc import IntegrityError
import logging
import uuid # Only needed if you explicitly need to generate UUIDs elsewhere

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def insert_sample_targets():
    """
    Inserts sample data into the Targets table using SQLAlchemy ORM.
    Target_Id is generated automatically by the ORM's default=uuid.uuid4.
    """
    
    db = SessionLocal()
    
    # Sample data matching ALL fields of your Targets table schema.
    targets_data = [
        {
            "Name": "Shivansh Gupta",
            "Phone_No": "9369049853", 
            "City": "Prayagraj",
            "State": "Uttar Pradesh",
            "Zip_Code": "211003",
            "Street": "Puravaldi Kydganj",
            "Address": "House Number/Society Name",
            "Batch": 2024,
            "Department_Name": "Computer Science", 
            "Program": "MTech AI",
            "Semester": 3,
        },
        # {
        #     "Name": "Muni",
        #     "Street": "street1",
        #     "City": "Gandhinagar",
        #     "State": "Gujarat",
        #     "Zip_Code": "xxxxxx",
        #     "Address": "address1",
        #     "Phone_No": "+919390223030",
        #     "Batch": 2024,
        #     "Department_Name": "Computer Science",
        #     "Program": "M.Tech AI",
        #     "Semester": 3,
        # },
        # {
        #     "Name": "Shiva",
        #     "Street": "street2",
        #     "City": "Surat",
        #     "State": "Gujarat",
        #     "Zip_Code": "xxxxx",
        #     "Address": "address2",
        #     "Phone_No": "+919676733610",
        #     "Batch": 2024,
        #     "Department_Name": "Computer Science",
        #     "Program": "MTech AI",
        #     "Semester": 3,
        # }
    ]

    try:
        inserted_count = 0
        for data in targets_data:
            # Check for existing target using the unique Phone_No
            existing_target = db.query(Targets).filter(Targets.Phone_No == data["Phone_No"]).first()
            if existing_target:
                logger.warning(f"Target with phone number {data['Phone_No']} already exists. Skipping.")
                continue

            # SQLAlchemy generates the UUID automatically upon instantiation
            new_target = Targets(**data) 
            db.add(new_target)
            inserted_count += 1
        
        db.commit()
        logger.info(f"Successfully inserted {inserted_count} sample target records.")

    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database Integrity Error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"An unexpected error occurred during insertion: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insert_sample_targets()