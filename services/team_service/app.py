from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
import uuid
import hashlib
import secrets

app = FastAPI(title="Team Management Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

class TeamMember(BaseModel):
    user_id: str
    email: EmailStr
    role: str = "member"
    joined_at: datetime = Field(default_factory=datetime.now)

class Team(BaseModel):
    team_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[TeamMember] = []
    created_at: datetime = Field(default_factory=datetime.now)
    credits: float = 0.0
    subscription_tier: str = "free"
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

class CreateTeamRequest(BaseModel):
    name: str
    description: Optional[str] = None
    owner_email: EmailStr

class AddMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=datetime.now)
    api_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

teams_db: Dict[str, Team] = {}
users_db: Dict[str, User] = {}
email_to_user: Dict[str, str] = {}

@app.get("/")
async def root():
    return {
        "service": "Team Management Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/users", response_model=User)
async def create_user(email: EmailStr, name: str):
    if email in email_to_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user = User(email=email, name=name)
    users_db[user.user_id] = user
    email_to_user[email] = user.user_id
    
    return user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/teams", response_model=Team)
async def create_team(request: CreateTeamRequest):
    if request.owner_email not in email_to_user:
        raise HTTPException(status_code=404, detail="Owner user not found")
    
    owner_id = email_to_user[request.owner_email]
    owner = users_db[owner_id]
    
    team = Team(
        name=request.name,
        description=request.description,
        owner_id=owner_id,
        members=[TeamMember(user_id=owner_id, email=owner.email, role="owner")]
    )
    
    teams_db[team.team_id] = team
    return team

@app.get("/teams", response_model=List[Team])
async def list_teams(user_id: Optional[str] = None):
    if user_id:
        user_teams = [
            team for team in teams_db.values()
            if any(member.user_id == user_id for member in team.members)
        ]
        return user_teams
    
    return list(teams_db.values())

@app.get("/teams/{team_id}", response_model=Team)
async def get_team(team_id: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    return teams_db[team_id]

@app.post("/teams/{team_id}/members")
async def add_team_member(team_id: str, request: AddMemberRequest):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if request.email not in email_to_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    team = teams_db[team_id]
    user_id = email_to_user[request.email]
    
    if any(member.user_id == user_id for member in team.members):
        raise HTTPException(status_code=400, detail="User already a member of this team")
    
    member = TeamMember(user_id=user_id, email=request.email, role=request.role)
    team.members.append(member)
    
    return {"message": "Member added successfully", "member": member}

@app.delete("/teams/{team_id}/members/{user_id}")
async def remove_team_member(team_id: str, user_id: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    
    if team.owner_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot remove team owner")
    
    team.members = [m for m in team.members if m.user_id != user_id]
    
    return {"message": "Member removed successfully"}

@app.post("/teams/{team_id}/credits")
async def add_credits(team_id: str, amount: float):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    team.credits += amount
    
    return {
        "message": "Credits added successfully",
        "team_id": team_id,
        "new_balance": team.credits
    }

@app.post("/teams/{team_id}/credits/deduct")
async def deduct_credits(team_id: str, amount: float):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    
    if team.credits < amount:
        raise HTTPException(status_code=400, detail="Insufficient credits")
    
    team.credits -= amount
    
    return {
        "message": "Credits deducted successfully",
        "team_id": team_id,
        "new_balance": team.credits
    }

@app.get("/teams/{team_id}/credits")
async def get_team_credits(team_id: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    return {
        "team_id": team_id,
        "credits": team.credits,
        "subscription_tier": team.subscription_tier
    }

@app.put("/teams/{team_id}/subscription")
async def update_subscription(team_id: str, tier: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    valid_tiers = ["free", "basic", "pro", "enterprise"]
    if tier not in valid_tiers:
        raise HTTPException(status_code=400, detail=f"Invalid tier. Must be one of: {valid_tiers}")
    
    team = teams_db[team_id]
    team.subscription_tier = tier
    
    return {
        "message": "Subscription updated successfully",
        "team_id": team_id,
        "new_tier": tier
    }

@app.get("/teams/{team_id}/api-key")
async def get_team_api_key(team_id: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    return {
        "team_id": team_id,
        "api_key": team.api_key
    }

@app.post("/teams/{team_id}/api-key/regenerate")
async def regenerate_api_key(team_id: str):
    if team_id not in teams_db:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team = teams_db[team_id]
    team.api_key = secrets.token_urlsafe(32)
    
    return {
        "message": "API key regenerated successfully",
        "team_id": team_id,
        "new_api_key": team.api_key
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
