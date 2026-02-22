"""
Reset pending calls to allow new call attempts
Run this when you want to clear stuck "Awaiting Schedule" calls
"""
from app.sql_db import SessionLocal
from app.models import Calls
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def reset_pending_calls():
    db = SessionLocal()
    try:
        # Find all pending calls
        pending_calls = db.query(Calls).filter(
            Calls.Status.in_(['Awaiting Schedule', 'Message Not Conveyed'])
        ).all()
        
        print(f"Found {len(pending_calls)} pending/failed calls")
        
        for call in pending_calls:
            print(f"  - Call ID: {call.Call_Id}, Target: {call.Target_Id}, Status: {call.Status}")
            call.Status = 'Message Not Conveyed'
            call.End_Time = datetime.now(IST)
        
        db.commit()
        print(f"\n✅ Reset {len(pending_calls)} calls. They can now be retried.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_pending_calls()
