"""Create the schema and add the sample records once; preserve later CRUD changes."""
import json
from pathlib import Path
from sqlalchemy import func, select
from .database import Base, SessionLocal, engine
from .models import WantedCriminal, HuntLog

def seed():
    Base.metadata.create_all(engine)
    data = json.loads((Path(__file__).resolve().parent.parent / "database" / "seed.json").read_text())
    with SessionLocal.begin() as db:
        # Do not reinsert logs that the user deleted on a previous run.
        if db.scalar(select(func.count()).select_from(WantedCriminal)):
            return
        criminals = {c["id"]: WantedCriminal(**{k:v for k,v in c.items() if k != "id"}) for c in data["criminals"]}
        db.add_all(criminals.values())
        db.flush()
        for log in data["hunts"]:
            db.add(HuntLog(criminal_id=criminals[log["criminal_id"]].id,
                           success=log["success"], notes=log["notes"]))
    print("Database ready: 5 criminals and 10 hunt logs inserted.")

if __name__ == "__main__":
    seed()
