from fastapi import FastAPI, APIRouter, HTTPException, Depends, Header
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (must use env variables only)
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security setup
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_SECRET = os.environ.get("ADMIN_JWT_SECRET", "dev-admin-secret")  # acceptable fallback for MVP
JWT_ALG = "HS256"

# Utils for Mongo <-> Pydantic

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def prepare_for_mongo(data: dict) -> dict:
    # Convert datetime/date/time to strings for Mongo
    for k, v in list(data.items()):
        if isinstance(v, datetime):
            data[k] = v.astimezone(timezone.utc).isoformat()
    return data


def parse_from_mongo(item: dict) -> dict:
    if not item:
        return item
    item.pop("_id", None)  # Never expose ObjectId
    return item

# Pydantic Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: str = Field(default_factory=iso_now)

class StatusCheckCreate(BaseModel):
    client_name: str

class AlumniCreate(BaseModel):
    full_name: str
    graduation_year: int
    bacalaureat_passed: bool
    path: str  # "faculty" | "employed" | "other"
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class Alumni(AlumniCreate):
    id: str
    created_at: str

class EventCreate(BaseModel):
    title: str
    date: str  # ISO date string (yyyy-mm-dd) for MVP simplicity
    location: str
    description: Optional[str] = None

class Event(EventCreate):
    id: str
    created_at: str

class InvitationCreate(BaseModel):
    event_id: str

class Invitation(BaseModel):
    id: str
    token: str
    event_id: str
    created_at: str
    rsvp_status: Optional[str] = None  # "yes" | "no"
    rsvp_at: Optional[str] = None

class RSVPRequest(BaseModel):
    status: str  # "yes" or "no"

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str

# Auth helpers
async def ensure_admin_seed():
    # Seed a default admin user if not present
    existing = await db.users.find_one({"username": "admin"})
    if not existing:
        hashed = pwd_context.hash("admin123")
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": hashed,
            "created_at": iso_now(),
        })

async def get_current_user(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        scheme, token = authorization.split(" ")
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Alumni & Events API active"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(client_name=input.client_name)
    await db.status_checks.insert_one(prepare_for_mongo(status_obj.model_dump()))
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(length=1000)
    return [StatusCheck(**parse_from_mongo(s)) for s in status_checks]

# Auth
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(data: LoginRequest):
    user = await db.users.find_one({"username": data.username})
    if not user or not pwd_context.verify(data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    exp = datetime.now(timezone.utc) + timedelta(hours=24)
    token = jwt.encode({"sub": data.username, "exp": exp}, JWT_SECRET, algorithm=JWT_ALG)
    return LoginResponse(access_token=token, username=data.username)

# Alumni CRUD
@api_router.post("/alumni", response_model=Alumni)
async def create_alumni(payload: AlumniCreate, _: str = Depends(get_current_user)):
    new_obj = Alumni(
        id=str(uuid.uuid4()),
        created_at=iso_now(),
        **payload.model_dump(),
    )
    await db.alumni.insert_one(prepare_for_mongo(new_obj.model_dump()))
    return new_obj

@api_router.get("/alumni", response_model=List[Alumni])
async def list_alumni():
    rows = await db.alumni.find().sort("created_at", -1).to_list(length=1000)
    return [Alumni(**parse_from_mongo(r)) for r in rows]

@api_router.get("/alumni/{alumni_id}", response_model=Alumni)
async def get_alumni(alumni_id: str):
    row = await db.alumni.find_one({"id": alumni_id})
    if not row:
        raise HTTPException(status_code=404, detail="Alumnus not found")
    return Alumni(**parse_from_mongo(row))

@api_router.put("/alumni/{alumni_id}", response_model=Alumni)
async def update_alumni(alumni_id: str, payload: AlumniCreate, _: str = Depends(get_current_user)):
    row = await db.alumni.find_one({"id": alumni_id})
    if not row:
        raise HTTPException(status_code=404, detail="Alumnus not found")
    updated = {
        **row,
        **prepare_for_mongo(payload.model_dump()),
    }
    await db.alumni.update_one({"id": alumni_id}, {"$set": updated})
    updated = await db.alumni.find_one({"id": alumni_id})
    return Alumni(**parse_from_mongo(updated))

@api_router.delete("/alumni/{alumni_id}")
async def delete_alumni(alumni_id: str, _: str = Depends(get_current_user)):
    await db.alumni.delete_one({"id": alumni_id})
    return {"ok": True}

# Events CRUD
@api_router.post("/events", response_model=Event)
async def create_event(payload: EventCreate, _: str = Depends(get_current_user)):
    evt = Event(id=str(uuid.uuid4()), created_at=iso_now(), **payload.model_dump())
    await db.events.insert_one(prepare_for_mongo(evt.model_dump()))
    return evt

@api_router.get("/events", response_model=List[Event])
async def list_events():
    rows = await db.events.find().sort("created_at", -1).to_list(length=1000)
    return [Event(**parse_from_mongo(r)) for r in rows]

@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: str):
    row = await db.events.find_one({"id": event_id})
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return Event(**parse_from_mongo(row))

# Invitations
@api_router.post("/invitations", response_model=Invitation)
async def create_invitation(data: InvitationCreate, _: str = Depends(get_current_user)):
    # Ensure event exists
    ev = await db.events.find_one({"id": data.event_id})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    inv = Invitation(
        id=str(uuid.uuid4()),
        token=str(uuid.uuid4()),
        event_id=data.event_id,
        created_at=iso_now(),
    )
    await db.invitations.insert_one(inv.model_dump())
    return inv

@api_router.get("/invitations/{token}")
async def get_invitation_by_token(token: str):
    inv = await db.invitations.find_one({"token": token})
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    ev = await db.events.find_one({"id": inv.get("event_id")})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return {
        "invitation": parse_from_mongo(inv),
        "event": parse_from_mongo(ev),
    }

@api_router.post("/invitations/{token}/rsvp")
async def rsvp_invitation(token: str, req: RSVPRequest):
    if req.status not in ("yes", "no"):
        raise HTTPException(status_code=400, detail="Invalid RSVP status")
    inv = await db.invitations.find_one({"token": token})
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found")
    await db.invitations.update_one({"token": token}, {"$set": {"rsvp_status": req.status, "rsvp_at": iso_now()}})
    inv = await db.invitations.find_one({"token": token})
    ev = await db.events.find_one({"id": inv.get("event_id")})
    return {
        "invitation": parse_from_mongo(inv),
        "event": parse_from_mongo(ev) if ev else None,
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def on_startup():
    await ensure_admin_seed()

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
