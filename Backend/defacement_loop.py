
# import os
# import time
# import requests
# from io import BytesIO
# from PIL import Image
# from sqlalchemy.orm import Session, joinedload
# from db import SessionLocal
# from models import DefacementLog, Website
# from datetime import datetime, timedelta
# import numpy as np
# import tensorflow as tf
# from tensorflow import keras

# from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
# from sqlalchemy.orm import Session
# from datetime import datetime
# from typing import Optional

# import models, schemas
# from db import get_db
# from auth import get_current_user
# from notifications import send_email_now, build_threat_email_html

# img_height = 250
# img_width = 250
# model = keras.models.load_model("ml/defacement_model.h5", compile = False)

# class_names = ["clean", "defaced"]


# def get_site_primitives(db: Session, website_id: int, current_user):
#     site = (
#         db.query(models.Website)
#         .filter(
#             models.Website.id == website_id,
#             models.Website.user_id == current_user.id,
#         )
#         .first()
#     )
#     if not site:
#         raise HTTPException(status_code=404, detail="Website not found")

#     owner_email = getattr(current_user, "email", None)
#     if not owner_email:
#         raise HTTPException(status_code=400, detail="Owner email not configured for alerts")

#     # return primitives only (no ORM objects outside)
#     return site.name, site.url, owner_email
# def check(images_path):
#     img = keras.preprocessing.image.load_img(
#         images_path, target_size=(img_height, img_width)
#     )
#     img_array = keras.preprocessing.image.img_to_array(img)
#     img_array = tf.expand_dims(img_array, 0)  # Create a batch
#     predictions = model.predict(img_array)
#     score = tf.nn.softmax(predictions[-1])
#     if format(class_names[np.argmax(score)]) == "defaced":
#         return 1
#     else:
#         return 0

# def run_defacement_monitor(website_id, website_url , current_user):
#     while True:
#         db = SessionLocal()
#         site = db.query(Website).filter(Website.id == website_id).first()
#         if not site or not site.defacement_enabled:
#             db.close()
#             break 
#         try:
#             print(f"Checking website: {website_url}")
#             timestamp = datetime.now()
#             screenshot_url = f"https://api.screenshotone.com/take?access_key=LZQpD08KX7gH5g&url={website_url}&format=jpg&block_ads=true&block_cookie_banners=true&block_trackers=true&response_type=by_format&image_quality=80"

#             response = requests.get(screenshot_url)
#             image = Image.open(BytesIO(response.content))
#             image_path = f"screenshot_{website_id}.jpg"
#             image.save(image_path)

#             result = check(image_path)

#             db: Session = SessionLocal()

#             log = DefacementLog(
#                 website_id=website_id,
#                 prediction="defaced" if result else "clean",
#                 timestamp=timestamp
#             )
#             db.add(log)

#             cutoff_time = timestamp - timedelta(minutes=60)
#             db.query(DefacementLog).filter(
#                 DefacementLog.website_id == website_id,
#                 DefacementLog.timestamp < cutoff_time
#             ).delete()

#             db.commit()
#             db.close()

#             ts = datetime.utcnow()
#             print(f"Logged defacement check: {result} at {timestamp}")
#             website_name, website_url, owner_email = get_site_primitives(db, website_id, current_user)
#             if (result == 1):
#                 subject = f"[Web Shield AI] DEFACEMENT detected on {website_name}"
#                 html = build_threat_email_html(
#                     website_name=website_name,
#                     website_url=website_url,
#                     log_type="defacement",
#                     occurred_at=ts,
#                     # prediction=payload.prediction,
#                 )
#                 # Synchronous send (no BackgroundTasks)
#                 try:
#                     send_email_now(owner_email, subject, html)
#                 except Exception as e:
#                     # choose: swallow, log, or raise
#                     print("Email send error:", e)

#             os.remove(image_path)
#         except Exception as e:
#             print(f"Error during defacement check: {e}")

#         time.sleep(60)

import os
import time
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session
from db import SessionLocal
from models import DefacementLog, Website
from datetime import datetime, timedelta
import numpy as np
import tensorflow as tf
from tensorflow import keras

img_height = 250
img_width = 250
model = keras.models.load_model("ml/defacement_model.h5", compile=False)
class_names = ["clean", "defaced"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def fetch_screenshot_bytes(website_url: str, *, timeout=20) -> bytes:
    # NOTE: verify your ScreenshotOne params; non-image responses will be rejected below
    screenshot_url = (
        "https://api.screenshotone.com/take"
        "?access_key=1Fp_kfqq-P3z6A"
        f"&url={website_url}"
        "&format=jpg"
        "&block_ads=true&block_cookie_banners=true&block_trackers=true"
        # Response should be an image for Pillow. If this param causes JSON, remove it.
        # "&response_type=by_format"
        "&image_quality=80"
    )
    resp = requests.get(
        screenshot_url,
        timeout=timeout,
        allow_redirects=True,
        headers={"User-Agent": UA, "Accept": "image/*,application/json;q=0.9,*/*;q=0.8"},
    )
    # Raise for 4xx/5xx so callers can handle/log
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        # Include a small preview of the body for debugging
        preview = resp.text[:200].replace("\n", " ")
        raise RuntimeError(f"Screenshot API error: {e}; body: {preview!r}")

    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("image/"):
        preview = resp.text[:200].replace("\n", " ")
        raise RuntimeError(f"Expected image/* but got {ctype!r}; body preview: {preview!r}")
    return resp.content

def classify_pil(img: Image.Image) -> int:
    # 0=clean, 1=defaced
    img = img.convert("RGB").resize((img_width, img_height))
    arr = keras.preprocessing.image.img_to_array(img)
    arr = tf.expand_dims(arr, 0)
    preds = model.predict(arr, verbose=0)
    score = tf.nn.softmax(preds[-1])
    return int(class_names[int(np.argmax(score))] == "defaced")

def run_defacement_monitor(website_id, website_url, current_user):
    while True:
        # Open a session for this iteration
        db: Session = SessionLocal()
        try:
            site = db.query(Website).filter(Website.id == website_id).first()
            if not site or not site.defacement_enabled:
                break

            # Get primitives while session is open
            website_name = site.name
            owner_email = getattr(site.user, "email", None) if hasattr(site, "user") else None
            if not owner_email:
                # Or fetch from current_user if you trust it: getattr(current_user, "email", None)
                print(f"Owner email not configured for alerts (website_id={website_id}).")
                owner_email = None

            print(f"Checking website: {website_url}")
            timestamp = datetime.now()

            try:
                img_bytes = fetch_screenshot_bytes(website_url, timeout=25)
                img = Image.open(BytesIO(img_bytes))
                img.load()  # force decode now to catch errors early
            except (RuntimeError, UnidentifiedImageError) as e:
                print(f"Error during defacement check (fetch/decode): {e}")
                # Log a 'clean' or 'error' state if you want; then wait and retry
                time.sleep(60)
                continue

            result = classify_pil(img)  # 1 = defaced, 0 = clean

            # Log to DB
            log = DefacementLog(
                website_id=website_id,
                prediction="defaced" if result else "clean",
                timestamp=timestamp
            )
            db.add(log)

            cutoff_time = timestamp - timedelta(minutes=60)
            db.query(DefacementLog).filter(
                DefacementLog.website_id == website_id,
                DefacementLog.timestamp < cutoff_time
            ).delete()

            db.commit()
            print(f"Logged defacement check: {result} at {timestamp}")

            # Email after commit (optional)
            if result == 1 and owner_email:
                try:
                    from notifications import send_email_now, build_threat_email_html
                    html = build_threat_email_html(
                        website_name=website_name,
                        website_url=website_url,
                        log_type="defacement",
                        occurred_at=datetime.utcnow(),
                    )
                    send_email_now(owner_email, f"[Web Shield AI] DEFACEMENT detected on {website_name}", html)
                except Exception as e:
                    print("Email send error:", e)

        except Exception as e:
            print(f"Error during defacement check (outer): {e}")
        finally:
            db.close()

        time.sleep(60)

