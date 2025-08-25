import asyncio, time, httpx
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select
from db import SessionLocal
from models import Website, UptimeCheck  

TIMEOUT = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)
HEADERS = {"User-Agent": "WebShieldAI-Uptime/1.0"}

async def check_site(client: httpx.AsyncClient, url: str) -> tuple[bool,int|None,int|None,str|None]:
    t0 = time.perf_counter()
    try:
        r = await client.request("HEAD", url, follow_redirects=True)
        ok = 200 <= r.status_code < 400
        ms = int((time.perf_counter() - t0) * 1000)
        return ok, r.status_code, ms, None
    except Exception as e:
        return False, None, None, type(e).__name__

async def run_checks_once(websites: Sequence[Website]):
    async with httpx.AsyncClient(timeout=TIMEOUT, headers=HEADERS, verify=True) as client:
        results = await asyncio.gather(*(check_site(client, w.url) for w in websites), return_exceptions=False)

    db: Session = SessionLocal()
    try:
        for w, (ok, status, ms, err) in zip(websites, results):
            db.add(UptimeCheck(
                website_id=w.id, status_up=ok, status_code=status,
                response_ms=ms, error=err
            ))
        db.commit()
    finally:
        db.close()

async def monitor_loop(interval_sec: int = 60):
    while True:
        db = SessionLocal()
        try:
            sites = db.execute(select(Website)).scalars().all()
        finally:
            db.close()

        if sites:
            await run_checks_once(sites)
        await asyncio.sleep(interval_sec)