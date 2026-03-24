"""CORS security tests for StellarInsure API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


class TestCORSConfiguration:
    """Test suite for CORS security configuration"""

    def test_development_allows_localhost_origins(self):
        """Test that development environment allows localhost origins"""
        from src.main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_development_allows_localhost_5173(self):
        """Test that development allows Vite default port"""
        from src.main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    @patch.dict("os.environ", {"ENVIRONMENT": "production", "CORS_ORIGINS": "https://app.example.com,https://admin.example.com"})
    def test_production_allows_only_whitelisted_origins(self):
        """Test that production only allows whitelisted origins"""
        from src.config import get_settings
        
        get_settings.cache_clear()
        settings = get_settings()
        
        assert settings.environment == "production"
        assert settings.allowed_origins == ["https://app.example.com", "https://admin.example.com"]

    @patch.dict("os.environ", {"ENVIRONMENT": "production", "CORS_ORIGINS": ""})
    def test_production_empty_origins(self):
        """Test that production with empty CORS_ORIGINS returns empty list"""
        from src.config import get_settings
        
        get_settings.cache_clear()
        settings = get_settings()
        
        assert settings.environment == "production"
        assert settings.allowed_origins == []

    def test_config_cache(self):
        """Test that settings are properly cached"""
        from src.config import get_settings
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2

    def test_credentials_enabled(self):
        """Test that credentials are enabled for CORS"""
        from src.main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        assert "access-control-allow-credentials" in response.headers

    def test_allowed_methods(self):
        """Test that specific HTTP methods are allowed"""
        from src.main import app
        
        client = TestClient(app)
        
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        
        assert response.status_code == 200

    @patch.dict("os.environ", {"ENVIRONMENT": "development"})
    def test_wildcard_not_allowed_in_any_environment(self):
        """Test that wildcard origin is never allowed"""
        from src.config import get_settings
        
        get_settings.cache_clear()
        settings = get_settings()
        
        assert "*" not in settings.allowed_origins
