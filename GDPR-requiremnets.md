| GDPR Right                     | What it means in your system      |
| ------------------------------ | --------------------------------- |
| Lawful processing              | Only store what’s needed          |
| Data minimization              | Don’t log raw PII unless required |
| Right to access                | Retrieve all data for a GUID      |
| Right to rectification         | Update user data                  |
| Right to erasure (“forget me”) | Delete or anonymize GUID data     |
| Data portability               | Export GUID data                  |
| Purpose limitation             | Separate AI logs vs business data |
| Retention limits               | TTL + lifecycle policies          |
| Security                       | Encryption, access control, audit |

Incoming API (Sync)
  └─ Validates GUID & consent
  └─ Logs request in GDPR queue (async)
       ↓
Async Processor
  ├─ Exports user data (Right to Access)
  ├─ Deletes user data (Right to Erasure)
  └─ Generates notification file (CSV/JSON) for caller
       ↓
Audit Log updated

Key points:

API responds immediately: “Request accepted for processing”

Actual processing happens asynchronously

Output files for audit or user download

**GDPR Request Queue (Mongo collection):**
{
  "_id": ObjectId(),
  "guid": "c2a4d2c7-4e8e-4a3c-b9e9-xxxxx",
  "request_type": "EXPORT" | "DELETE",
  "status": "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED",
  "requested_at": "...",
  "completed_at": null,
  "file_path": null
}

**SYNC API (FastAPI Example)**
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from pymongo import MongoClient
import os

client = MongoClient(os.environ["COSMOS_MONGO_URI"])
db = client["chatbot"]
gdpr_requests = db["gdpr_requests"]

app = FastAPI()

class GDPRRequest(BaseModel):
    guid: str
    request_type: str  # "EXPORT" or "DELETE"

@app.post("/gdpr/request")
def create_gdpr_request(req: GDPRRequest):
    # basic validation
    if req.request_type not in ["EXPORT", "DELETE"]:
        raise HTTPException(status_code=400, detail="Invalid request type")
    
    request_doc = {
        "guid": req.guid,
        "request_type": req.request_type,
        "status": "PENDING",
        "requested_at": datetime.utcnow(),
        "completed_at": None,
        "file_path": None
    }
    
    gdpr_requests.insert_one(request_doc)
    return {"message": "GDPR request accepted", "status": "PENDING"}
**Features of this design:**

Requests accepted sync → user sees instant confirmation

Heavy processing done async → exported files for download or notification

Full audit trail for each request

Can scale horizontally in AKS
**ASYNC PROCESSOR (Background Job)**
You can run this as separate worker in AKS (Python + Celery/RQ, or simple cron loop).
from pymongo import MongoClient
import json
import os
from datetime import datetime

client = MongoClient(os.environ["COSMOS_MONGO_URI"])
db = client["chatbot"]
chat_sessions = db["chat_sessions"]
gdpr_requests = db["gdpr_requests"]
audit_logs = db["audit_log"]

OUTPUT_DIR = "/tmp/gdpr_files"  # mounted storage or Azure Files

def process_gdpr_requests():
    pending_requests = gdpr_requests.find({"status": "PENDING"})
    
    for req in pending_requests:
        guid = req["guid"]
        req_type = req["request_type"]
        try:
            gdpr_requests.update_one({"_id": req["_id"]}, {"$set": {"status": "PROCESSING"}})
            
            if req_type == "EXPORT":
                # export chat data
                sessions = list(chat_sessions.find({"guid": guid}, {"_id": 0}))
                file_path = os.path.join(OUTPUT_DIR, f"{guid}_export.json")
                with open(file_path, "w") as f:
                    json.dump({"guid": guid, "sessions": sessions}, f, default=str)
                
            elif req_type == "DELETE":
                # delete chat data
                chat_sessions.delete_many({"guid": guid})
                file_path = os.path.join(OUTPUT_DIR, f"{guid}_delete_confirm.json")
                with open(file_path, "w") as f:
                    json.dump({"guid": guid, "deleted": True}, f)
            
            # mark request as completed
            gdpr_requests.update_one(
                {"_id": req["_id"]},
                {"$set": {
                    "status": "COMPLETED",
                    "completed_at": datetime.utcnow(),
                    "file_path": file_path
                }}
            )
            
            # audit log
            audit_logs.insert_one({
                "guid": guid,
                "action": req_type,
                "performed_by": "system_async",
                "timestamp": datetime.utcnow()
            })
            
        except Exception as e:
            gdpr_requests.update_one({"_id": req["_id"]}, {"$set": {"status": "FAILED"}})
            audit_logs.insert_one({
                "guid": guid,
                "action": f"{req_type}_FAILED",
                "performed_by": "system_async",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            })

**Features of this design:**

Requests accepted sync → user sees instant confirmation

Heavy processing done async → exported files for download or notification

Full audit trail for each request

Can scale horizontally in AKS
**TRACKING & NOTIFICATION**
Tracking: Use gdpr_requests.status + file_path

Notification: Worker generates JSON/CSV file per GUID

Optional: write to Azure Storage or blob for user download

Optional: trigger Event Grid for downstream systems

**ADDITIONAL CONSIDERATIONS**

TTL for old GDPR files: auto-delete after X days

Secure file storage: blob container with SAS tokens

Rate limiting: prevent spam GDPR requests

Optional: hash GUID in exported files if sharing outside internal systems


----------------------
Final architecture

Config-driven notification framework

Complete FastAPI (sync) service

Async worker

Pluggable notification handlers

How GET vs DELETE differ

How to extend later (blob, SFTP, webhook, etc.)
**FINAL ARCHITECTURE (SYNC + ASYNC)**
Client
  │
  │  (SYNC)
  ▼
GDPR API (FastAPI)
  └─ Create GDPR request
       ↓
Cosmos Mongo (gdpr_requests)
       ↓
Async Worker (AKS Job / Deployment)
  ├─ Process EXPORT or DELETE
  ├─ Generate output file (JSON)
  ├─ Invoke notification strategy
  └─ Update audit + status

CONFIGURATION MODEL (KEY TO EXTENSIBILITY):
notifications:
  EXPORT:
    - type: file
      config:
        output_dir: "/mnt/external/gdpr/exports"

    - type: http
      config:
        url: "https://external-system/api/gdpr/export/notify"
        method: "POST"
        timeout_seconds: 5
        headers:
          Authorization: "Bearer ${EXPORT_TOKEN}"

  DELETE:
    - type: http
      config:
        url: "https://external-system/api/gdpr/delete/notify"
        method: "POST"
        timeout_seconds: 5
        headers:
          Authorization: "Bearer ${DELETE_TOKEN}"
**What this gives you
**
✔ Different behavior per GDPR request
✔ Multiple notification channels per request
✔ Easy to add new types (blob, SFTP, event grid)
✔ Zero code change to switch behavior
NOTIFICATION INTERFACE:
notifiers/base.py
from abc import ABC, abstractmethod

class Notifier(ABC):
    @abstractmethod
    def notify(self, payload: dict):
        pass

HTTP NOTIFIER (GENERIC, REUSABLE):
notifiers/http.py
import requests

class HttpNotifier:
    def __init__(self, config: dict):
        self.url = config["url"]
        self.method = config.get("method", "POST")
        self.timeout = config.get("timeout_seconds", 5)
        self.headers = config.get("headers", {})

    def notify(self, payload: dict):
        response = requests.request(
            method=self.method,
            url=self.url,
            json=payload,
            headers=self.headers,
            timeout=self.timeout
        )
        response.raise_for_status()

FILE NOTIFIER (EXPORT USE CASE):
notifiers/file.py
import json
import os

class FileNotifier:
    def __init__(self, config: dict):
        self.output_dir = config["output_dir"]
        os.makedirs(self.output_dir, exist_ok=True)

    def notify(self, payload: dict):
        path = os.path.join(
            self.output_dir,
            f"{payload['guid']}_{payload['request_type']}.json"
        )
        with open(path, "w") as f:
            json.dump(payload, f, default=str)

NOTIFIER FACTORY (NOW ACTION-AWARE):
notifiers/factory.py
from notifiers.http import HttpNotifier
from notifiers.file import FileNotifier

def build_notifiers(notification_config: list):
    notifiers = []

    for entry in notification_config:
        ntype = entry["type"]
        cfg = entry["config"]

        if ntype == "http":
            notifiers.append(HttpNotifier(cfg))
        elif ntype == "file":
            notifiers.append(FileNotifier(cfg))

    return notifiers

ASYNC WORKER:
worker.py
import json
import os
import yaml
from datetime import datetime
from db import chat_sessions, gdpr_requests, audit_logs
from notifiers.factory import build_notifiers

OUTPUT_DIR = "/tmp/gdpr_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

def process_requests():
    requests = gdpr_requests.find({"status": "PENDING"})

    for req in requests:
        guid = req["guid"]
        rtype = req["request_type"]

        try:
            gdpr_requests.update_one(
                {"_id": req["_id"]},
                {"$set": {"status": "PROCESSING"}}
            )

            # ---- GDPR CORE LOGIC ----
            if rtype == "EXPORT":
                sessions = list(chat_sessions.find({"guid": guid}, {"_id": 0}))
                output_data = {
                    "guid": guid,
                    "request_type": "EXPORT",
                    "data": sessions
                }

            elif rtype == "DELETE":
                chat_sessions.delete_many({"guid": guid})
                output_data = {
                    "guid": guid,
                    "request_type": "DELETE",
                    "deleted": True
                }

            # ---- Write canonical output file (always) ----
            file_path = os.path.join(OUTPUT_DIR, f"{guid}_{rtype}.json")
            with open(file_path, "w") as f:
                json.dump(output_data, f, default=str)

            # ---- Notify based on CONFIG ----
            notification_entries = config["notifications"].get(rtype, [])
            notifiers = build_notifiers(notification_entries)

            notify_payload = {
                "guid": guid,
                "request_type": rtype,
                "status": "COMPLETED",
                "file_path": file_path,
                "timestamp": datetime.utcnow()
            }

            for notifier in notifiers:
                notifier.notify(notify_payload)

            # ---- Update DB ----
            gdpr_requests.update_one(
                {"_id": req["_id"]},
                {"$set": {
                    "status": "COMPLETED",
                    "completed_at": datetime.utcnow(),
                    "output": file_path
                }}
            )

            audit_logs.insert_one({
                "guid": guid,
                "action": rtype,
                "performed_by": "async_worker",
                "timestamp": datetime.utcnow()
            })

        except Exception as e:
            gdpr_requests.update_one(
                {"_id": req["_id"]},
                {"$set": {"status": "FAILED", "error": str(e)}}
            )

RESULTING BEHAVIOR:
EXPORT

Generate file

Place file in external location

Call external HTTP API

Both configurable

DELETE

Delete data

Call HTTP API only

No file exposure unless configured
**WHY THIS DESIGN IS AUDIT-SAFE & FUTURE-PROOF**

✔ GDPR actions are explicit & traceable
✔ Behavior controlled by policy (config)
✔ Easy to explain to auditors
✔ Supports multiple external systems
**HIGH-LEVEL SYSTEM DESIGN DIAGRAM**
┌──────────────────────┐
│  Client / Partner    │
│  (Portal / System)   │
└─────────┬────────────┘
          │  (1) Submit GDPR Request (SYNC)
          ▼
┌────────────────────────────────────┐
│      GDPR API (FastAPI, AKS)        │
│  - /gdpr/request                    │
│  - /gdpr/status                     │
│  - Auth / Validation                │
└─────────┬──────────────────────────┘
          │
          │  (2) Insert PENDING request
          ▼
┌────────────────────────────────────┐
│ Cosmos DB (Mongo API)               │
│                                    │
│  Collections:                      │
│  - chat_sessions                   │
│  - gdpr_requests                   │
│  - audit_log                       │
└─────────┬──────────────────────────┘
          │
          │  (3) Async pickup
          ▼
┌────────────────────────────────────┐
│ Async GDPR Worker (AKS)             │
│                                    │
│  - EXPORT: read + generate file    │
│  - DELETE: delete data             │
│  - Update status                   │
└─────────┬──────────────────────────┘
          │
          │  (4) Notification (config-driven)
          ▼
┌──────────────────────────────────────────────────────┐
│ Notification Targets (per config)                     │
│                                                       │
│  - External HTTP API                                  │
│  - External File Location (NFS / Blob / SFTP)         │
│  - (Future: Event Grid, Email, etc.)                  │
└──────────────────────────────────────────────────────┘

**DETAILED GDPR FLOW (STEP-BY-STEP)**
A. Submit GDPR Request (SYNC)
Client
  │ POST /gdpr/request
  │ { guid, request_type }
  ▼
GDPR API
  ├─ Validate request
  ├─ Insert record (PENDING)
  └─ Return 202 Accepted

Why sync?

Fast response

No long-running HTTP calls

Safe for retries
**B. Async Processing**
Async Worker
  │
  ├─ Find PENDING requests
  ├─ Mark PROCESSING
  │
  ├─ EXPORT
  │   ├─ Read chat_sessions by GUID
  │   └─ Generate JSON file
  │
  ├─ DELETE
  │   └─ Delete chat_sessions by GUID
  │
  ├─ Write canonical output file
  ├─ Notify external systems
  ├─ Update status → COMPLETED
  └─ Write audit log

**C. Notification (Policy Driven)**
EXPORT:
  - Write file to external location
  - Call HTTP endpoint with file reference

DELETE:
  - Call HTTP endpoint (confirmation only)

**D. Status Polling (SYNC)**
Client
  │ GET /gdpr/status?guid=...&type=EXPORT
  ▼
GDPR API
  ├─ Query gdpr_requests
  └─ Return status + metadata

STATUS POLLING API DESIGN:
Endpoint:
GET /gdpr/status/{guid}
OR GET /gdpr/status?guid=...&request_type=EXPORT
Response Model:
{
  "guid": "c2a4d2c7-...",
  "request_type": "EXPORT",
  "status": "COMPLETED",
  "requested_at": "2026-01-25T10:00:00Z",
  "completed_at": "2026-01-25T10:01:10Z",
  "output": {
    "file_path": "/mnt/external/gdpr/exports/c2a4d2c7_EXPORT.json"
  }
}

**FastAPI Example:**
from fastapi import HTTPException
from db import gdpr_requests

@app.get("/gdpr/status")
def get_status(guid: str, request_type: str):
    record = gdpr_requests.find_one(
        {"guid": guid, "request_type": request_type},
        {"_id": 0}
    )
    if not record:
        raise HTTPException(status_code=404, detail="Request not found")

    return record

**Explicit state machine:**
PENDING → PROCESSING → COMPLETED | FAILED
Evidence

Audit log per action

File artifacts

External notifications logged

✔ Least privilege

Worker only accesses required collections

API never touches chat data



