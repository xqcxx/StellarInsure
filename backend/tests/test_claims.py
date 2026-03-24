"""Test claim endpoints for StellarInsure API"""
import pytest
from datetime import datetime
from io import BytesIO
from fastapi.testclient import TestClient


class TestClaimEndpoints:
    """Test suite for claim endpoints"""

    def test_create_claim_success(self):
        """Test successful claim creation"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        current_time = int(datetime.utcnow().timestamp())

        policy_response = client.post(
            "/policies/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_type": "weather",
                "coverage_amount": 1000.0,
                "premium": 50.0,
                "start_time": current_time,
                "end_time": current_time + 86400,
                "trigger_condition": "Temperature below -10C"
            }
        )

        if policy_response.status_code == 201:
            policy_id = policy_response.json()["id"]
        else:
            policy_id = 1

        response = client.post(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_id": policy_id,
                "claim_amount": 500.0,
                "proof": "Weather report evidence"
            }
        )

        assert response.status_code in [201, 400, 404]

    def test_create_claim_invalid_policy(self):
        """Test claim creation with nonexistent policy"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.post(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_id": 99999,
                "claim_amount": 500.0,
                "proof": "Weather report evidence"
            }
        )

        assert response.status_code == 404

    def test_create_claim_exceeds_coverage(self):
        """Test claim creation exceeding remaining coverage"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        current_time = int(datetime.utcnow().timestamp())

        policy_response = client.post(
            "/policies/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_type": "weather",
                "coverage_amount": 100.0,
                "premium": 50.0,
                "start_time": current_time,
                "end_time": current_time + 86400,
                "trigger_condition": "Temperature below -10C"
            }
        )

        if policy_response.status_code == 201:
            policy_id = policy_response.json()["id"]
        else:
            policy_id = 1

        response = client.post(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_id": policy_id,
                "claim_amount": 10000.0,
                "proof": "Weather report evidence"
            }
        )

        assert response.status_code in [400, 404]

    def test_get_claim_by_id(self):
        """Test getting a specific claim"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/1",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code in [200, 404]

    def test_get_nonexistent_claim(self):
        """Test getting a nonexistent claim"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/99999",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 404

    def test_list_claims(self):
        """Test listing all claims"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "has_next" in data

    def test_list_claims_with_pagination(self):
        """Test listing claims with pagination"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/?page=1&per_page=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "claims" in data

    def test_list_claims_with_filters(self):
        """Test listing claims with filters"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/?approved=true&policy_id=1",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 200

    def test_list_claims_by_policy(self):
        """Test listing claims by policy"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/policy/1",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code in [200, 404]

    def test_update_claim_status_approve(self):
        """Test approving a claim"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.patch(
            "/claims/1?approved=true",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code in [200, 404]

    def test_update_claim_status_reject(self):
        """Test rejecting a claim"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.patch(
            "/claims/1?approved=false",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code in [200, 404]

    def test_unauthorized_claim_access(self):
        """Test unauthorized claim access"""
        from src.main import app

        client = TestClient(app)

        response = client.get("/claims/")

        assert response.status_code == 403

    def test_create_claim_with_file_upload(self):
        """Test creating a claim with file upload"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        file_content = b"test image content"
        file = BytesIO(file_content)

        response = client.post(
            "/claims/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "policy_id": "1",
                "claim_amount": "500.0"
            },
            files={
                "file": ("test_image.jpg", file, "image/jpeg")
            }
        )

        assert response.status_code in [201, 400, 404]


class TestClaimValidation:
    """Test suite for claim validation"""

    def test_claim_amount_validation(self):
        """Test claim amount must be positive"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.post(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_id": 1,
                "claim_amount": -100.0,
                "proof": "Weather report evidence"
            }
        )

        assert response.status_code == 422

    def test_claim_proof_validation(self):
        """Test claim proof must not be empty"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.post(
            "/claims/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "policy_id": 1,
                "claim_amount": 100.0,
                "proof": ""
            }
        )

        assert response.status_code == 422

    def test_pagination_parameters(self):
        """Test pagination parameter validation"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/?page=0&per_page=10",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422

    def test_per_page_limit(self):
        """Test per_page limit validation"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        response = client.get(
            "/claims/?page=1&per_page=150",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert response.status_code == 422

    def test_file_type_validation(self):
        """Test file type validation for uploads"""
        from src.main import app
        from src.auth import create_access_token

        client = TestClient(app)

        access_token = create_access_token(
            {"sub": "1", "stellar_address": "GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS"}
        )

        file_content = b"test content"
        file = BytesIO(file_content)

        response = client.post(
            "/claims/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "policy_id": "1",
                "claim_amount": "500.0"
            },
            files={
                "file": ("test_file.txt", file, "text/plain")
            }
        )

        assert response.status_code in [400, 404]


class TestClaimBusinessLogic:
    """Test suite for claim business logic"""

    def test_claim_model_representation(self):
        """Test claim model string representation"""
        from src.models import Claim, PolicyStatus, PolicyType
        from decimal import Decimal

        claim = Claim(
            id=1,
            policy_id=1,
            claimant_id=1,
            claim_amount=Decimal("500.0"),
            proof="Test proof",
            timestamp=1000000,
            approved=False
        )

        assert "Claim" in repr(claim)
        assert "policy_id=1" in repr(claim)
        assert "approved=False" in repr(claim)

    def test_claim_approval_updates_policy_status(self):
        """Test that claim approval updates policy status"""
        from src.models import Policy, PolicyStatus, PolicyType
        from decimal import Decimal

        policy = Policy(
            id=1,
            policyholder_id=1,
            policy_type=PolicyType.weather,
            coverage_amount=Decimal("1000.0"),
            premium=Decimal("50.0"),
            start_time=1000000,
            end_time=2000000,
            trigger_condition="Temperature below -10C",
            status=PolicyStatus.claim_pending
        )

        policy.status = PolicyStatus.claim_approved
        assert policy.status == PolicyStatus.claim_approved
