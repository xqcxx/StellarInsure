"""Test Stellar smart contract integration for StellarInsure API"""
import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime


class TestStellarServiceInit:
    """Test suite for StellarService initialization"""

    def test_service_initialization(self):
        """Test that StellarService initializes correctly"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract_id",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()
            assert service is not None

    def test_service_uses_testnet_settings(self):
        """Test that service uses testnet settings when configured"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract_id",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()
            assert "testnet" in service.settings.stellar_horizon_url.lower()


class TestStellarConfig:
    """Test suite for Stellar configuration"""

    def test_config_has_stellar_settings(self):
        """Test that configuration includes Stellar settings"""
        from src.config import Settings

        settings = Settings()
        assert hasattr(settings, 'stellar_network_passphrase')
        assert hasattr(settings, 'stellar_horizon_url')
        assert hasattr(settings, 'stellar_contract_id')

    def test_config_default_testnet(self):
        """Test that default configuration is for testnet"""
        from src.config import Settings

        settings = Settings()
        assert "testnet" in settings.stellar_horizon_url.lower() or "test" in settings.stellar_network_passphrase.lower()

    def test_is_testnet_property(self):
        """Test is_testnet property detection"""
        from src.config import Settings

        settings = Settings()
        assert settings.is_testnet is True


class TestTransactionBuilding:
    """Test suite for transaction building"""

    def test_build_transaction_requires_contract_id(self):
        """Test that transaction building requires a contract ID"""
        from src.services.stellar_service import StellarService, StellarContractError

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id=None,
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            with pytest.raises(StellarContractError) as exc_info:
                service.build_transaction(
                    source_public_key="GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS",
                    contract_function="test_function",
                    contract_args=[]
                )
            assert "Contract ID" in str(exc_info.value)


class TestContractInvocation:
    """Test suite for contract function invocation"""

    def test_invoke_contract_requires_keypair(self):
        """Test that contract invocation requires a keypair"""
        from src.services.stellar_service import StellarService, StellarContractError

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            with pytest.raises(StellarContractError) as exc_info:
                import asyncio
                asyncio.run(service.invoke_contract(
                    function_name="test_function",
                    args=[]
                ))
            assert "keypair" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_create_policy_contract(self):
        """Test creating a policy contract"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret="SBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service, 'invoke_contract', new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {"hash": "test_hash", "status": "pending"}

                result = await service.create_policy_contract(
                    policy_id=1,
                    policyholder_address="GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS",
                    coverage_amount=1000.0,
                    premium=50.0,
                    start_time=1000000,
                    end_time=2000000,
                    trigger_condition="Temperature below -10C"
                )

                assert result["hash"] == "test_hash"
                mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_claim_contract(self):
        """Test submitting a claim contract"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret="SBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service, 'invoke_contract', new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {"hash": "test_hash", "status": "pending"}

                result = await service.submit_claim_contract(
                    claim_id=1,
                    policy_id=1,
                    claimant_address="GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS",
                    claim_amount=500.0,
                    proof="Weather report evidence"
                )

                assert result["hash"] == "test_hash"
                mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_claim_contract(self):
        """Test approving a claim contract"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret="SBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service, 'invoke_contract', new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {"hash": "test_hash", "status": "pending"}

                result = await service.approve_claim_contract(claim_id=1)

                assert result["hash"] == "test_hash"
                mock_invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_reject_claim_contract(self):
        """Test rejecting a claim contract"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret="SBXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service, 'invoke_contract', new_callable=AsyncMock) as mock_invoke:
                mock_invoke.return_value = {"hash": "test_hash", "status": "pending"}

                result = await service.reject_claim_contract(
                    claim_id=1,
                    reason="Invalid claim"
                )

                assert result["hash"] == "test_hash"
                mock_invoke.assert_called_once()


class TestTransactionStatus:
    """Test suite for transaction status checking"""

    def test_get_transaction_status_success(self):
        """Test getting transaction status"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service.server.transactions(), 'transaction') as mock_tx:
                mock_tx.return_value.transaction.return_value.call.return_value = {
                    "hash": "test_hash",
                    "status": "success",
                    "ledger": 12345,
                    "created_at": "2024-01-01T00:00:00Z",
                    "successful": True
                }

                result = service.get_transaction_status("test_hash")

                assert result["hash"] == "test_hash"
                assert result["status"] == "success"

    def test_get_transaction_status_not_found(self):
        """Test getting status for non-existent transaction"""
        from src.services.stellar_service import StellarService
        from stellar_sdk.exceptions import NotFoundError

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            with patch.object(service.server.transactions(), 'transaction') as mock_tx:
                from stellar_sdk.exceptions import NotFoundError
                mock_tx.return_value.transaction.return_value.call.side_effect = NotFoundError(
                    404, "Transaction not found"
                )

                result = service.get_transaction_status("nonexistent_hash")

                assert result["status"] == "not_found"


class TestEventListening:
    """Test suite for event listening"""

    @pytest.mark.asyncio
    async def test_listen_for_events_requires_contract_id(self):
        """Test that event listening requires contract ID"""
        from src.services.stellar_service import StellarService, StellarContractError

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id=None,
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            with pytest.raises(StellarContractError) as exc_info:
                async for _ in service.listen_for_events():
                    pass
            assert "Contract ID" in str(exc_info.value)


class TestSignatureVerification:
    """Test suite for Stellar signature verification"""

    @pytest.mark.asyncio
    async def test_verify_stellar_signature(self):
        """Test Stellar signature verification"""
        from src.services.stellar_service import StellarService

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            result = await service.verify_stellar_signature(
                public_key="GABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789ABCDEFGHIJKLMNOPQRS",
                signature="test_signature",
                message="test_message"
            )

            assert isinstance(result, bool)


class TestTransactionRecordStorage:
    """Test suite for transaction record storage"""

    @pytest.mark.asyncio
    async def test_store_transaction_record(self):
        """Test storing transaction record"""
        from src.services.stellar_service import StellarService
        from src.models import Transaction

        with patch('src.services.stellar_service.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                stellar_horizon_url="https://horizon-testnet.stellar.org",
                is_testnet=True,
                stellar_contract_id="test_contract",
                stellar_admin_secret=None,
                stellar_admin_public=None
            )

            service = StellarService()

            mock_db = Mock()
            mock_transaction = Transaction(
                id=1,
                user_id=1,
                transaction_hash="test_hash",
                amount=100.0,
                transaction_type="premium",
                status="pending"
            )

            with patch.object(mock_db, 'add'), \
                 patch.object(mock_db, 'commit'), \
                 patch.object(mock_db, 'refresh'):
                mock_db.add.return_value = None
                mock_db.commit.return_value = None
                mock_db.refresh.return_value = None

                result = await service.store_transaction_record(
                    db=mock_db,
                    user_id=1,
                    transaction_hash="test_hash",
                    amount=100.0,
                    transaction_type="premium"
                )


class TestStellarContractError:
    """Test suite for StellarContractError"""

    def test_error_message(self):
        """Test that StellarContractError preserves message"""
        from src.services.stellar_service import StellarContractError

        error = StellarContractError("Test error message")
        assert str(error) == "Test error message"

    def test_error_inheritance(self):
        """Test that StellarContractError inherits from Exception"""
        from src.services.stellar_service import StellarContractError

        error = StellarContractError("Test error")
        assert isinstance(error, Exception)
