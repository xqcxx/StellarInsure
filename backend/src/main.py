from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings

settings = get_settings()

app = FastAPI(title="StellarInsure API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "StellarInsure API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/policies")
async def get_policies():
    # TODO: Implement policy fetching
    return {"policies": []}

@app.get("/api/policies/{policy_id}")
async def get_policy(policy_id: int):
    # TODO: Implement policy details
    return {"policy_id": policy_id}

@app.post("/api/claims")
async def submit_claim():
    # TODO: Implement claim submission
    return {"message": "Claim submitted"}
