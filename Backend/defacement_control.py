from threading import Thread
from models import Website
from db import SessionLocal
from defacement_loop import run_defacement_monitor

running_monitors = {}

async def toggle_defacement(website_id: int, enable: bool, current_user):
    db = SessionLocal()
    website = db.query(Website).filter(Website.id == website_id).first()
    
    if not website:
        db.close()
        return {"error": "Website not found"}

    website.defacement_enabled = enable
    db.commit()

    if enable:
        if website_id not in running_monitors:
            print("Starting defacement monitor for website:", website_id)
            thread = Thread(target=run_defacement_monitor, args=(website_id, website.url, current_user), daemon=True)
            running_monitors[website_id] = thread
            thread.start()
    else:
        if website_id in running_monitors:
            del running_monitors[website_id]

    db.close()
    return {"status": "success", "enabled": enable}