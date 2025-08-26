
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
    screenshot_url = (
        "https://api.screenshotone.com/take"
        "?access_key=1Fp_kfqq-P3z6A"
        f"&url={website_url}"
        "&format=jpg"
        "&block_ads=true&block_cookie_banners=true&block_trackers=true"
        "&image_quality=80"
    )
    resp = requests.get(
        screenshot_url,
        timeout=timeout,
        allow_redirects=True,
        headers={"User-Agent": UA, "Accept": "image/*,application/json;q=0.9,*/*;q=0.8"},
    )
    try:
        resp.raise_for_status()
    except requests.HTTPError as e:
        preview = resp.text[:200].replace("\n", " ")
        raise RuntimeError(f"Screenshot API error: {e}; body: {preview!r}")

    ctype = resp.headers.get("Content-Type", "")
    if not ctype.startswith("image/"):
        preview = resp.text[:200].replace("\n", " ")
        raise RuntimeError(f"Expected image/* but got {ctype!r}; body preview: {preview!r}")
    return resp.content

def classify_pil(img: Image.Image) -> int:
    # 1 = defaced, 0 = clean
    img = img.convert("RGB").resize((img_width, img_height))
    arr = keras.preprocessing.image.img_to_array(img)
    arr = tf.expand_dims(arr, 0)
    preds = model.predict(arr, verbose=0)
    score = tf.nn.softmax(preds[-1])
    return int(class_names[int(np.argmax(score))] == "defaced")

def run_defacement_monitor(website_id, website_url, current_user):
    while True:
        db: Session = SessionLocal()
        try:
            site = db.query(Website).filter(Website.id == website_id).first()
            if not site or not site.defacement_enabled:
                break

            website_name = site.name
            owner_email = getattr(site.user, "email", None) if hasattr(site, "user") else None
            if not owner_email:
                print(f"Owner email not configured for alerts (website_id={website_id}).")
                owner_email = None

            print(f"Checking website: {website_url}")
            timestamp = datetime.now()

            try:
                img_bytes = fetch_screenshot_bytes(website_url, timeout=25)
                img = Image.open(BytesIO(img_bytes))
                img.load() 
            except (RuntimeError, UnidentifiedImageError) as e:
                print(f"Error during defacement check (fetch/decode): {e}")
                time.sleep(60)
                continue

            result = classify_pil(img)  # 1 = defaced, 0 = clean

        
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

