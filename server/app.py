# server/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timezone
import requests
import uuid
import os
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

# Configuration
MOCK_API_BASE = os.environ.get("MOCK_API_BASE", "http://localhost:5000")
EXTERNAL_POST = f"{MOCK_API_BASE}/api/call"
EXTERNAL_GET_TEMPLATE = f"{MOCK_API_BASE}/api/call/{{}}"

app = Flask(__name__)
CORS(app)

# DB setup (SQLite simple file)
engine = create_engine("sqlite:///schedules.db", echo=False, future=True)
Base = declarative_base()

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(String, primary_key=True)  # local uuid
    phone_number = Column(String, nullable=False)
    schedule_time = Column(DateTime, nullable=True)  # UTC
    created_at = Column(DateTime, nullable=False)
    started = Column(Boolean, default=False)
    external_call_id = Column(String, nullable=True)
    last_status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, future=True)

# Scheduler
sched = BackgroundScheduler()
sched.start()

# ---------------------------------------------------------------------
# 🧠 Background simulator for mock call progress
# ---------------------------------------------------------------------
def simulate_call_progress(schedule_id):
    """Simulate call progress after it starts (only for local UI demo)."""
    statuses = ["ringing", "connected", "completed"]
    delay = 3  # seconds between status transitions

    with Session() as s:
        sch = s.get(Schedule, schedule_id)
        if not sch:
            return
        if not sch.external_call_id:
            # nothing to simulate if external call not started
            return
        call_id = sch.external_call_id

    for status in statuses:
        time.sleep(delay)
        with Session() as s:
            sch = s.get(Schedule, schedule_id)
            if not sch:
                return
            sch.last_status = status
            s.add(sch)
            s.commit()
            print(f"[simulate_call_progress] {schedule_id} → {status}")

# ---------------------------------------------------------------------
# Actual call initiation
# ---------------------------------------------------------------------
def initiate_external_call(schedule_id):
    """Job run by APScheduler to actually POST to mock API"""
    with Session() as s:
        sch = s.get(Schedule, schedule_id)
        if sch is None:
            print("Schedule not found", schedule_id)
            return
        if sch.started:
            print("Already started", schedule_id)
            return

        # call external API
        try:
            resp = requests.post(EXTERNAL_POST, json={"phone_number": sch.phone_number}, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            call_obj = data.get("call", {})
            sch.external_call_id = call_obj.get("id")
            sch.started = True
            sch.last_status = call_obj.get("status") or "initiated"
            s.add(sch)
            s.commit()
            print(f"Started external call for schedule {schedule_id} -> {sch.external_call_id}")

            # 🔹 Start simulation thread for mock progression
            threading.Thread(target=simulate_call_progress, args=(schedule_id,), daemon=True).start()

        except Exception as e:
            sch.notes = f"error_initiating: {str(e)}"
            s.add(sch)
            s.commit()
            print("Error calling external API:", e)

# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "call-scheduler-backend"}), 200

@app.route("/schedule", methods=["POST"])
def schedule_call():
    """
    Body: { phone_number: str, schedule_time: iso8601 string optional }
    If schedule_time omitted or in the past, initiate immediately (via external API)
    Returns local schedule object
    """
    payload = request.get_json() or {}
    phone = payload.get("phone_number")
    schedule_time = payload.get("schedule_time")  # expected ISO string in UTC or with timezone

    if not phone or len(phone.strip()) < 10:
        return jsonify({"error": "phone_number is required and must be >=10 chars"}), 400

    now = datetime.now(timezone.utc)
    local_id = str(uuid.uuid4())

    # parse schedule_time if provided
    dt = None
    if schedule_time:
        try:
            dt = datetime.fromisoformat(schedule_time)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
        except Exception as e:
            return jsonify({"error": "Invalid schedule_time. Use ISO format."}), 400

    with Session() as s:
        sch = Schedule(
            id=local_id,
            phone_number=phone,
            schedule_time=dt,
            created_at=now,
            started=False,
            external_call_id=None,
            last_status="scheduled" if dt else "pending"
        )
        s.add(sch)
        s.commit()

    # If no schedule time or schedule_time <= now -> start immediately
    if not dt or dt <= now:
        sched.add_job(
            initiate_external_call,
            args=[local_id],
            id=f"job-{local_id}",
            replace_existing=True,
            next_run_time=now
        )
    else:
        trigger = DateTrigger(run_date=dt)
        sched.add_job(
            initiate_external_call,
            trigger=trigger,
            args=[local_id],
            id=f"job-{local_id}"
        )

    return jsonify({"success": True, "schedule_id": local_id}), 201

@app.route("/schedules", methods=["GET"])
def list_schedules():
    """Return list of schedules."""
    with Session() as s:
        rows = s.query(Schedule).order_by(Schedule.created_at.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "phone_number": r.phone_number,
                "schedule_time": r.schedule_time.isoformat() if r.schedule_time else None,
                "created_at": r.created_at.isoformat(),
                "started": bool(r.started),
                "external_call_id": r.external_call_id,
                "last_status": r.last_status,
                "notes": r.notes
            })
    return jsonify({"schedules": out}), 200

@app.route("/schedules/<schedule_id>/start", methods=["POST"])
def start_now(schedule_id):
    """Force start a scheduled entry now"""
    with Session() as s:
        sch = s.get(Schedule, schedule_id)
        if not sch:
            return jsonify({"error": "not found"}), 404
        sched.add_job(
            initiate_external_call,
            args=[schedule_id],
            id=f"job-{schedule_id}",
            replace_existing=True,
            next_run_time=datetime.now(timezone.utc)
        )
    return jsonify({"success": True}), 200

@app.route("/status/<schedule_id>", methods=["GET"])
def get_status(schedule_id):
    """Return local schedule info and external call status"""
    with Session() as s:
        sch = s.get(Schedule, schedule_id)
        if not sch:
            return jsonify({"error": "not found"}), 404

        result = {
            "id": sch.id,
            "phone_number": sch.phone_number,
            "schedule_time": sch.schedule_time.isoformat() if sch.schedule_time else None,
            "created_at": sch.created_at.isoformat(),
            "started": sch.started,
            "external_call_id": sch.external_call_id,
            "last_status": sch.last_status,
            "notes": sch.notes
        }

        # If we have external_call_id, fetch latest mock status
        if sch.external_call_id:
            try:
                resp = requests.get(EXTERNAL_GET_TEMPLATE.format(sch.external_call_id), timeout=4)
                if resp.status_code == 200:
                    data = resp.json().get("call", {})
                    result["external_call"] = data
                    sch.last_status = data.get("status")
                    s.add(sch)
                    s.commit()
                else:
                    result["external_error"] = resp.text
            except Exception as e:
                result["external_error"] = str(e)

    return jsonify(result), 200

# ---------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------
if __name__ == "__main__":
    print("✅ Call Scheduler backend starting on http://0.0.0.0:8000")
    print("→ Talking to mock API at", MOCK_API_BASE)
    app.run(host="0.0.0.0", port=8000, debug=True)
