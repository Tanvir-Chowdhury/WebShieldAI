from fastapi import FastAPI, Depends, HTTPException, status, Query, BackgroundTasks
from db import create_table, get_db
from sqlalchemy.orm import Session, joinedload
import models, schemas, services
from sqlalchemy import Integer, String, func, case
from defacement_control import toggle_defacement
from fastapi import Request
from models import SQLLog
from ml_model import predict_query
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from auth import get_current_user
import requests
from typing import List, Union, Optional, Dict
from uptime import monitor_loop
import asyncio
from datetime import datetime, timedelta, timezone
from notifications import send_email_now, build_threat_email_html
import models, schemas
from urllib.parse import urlparse
from pydantic import BaseModel

app = FastAPI(title="WebShieldAI API")

create_table()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key="9f2b3a6e5c7c4965b5c3d11ecac7d6f1bd8446e23c4db487915b6a04e7db47bc")

# 9f2b3a6e5c7c4965b5c3d11ecac7d6f1bd8446e23c4db487915b6a04e7db47bc

def get_site_primitives(db: Session, website_id: int, user_id: int):
    site = (
        db.query(models.Website)
        .filter(
            models.Website.id == website_id,
            models.Website.user_id == user_id,
        )
        .first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    if not site:
        raise HTTPException(404, "Website not found")
    if not site.user or not site.user.email:
        raise HTTPException(400, "Owner email not configured for alerts")
    # Return only primitives (no ORM usage later)
    return site.name, site.url, site.user.email


@app.post("/users/", response_model=schemas.GetUser)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return services.create_user(user, db)
  
@app.post("/login")
async def login(user: schemas.UserLogin, request: Request, db: Session = Depends(get_db)):
    db_user = services.authenticate_user(user.email, user.password, db)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    request.session["user_id"] = db_user.id
    request.session["user_email"] = db_user.email
    return {"message": "Login successful", "user": {"email": db_user.email, "name": db_user.name, "plan": db_user.plan}}


@app.get("/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.query(models.User).get(user_id)
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "plan": user.plan
    }


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out successfully"}


# @app.post("/websites/", response_model=schemas.GetWebsite)
# async def create_website(website: schemas.WebsiteCreate, db: Session = Depends(get_db)):
#     return services.create_website(website, db)
  
@app.post("/websites/", response_model=schemas.GetWebsite)
async def add_website(website: schemas.WebsiteCreate, db: Session = Depends(get_db)):
    return services.create_website(website, db)

@app.get("/websites/", response_model=list[schemas.GetWebsite])
def list_user_websites(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Website).filter(models.Website.user_id == current_user.id).all()

@app.get("/websites/me")
def list_user_websites(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Website).filter(models.Website.user_id == current_user.id).all()

@app.get("/websites/{website_id}", response_model=schemas.GetWebsite)
def get_website(website_id: int, db: Session = Depends(get_db)):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")
    return website

@app.delete("/websites/{website_id}", status_code=204)
def delete_website(website_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    website = db.query(models.Website).filter_by(id=website_id, user_id=current_user.id).first()

    if not website:
        raise HTTPException(status_code=404, detail="Website not found or access denied")

    db.delete(website)
    db.commit()
    return {"detail": "Website deleted successfully"}

def since_window(days: int):
    return datetime.now(timezone.utc) - timedelta(days=days)

@app.get("/websites/{website_id}/uptime")
def site_uptime_metrics(website_id: int, days: int = Query(7, ge=1, le=90),
                        db: Session = Depends(get_db),
                        user = Depends(get_current_user)):
    # ensure ownership
    site = db.query(models.Website).filter(models.Website.id==website_id,
                                    models.Website.user_id==user.id).first()
    if not site:
        return {"uptime_pct": 0, "checks": 0}

    start = since_window(days)
    q = (db.query(
            func.count().label("checks"),
            func.sum(case((models.UptimeCheck.status_up==True, 1), else_=0)).label("up_checks"),
            func.avg(models.UptimeCheck.response_ms).label("avg_ms"))
         .filter(models.UptimeCheck.website_id==website_id,
                 models.UptimeCheck.checked_at >= start))
    row = q.one()
    checks = row.checks or 0
    up = row.up_checks or 0
    avg_ms = int(row.avg_ms) if row.avg_ms is not None else None

    # p50/p95 (simple approach)
    latencies = (db.query(models.UptimeCheck.response_ms)
                   .filter(models.UptimeCheck.website_id==website_id,
                           models.UptimeCheck.checked_at >= start,
                           models.UptimeCheck.response_ms.isnot(None))
                   .order_by(models.UptimeCheck.response_ms)
                   .all())
    l = [r[0] for r in latencies]
    p50 = l[len(l)//2] if l else None
    p95 = l[int(len(l)*0.95)] if l else None

    uptime_pct = round((up/checks)*100, 2) if checks else 0.0
    return {"uptime_pct": uptime_pct, "checks": checks, "avg_ms": avg_ms, "p50_ms": p50, "p95_ms": p95}

@app.get("/summary/uptime")
def global_uptime_summary(days: int = Query(7, ge=1, le=90),
                          db: Session = Depends(get_db),
                          user = Depends(get_current_user)):
    start = since_window(days)
    # only user's websites
    site_ids = [w.id for w in db.query(models.Website.id).filter(models.Website.user_id==user.id).all()]
    if not site_ids:
        return {"uptime_pct": 0, "avg_ms": None}

    q = (db.query(
            func.count().label("checks"),
            func.sum(case((models.UptimeCheck.status_up==True, 1), else_=0)).label("up_checks"),
            func.avg(models.UptimeCheck.response_ms).label("avg_ms"))
         .filter(models.UptimeCheck.website_id.in_(site_ids),
                 models.UptimeCheck.checked_at >= start))
    row = q.one()
    checks = row.checks or 0
    up = row.up_checks or 0
    uptime_pct = round((up/checks)*100, 2) if checks else 0.0
    avg_ms = int(row.avg_ms) if row.avg_ms is not None else None
    return {"uptime_pct": uptime_pct, "avg_ms": avg_ms}



@app.post("/websites/{website_id}/toggle-defacement")
async def toggle_defacement_route(website_id: int, enable: bool, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return await toggle_defacement(website_id, enable, current_user)
  
@app.post("/websites/{website_id}/update-protection")
def update_protection(
    website_id: int,
    payload: schemas.ProtectionUpdate,
    db: Session = Depends(get_db)
):
    website = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found")

    if payload.protection_type == "xss":
        website.xss_enabled = payload.enabled
    elif payload.protection_type == "sqli":
        website.sqli_enabled = payload.enabled
    elif payload.protection_type == "dom":
        website.dom_enabled = payload.enabled
    else:
        raise HTTPException(status_code=400, detail="Invalid protection type")

    db.commit()
    return {"success": True}

def website_id_filter(col, website_id: int):
    if isinstance(col.type, Integer):
        return col == website_id
    if isinstance(col.type, String):
        return col == str(website_id)
    return col == website_id
  
@app.get("/websites/{website_id}/attack-logs", response_model=List[schemas.AttackLogOut])
def get_attack_logs(
    website_id: int,
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    site = (
        db.query(models.Website)
        .filter(
            models.Website.id == website_id,
            models.Website.user_id == current_user.id,  
        )
        .first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")

    xss_rows = (
        db.query(models.XSSLog)
        .filter(website_id_filter(models.XSSLog.website_id, website_id))
        .order_by(models.XSSLog.created_at.desc())
        .limit(limit)
        .all()
    )

    deface_rows = (
        db.query(models.DefacementLog)
        .filter(website_id_filter(models.DefacementLog.website_id, website_id))
        .order_by(models.DefacementLog.timestamp.desc())
        .limit(limit)
        .all()
    )

    dom_rows = (
        db.query(models.DomManipulationLog)
        .filter(website_id_filter(models.DomManipulationLog.website_id, website_id))
        .order_by(models.DomManipulationLog.created_at.desc())
        .limit(limit)
        .all()
    )

    sql_rows = (
        db.query(SQLLog)
        .filter(website_id_filter(SQLLog.website_id, website_id))
        .order_by(SQLLog.created_at.desc())
        .limit(limit)
        .all()
    )

    out: List[schemas.AttackLogOut] = []

    for r in xss_rows:
        out.append(
            schemas.AttackLogOut(
                id=r.id,
                type="xss",
                website_id=r.website_id,
                occurred_at=r.created_at,
                ip_address=getattr(r, "ip_address", None),
            )
        )

    for r in deface_rows:
        out.append(
            schemas.AttackLogOut(
                id=r.id,
                type="defacement",
                website_id=r.website_id,
                occurred_at=r.timestamp,
                prediction=getattr(r, "prediction", None),
            )
        )

    for r in dom_rows:
        out.append(
            schemas.AttackLogOut(
                id=r.id,
                type="dom",
                website_id=r.website_id,
                occurred_at=r.created_at,
                ip_address=getattr(r, "ip_address", None),
            )
        )

    for r in sql_rows:
        out.append(
            schemas.AttackLogOut(
                id=r.id,
                type="sql_injection",
                website_id=r.website_id,
                occurred_at=r.created_at,
                query=getattr(r, "query", None),
                prediction=getattr(r, "prediction", None),
                score=getattr(r, "score", None),
            )
        )

    out.sort(key=lambda x: x.occurred_at, reverse=True)
    return out[:limit]

@app.get("/me/attack-logs/total-count", response_model=Dict[str, int])
def get_total_logs_for_user(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):

    has_site = (
        db.query(models.Website.id)
        .filter(models.Website.user_id == current_user.id)
        .first()
    )
    if not has_site:
        return {"total": 0}

    xss_count = (
        db.query(func.count(models.XSSLog.id))
        .join(models.Website, models.Website.id == models.XSSLog.website_id)
        .filter(models.Website.user_id == current_user.id)
        .scalar()
        or 0
    )

    dom_count = (
        db.query(func.count(models.DomManipulationLog.id))
        .join(models.Website, models.Website.id == models.DomManipulationLog.website_id)
        .filter(models.Website.user_id == current_user.id)
        .scalar()
        or 0
    )

    sql_count = (
        db.query(func.count(models.SQLLog.id))
        .join(models.Website, models.Website.id == models.SQLLog.website_id)
        .filter(models.Website.user_id == current_user.id)
        .scalar()
        or 0
    )

    total = xss_count + dom_count + sql_count
    return {"total": total}


@app.get("/websites/{website_id}/blocked-count")
def get_blocked_count_for_website(
    website_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
) -> Dict[str, int]:
    

    site = (
        db.query(models.Website)
        .filter(
            models.Website.id == website_id,
            models.Website.user_id == current_user.id,   
        )
        .first()
    )
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")

    xss_count = (
        db.query(func.count(models.XSSLog.id))
        .filter(models.XSSLog.website_id == website_id)
        .scalar()
        or 0
    )

    dom_count = (
        db.query(func.count(models.DomManipulationLog.id))
        .filter(models.DomManipulationLog.website_id == website_id)
        .scalar()
        or 0
    )

    sql_count = (
        db.query(func.count(models.SQLLog.id))
        .filter(models.SQLLog.website_id == website_id)
        .scalar()
        or 0
    )


    total = xss_count + dom_count + sql_count

    return {
        "xss": xss_count,
        "dom": dom_count,
        "sql_injection": sql_count,
        "total": total,
    }

@app.on_event("startup")
async def _start_monitor():
    # fire-and-forget background loop
    asyncio.create_task(monitor_loop(interval_sec=60))


@app.post("/predict-sqli/")
async def predict_sql_query(input: schemas.SQLQuery, db: Session = Depends(get_db)):
    return services.process_sql_query(input, db)


@app.post("/collect-sqli")
async def collect_sqli(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    website_id = data.get("website_id")
    query = data.get("query")

    prediction, confidence = predict_query(query)

    log = SQLLog(
        website_id=website_id,
        query=query,
        prediction=prediction,
        score=confidence
    )
    db.add(log)
    db.commit()
    # website_name, website_url, owner_email = get_site_primitives(db, website_id, current_user.id)

    site = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not site:
        raise HTTPException(404, detail="Website not found")
    
    user = db.query(models.User).filter(models.User.id == site.user_id).first()
    if not user or not user.email:
        raise HTTPException(404, detail="Owner email not found")
    
    website_name = site.name
    website_url = site.url
    owner_email = user.email

    ts = datetime.utcnow()
    subject = f"[Web Shield AI] SQL injection attempt on {website_name}"
    html = build_threat_email_html(
        website_name=website_name, website_url=website_url,
        log_type="sql_injection", occurred_at=ts,
        query=query, prediction=prediction, score=confidence
    )
    try:
        send_email_now(owner_email, subject, html)
    except Exception as e:
        print("Email send error:", e)
    

    return {"status": "ok", "prediction": prediction, "confidence": confidence}
  


@app.get("/cdn/webshield-sql-agent.js")
def serve_agent(request: Request):
    website_id = request.query_params.get("wid", "0")

    js_code = f"""
(function () {{
  const WEBSITE_ID = {website_id};
  const API_URL = "http://127.0.0.1:8000/collect-sqli";

  function sendSQLQuery(value, callback) {{
    fetch(API_URL, {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        website_id: WEBSITE_ID,
        query: value
      }}),
    }})
    .then(res => res.json())
    .then(data => {{
      console.log("Sending SQL query:", value);
      console.log("Prediction:", data);
      if (data.prediction === "malicious") {{
        alert("SQL Injection attempt detected!");
      }}
      callback(null, data);  
    }})
    .catch(err => {{
      console.error("Error:", err);
      callback(err, null); 
    }});
  }}

  document.addEventListener("DOMContentLoaded", function () {{
    const inputs = document.getElementsByTagName("input");
    const submitButton = document.querySelector("button[type='submit'], input[type='submit']");

    if (submitButton) {{
      submitButton.addEventListener("click", function (e) {{
        e.preventDefault(); 

        const valuesToCheck = [];
        for (let i = 0; i < inputs.length; i++) {{
          const val = inputs[i].value.trim();
          
          if (val.endsWith("@gmail.com") || val.endsWith("@yahoo.com") || val.endsWith("@hotmail.com")) {{
            console.warn("Skipping email input:", val);
            continue;  
          }}
          if (val !== "") {{
            valuesToCheck.push(val);
          }}
        }}

        if (valuesToCheck.length === 0) {{
          e.target.form.submit();
          return;
        }}

        let completed = 0;
        let maliciousDetected = false;

        function checkAndSubmit() {{
          completed++;
          if (completed === valuesToCheck.length) {{
            if (!maliciousDetected) {{
              console.log("All inputs are clean. Submitting form...");
              e.target.form.submit();  
            }} else {{
              console.warn("Malicious input detected. Form blocked.");
            }}
          }}
        }}

        for (let i = 0; i < valuesToCheck.length; i++) {{
          sendSQLQuery(valuesToCheck[i], function(err, data) {{
            if (err || (data.prediction && data.prediction === "malicious")) {{
              maliciousDetected = true;
            }}
            checkAndSubmit();
          }});
        }}
      }});
    }}
  }});

  const queryString = window.location.search;
  DqueryString = decodeURIComponent(queryString.substring(1));
  if (queryString) {{
    sendSQLQuery(DqueryString, function(err, data) {{
      if (!err && data.prediction === "malicious") {{
          alert("Malicious query detected in URL. Redirecting to home page.");
          window.location.href = "/";
        }}
    }});
  }}

  console.log("WebShield SQLI Agent active for Website ID:", WEBSITE_ID);
}})();
"""

    return Response(content=js_code, media_type="application/javascript")

@app.get("/check-cdn-code")
async def check_cdn_code(
    wid: int,
    expected_script: str = Query(..., description="Script tag to verify"),
    db: Session = Depends(get_db)
):
    try:
        website = db.query(models.Website).filter(models.Website.id == wid).first()
        if not website:
            return {"success": False, "error": "Website not found"}

        url = website.url
        response = requests.get(url, timeout=5)
        html_content = response.text

        if expected_script in html_content:
            return {"success": True}
        else:
            return {"success": False, "error": "CDN script not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def _hostname(u: str | None) -> str | None:
    if not u: return None
    try: return urlparse(u).hostname
    except: return None

def _canon(h: str | None) -> str | None:
    if not h: return None
    h = h.lower().strip().rstrip(".")
    if h.startswith("www."): h = h[4:]
    return h

def hosts_match(site_url: str, observed: str | None) -> bool:
    s = _canon(_hostname(site_url))
    o = _canon(observed)
    if not s or not o: return False
    return o == s or o.endswith("." + s)

def observed_host_from_request(request: Request) -> str | None:
    ref = request.headers.get("referer") or request.headers.get("referrer")
    return _hostname(ref)

def get_client_ip(request: Request) -> str:
    return (request.headers.get("X-Envoy-External-Address")
            or request.headers.get("X-Forwarded-For")
            or request.headers.get("X-Real-IP")
            or request.client.host)

NOOP_JS = '/* WebShield XSS Agent: disabled or host mismatch. */\n'

@app.get("/cdn/webshield-xss-agent.js")
def serve_xss_agent(request: Request, db: Session = Depends(get_db)):
    wid = int(request.query_params.get("wid") or 0)
    debug = request.query_params.get("debug") == "1"

    site = db.query(models.Website).filter(models.Website.id == wid).first()
    if not site or not site.xss_enabled:
        return Response('/* XSS disabled or site missing */', media_type="application/javascript")

    api_base = str(request.base_url).rstrip("/")  

    js = f"""
(function() {{
  const DEBUG = {str(debug).lower()};
  const WID = {wid};
  const API_BASE = {api_base!r};

  if (DEBUG) console.log("[WebShield] XSS agent starting", {{ WID, API_BASE }});

  const suspiciousPatterns = [
    /<script.*?>.*?<\\/script>/i,
    /%3C\\s*script.*?%3E.*?%3C\\s*\\/\\s*script\\s*%3E/i,
    /javascript:/i,
    /onerror\\s*=\\s*/i,
    /onload\\s*=\\s*/i,
    /<.*?on\\w+\\s*=\\s*['"].*?['"].*?>/i,
    /document\\.cookie/i,
    /<iframe/i,
    /<img.*?src=.*?>/i
  ];
  function isMalicious(v) {{ return suspiciousPatterns.some(re => re.test(v)); }}

  function reportXSS(vector, payload) {{
    fetch(API_BASE + "/api/xss-report", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        website_id: WID,
        vector, payload,
        page_url: window.location.href,
        occurred_at: new Date().toISOString()
      }}),
      mode: "cors",
      credentials: "omit",
      keepalive: true
    }}).then(() => {{
      if (DEBUG) console.log("[WebShield] XSS report sent");
    }}).catch(e => {{
      console.error("[WebShield] XSS report failed", e);
    }});
  }}

  function handleDetection(vector, value) {{
    reportXSS(vector, value);
    if (!DEBUG) {{
      alert("Script Injection Detected! Redirecting to home…");
    
      setTimeout(() => window.location.replace("/"), 100);
    }} else {{
      console.warn("[WebShield] (debug) Detected XSS, no redirect.");
    }}
  }}

  function checkInputs() {{
    const inputs = document.querySelectorAll("input[type='text'], textarea");
    for (const input of inputs) {{
      const v = (input.value || "").trim();
      if (v && isMalicious(v)) {{
        handleDetection("input", v);
        return true;
      }}
    }}
    return false;
  }}

  function checkURLParams() {{
    const params = new URLSearchParams(window.location.search);
    for (const [k, raw] of params.entries()) {{
      let v = raw; try {{ v = decodeURIComponent(raw); }} catch (_ ) {{}}
      if (v && isMalicious(v)) {{
        handleDetection("url", v);
        return true;
      }}
    }}
    return false;
  }}

  document.addEventListener("DOMContentLoaded", function () {{
    if (checkInputs()) return;
    if (checkURLParams()) return;

    // Intercept form submit so we can stop it on detection
    for (const form of document.querySelectorAll("form")) {{
      form.addEventListener("submit", function (e) {{
        if (checkInputs()) e.preventDefault();
      }});
    }}
  }});
}})();
"""
    return Response(js, media_type="application/javascript", headers={"Cache-Control": "no-store"})



class XSSPayload(BaseModel):
    website_id: int
    payload: str


@app.post("/api/xss-report", response_model=None)
async def xss_report(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = await request.json()
    website_id = int(data.get("website_id") or 0)
    if not website_id:
        raise HTTPException(400, "website_id missing")

    site = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not site or not site.xss_enabled:
        raise HTTPException(403, "XSS disabled or site missing")

    ip = (request.headers.get("X-Envoy-External-Address")
          or request.headers.get("X-Forwarded-For")
          or request.headers.get("X-Real-IP")
          or request.client.host)

    db.add(models.XSSLog(website_id=website_id, ip_address=ip))
    db.commit()

    user = db.query(models.User).filter(models.User.id == site.user_id).first()
    if user and user.email:
        subject = f"[WebShield AI] XSS attempt on {site.name}"
        html = build_threat_email_html(
            website_name=site.name, website_url=site.url,
            log_type="xss", occurred_at=datetime.utcnow(), ip_address=ip
        )
        background_tasks.add_task(send_email_now, user.email, subject, html)

    return Response(status_code=204)



@app.get("/cdn/dom-defacement-agent.js")
def serve_dom_defacement_agent(request: Request, db: Session = Depends(get_db)):
    wid = int(request.query_params.get("wid") or 0)
    debug = request.query_params.get("debug") == "1"

    site = db.query(models.Website).filter(models.Website.id == wid).first()
    if not site or not site.dom_enabled:
        return Response('/* DOM agent disabled or site missing */', media_type="application/javascript")

    api_base = str(request.base_url).rstrip("/")  # -> http://127.0.0.1:8000

    js_code = f"""
(function () {{
  const DEBUG = {str(debug).lower()};
  const WID = {wid};
  const API_BASE = {api_base!r};

  if (DEBUG) console.log("[WebShield] DOM agent starting", {{ WID, API_BASE }});

  // Config
  const ALLOWED_TAGS = ["DIV","SPAN","P","A","INPUT","TEXTAREA","BUTTON","UL","OL","LI","IMG","SECTION","NAV","HEADER","FOOTER","MAIN"];
  const SUSPICIOUS_TAGS = ["SCRIPT","IFRAME","EMBED","OBJECT","LINK","STYLE"];

  function isElement(node) {{ return node && node.nodeType === 1; }}
  function isSuspiciousNode(node) {{
    if (!isElement(node)) return false;
    const tag = node.tagName?.toUpperCase();
    return !!tag && SUSPICIOUS_TAGS.includes(tag);
  }}
  function isRemovalOfNonAllowed(node) {{
    if (!isElement(node)) return false;
    const tag = node.tagName?.toUpperCase();
    return !!tag && !ALLOWED_TAGS.includes(tag);
  }}

  function reportDomTamper(kind, tag, snippet) {{
    fetch(API_BASE + "/api/dom-report", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        website_id: WID,
        kind,          
        tag,          
        snippet,       
        page_url: window.location.href,
        occurred_at: new Date().toISOString()
      }}),
      mode: "cors",
      credentials: "omit",
      keepalive: true
    }})
    .then(() => DEBUG && console.log("[WebShield] DOM report sent"))
    .catch(err => console.error("[WebShield] DOM report failed:", err));
  }}

  function handleDetection(kind, tag, snippet) {{
    reportDomTamper(kind, tag, snippet);
    if (!DEBUG) {{
      alert("Suspicious DOM tampering detected! Redirecting to home…");
      setTimeout(() => window.location.replace("/"), 100);
    }} else {{
      console.warn("[WebShield] (debug) DOM tamper detected, no redirect.");
    }}
  }}

  function handleMutation(mutation) {{
    if (mutation.type !== "childList") return;

    // Added nodes: suspicious?
    for (const node of mutation.addedNodes) {{
      if (isSuspiciousNode(node)) {{
        const tag = node.tagName?.toUpperCase() || "";
        const snippet = isElement(node) ? (node.outerHTML || "").slice(0, 200) : "";
        handleDetection("added-suspicious", tag, snippet);
        return true;
      }}
    }}

    // Removed nodes: non-allowed?
    for (const node of mutation.removedNodes) {{
      if (isRemovalOfNonAllowed(node)) {{
        const tag = node.tagName?.toUpperCase() || "";
        handleDetection("removed-nonallowed", tag, "");
        return true;
      }}
    }}
    return false;
  }}

  window.addEventListener("load", function () {{
    try {{
      const observer = new MutationObserver(function (mutations) {{
        for (const m of mutations) {{
          if (handleMutation(m)) break;
        }}
      }});
      observer.observe(document.body, {{ childList: true, subtree: true }});
      console.log("WebShield DOM Agent activated");
    }} catch (e) {{
      console.error("[WebShield] DOM observer error:", e);
    }}
  }});
}})();
"""
    return Response(content=js_code, media_type="application/javascript", headers={"Cache-Control": "no-store"})


@app.post("/api/dom-report", response_model=None)
async def dom_report(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    data = await request.json()
    website_id = int(data.get("website_id", 0) or 0)
    if not website_id:
        raise HTTPException(400, "website_id missing")

    # Optional extras if you ever want them:
    # kind   = data.get("kind")
    # tag    = data.get("tag")
    # snippet= data.get("snippet")
    # page_url = data.get("page_url")

    # Lookup website & feature flag
    site = db.query(models.Website).filter(models.Website.id == website_id).first()
    if not site or not site.dom_enabled:
        raise HTTPException(403, "DOM protection disabled or site missing")

    ip = get_client_ip(request)

    new_log = models.DomManipulationLog(
        website_id=website_id,
        ip_address=ip
    )
    db.add(new_log)
    db.commit()

    user = db.query(models.User).filter(models.User.id == site.user_id).first()
    if user and user.email:
        subject = f"[WebShield AI] DOM tampering on {site.name}"
        html = build_threat_email_html(
            website_name=site.name,
            website_url=site.url,
            log_type="dom",
            occurred_at=datetime.utcnow(),
            ip_address=ip
        )
        background_tasks.add_task(send_email_now, user.email, subject, html)

    return Response(status_code=204)



