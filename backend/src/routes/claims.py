from datetime import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from ..database import get_db
from ..models import User, Policy, Claim, PolicyStatus
from ..schemas import (
    ClaimCreateRequest,
    ClaimResponse,
    MessageResponse
)
from ..dependencies import get_current_active_user

router = APIRouter(prefix="/claims", tags=["claims"])

UPLOAD_DIR = "uploads/claim_proofs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    claim_data: ClaimCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == claim_data.policy_id,
        Policy.policyholder_id == current_user.id
    ).first()

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    current_time = int(dt.utcnow().timestamp())

    if not policy.can_claim(current_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy is not eligible for claims"
        )

    if claim_data.claim_amount > float(policy.remaining_coverage()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim amount exceeds remaining coverage"
        )

    claim = Claim(
        policy_id=claim_data.policy_id,
        claimant_id=current_user.id,
        claim_amount=claim_data.claim_amount,
        proof=claim_data.proof,
        timestamp=current_time
    )

    policy.status = PolicyStatus.claim_pending
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return ClaimResponse(
        id=claim.id,
        policy_id=claim.policy_id,
        claimant_id=claim.claimant_id,
        claim_amount=float(claim.claim_amount),
        proof=claim.proof,
        timestamp=claim.timestamp,
        approved=claim.approved,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )


@router.post("/upload", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim_with_file(
    policy_id: int = Form(...),
    claim_amount: float = Form(..., gt=0),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.policyholder_id == current_user.id
    ).first()

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    current_time = int(dt.utcnow().timestamp())

    if not policy.can_claim(current_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Policy is not eligible for claims"
        )

    if claim_amount > float(policy.remaining_coverage()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim amount exceeds remaining coverage"
        )

    allowed_content_types = ["image/jpeg", "image/png", "application/pdf"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type not allowed. Allowed types: JPEG, PNG, PDF"
        )

    file_extension = file.filename.split(".")[-1] if "." in file.filename else "bin"
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    claim = Claim(
        policy_id=policy_id,
        claimant_id=current_user.id,
        claim_amount=claim_amount,
        proof=file_path,
        timestamp=current_time
    )

    policy.status = PolicyStatus.claim_pending
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return ClaimResponse(
        id=claim.id,
        policy_id=claim.policy_id,
        claimant_id=claim.claimant_id,
        claim_amount=float(claim.claim_amount),
        proof=claim.proof,
        timestamp=claim.timestamp,
        approved=claim.approved,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.claimant_id == current_user.id
    ).first()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )

    return ClaimResponse(
        id=claim.id,
        policy_id=claim.policy_id,
        claimant_id=claim.claimant_id,
        claim_amount=float(claim.claim_amount),
        proof=claim.proof,
        timestamp=claim.timestamp,
        approved=claim.approved,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )


@router.get("/", response_model=dict)
async def list_claims(
    policy_id: Optional[int] = Query(None, description="Filter by policy ID"),
    approved: Optional[bool] = Query(None, description="Filter by approval status"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Claim).filter(Claim.claimant_id == current_user.id)

    if policy_id is not None:
        query = query.filter(Claim.policy_id == policy_id)

    if approved is not None:
        query = query.filter(Claim.approved == approved)

    total = query.count()

    offset = (page - 1) * per_page
    claims = query.order_by(Claim.created_at.desc()).offset(offset).limit(per_page).all()

    claim_responses = [
        ClaimResponse(
            id=claim.id,
            policy_id=claim.policy_id,
            claimant_id=claim.claimant_id,
            claim_amount=float(claim.claim_amount),
            proof=claim.proof,
            timestamp=claim.timestamp,
            approved=claim.approved,
            created_at=claim.created_at,
            updated_at=claim.updated_at
        )
        for claim in claims
    ]

    return {
        "claims": claim_responses,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (offset + per_page) < total
    }


@router.patch("/{claim_id}", response_model=ClaimResponse)
async def update_claim_status(
    claim_id: int,
    approved: bool = Query(..., description="Approval status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    claim = db.query(Claim).filter(
        Claim.id == claim_id,
        Claim.claimant_id == current_user.id
    ).first()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found"
        )

    claim.approved = approved

    policy = db.query(Policy).filter(Policy.id == claim.policy_id).first()
    if policy:
        if approved:
            policy.status = PolicyStatus.claim_approved
            policy.claim_amount = policy.claim_amount + claim.claim_amount
        else:
            policy.status = PolicyStatus.claim_rejected

    db.commit()
    db.refresh(claim)

    return ClaimResponse(
        id=claim.id,
        policy_id=claim.policy_id,
        claimant_id=claim.claimant_id,
        claim_amount=float(claim.claim_amount),
        proof=claim.proof,
        timestamp=claim.timestamp,
        approved=claim.approved,
        created_at=claim.created_at,
        updated_at=claim.updated_at
    )


@router.get("/policy/{policy_id}", response_model=dict)
async def list_claims_by_policy(
    policy_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    policy = db.query(Policy).filter(
        Policy.id == policy_id,
        Policy.policyholder_id == current_user.id
    ).first()

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    query = db.query(Claim).filter(Claim.policy_id == policy_id)

    total = query.count()

    offset = (page - 1) * per_page
    claims = query.order_by(Claim.created_at.desc()).offset(offset).limit(per_page).all()

    claim_responses = [
        ClaimResponse(
            id=claim.id,
            policy_id=claim.policy_id,
            claimant_id=claim.claimant_id,
            claim_amount=float(claim.claim_amount),
            proof=claim.proof,
            timestamp=claim.timestamp,
            approved=claim.approved,
            created_at=claim.created_at,
            updated_at=claim.updated_at
        )
        for claim in claims
    ]

    return {
        "claims": claim_responses,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (offset + per_page) < total
    }
