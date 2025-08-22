"""
Tests for User Entity - Domain Layer (Focused Implementation)  
=============================================================

Essential tests for User aggregate root following DDD principles.
Tests user roles, permissions hierarchy, business validation, factory methods,
domain events, and core entity behavior.
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List
from uuid import UUID, uuid4

from boursa_vision.domain.entities.user import User, UserRole
from boursa_vision.domain.events.user_events import UserCreatedEvent, UserDeactivatedEvent
from boursa_vision.domain.value_objects.money import Currency


@pytest.fixture
def valid_user_data():
    """Fixture with valid user data"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }


@pytest.fixture  
def basic_user(valid_user_data):
    """Fixture for a basic user"""
    return User(**valid_user_data)


@pytest.fixture
def premium_user(valid_user_data):
    """Fixture for a premium user"""
    return User(**valid_user_data, role=UserRole.PREMIUM)


@pytest.fixture
def admin_user(valid_user_data):
    """Fixture for an admin user"""
    return User(**valid_user_data, role=UserRole.ADMIN)


class TestUserRole:
    """Tests for UserRole enum and permissions hierarchy"""

    def test_user_role_values(self):
        """Test UserRole enum has correct values"""
        assert UserRole.BASIC == "basic"
        assert UserRole.PREMIUM == "premium"
        assert UserRole.ADMIN == "admin"

    def test_basic_role_permissions(self):
        """Test BASIC role has correct permissions"""
        basic_permissions = UserRole.BASIC.permissions
        
        expected_basic = [
            "view_analytics",
            "view_basic_analytics", 
            "view_portfolios",
            "create_basic_portfolio",
            "view_public_data",
        ]
        
        assert len(basic_permissions) == 5
        for permission in expected_basic:
            assert permission in basic_permissions

    def test_premium_role_permissions(self):
        """Test PREMIUM role has basic + premium permissions (hierarchical)"""
        premium_permissions = UserRole.PREMIUM.permissions
        
        # Should have basic permissions
        basic_permissions = [
            "view_analytics",
            "view_basic_analytics",
            "view_portfolios",
            "create_basic_portfolio", 
            "view_public_data",
        ]
        
        # Plus premium permissions
        premium_specific = [
            "create_portfolio",
            "manage_own_portfolios",
            "execute_trades",
            "view_analytics",  # Also in premium role definition
            "view_advanced_analytics",
            "manage_alerts",
            "access_premium_features",
            "export_data",
            "real_time_data",
        ]
        
        # Total expected: basic (5) + premium (9) = 14 (view_analytics appears twice)
        expected_total = len(basic_permissions) + len(premium_specific)
        assert len(premium_permissions) == expected_total
        
        # Check that all basic permissions are included
        for permission in basic_permissions:
            assert permission in premium_permissions
            
        # Check that all premium-specific permissions are included  
        for permission in premium_specific:
            assert permission in premium_permissions

    def test_admin_role_permissions(self):
        """Test ADMIN role has all permissions (hierarchical)"""
        admin_permissions = UserRole.ADMIN.permissions
        
        # Should have basic permissions
        basic_permissions = [
            "view_analytics",
            "view_basic_analytics",
            "view_portfolios",
            "create_basic_portfolio",
            "view_public_data",
        ]
        
        # Premium permissions
        premium_specific = [
            "create_portfolio",
            "manage_own_portfolios",
            "execute_trades", 
            "view_advanced_analytics",
            "manage_alerts",
            "access_premium_features",
            "export_data",
            "real_time_data",
        ]
        
        # Admin specific permissions
        admin_specific = [
            "create_user",
            "delete_user",
            "manage_system",
            "delete_portfolio",
            "view_all_portfolios",
            "access_admin_panel",
            "manage_user_roles",
            "view_system_metrics",
        ]
        
        # Check all permissions are present
        for permission in basic_permissions:
            assert permission in admin_permissions
        for permission in premium_specific:
            assert permission in admin_permissions
        for permission in admin_specific:
            assert permission in admin_permissions
        
        # Admin should have more permissions than premium
        assert len(admin_permissions) > len(UserRole.PREMIUM.permissions)

    def test_role_permissions_hierarchy(self):
        """Test role hierarchy: ADMIN > PREMIUM > BASIC"""
        basic_count = len(UserRole.BASIC.permissions)
        premium_count = len(UserRole.PREMIUM.permissions)
        admin_count = len(UserRole.ADMIN.permissions)
        
        assert basic_count < premium_count < admin_count


class TestUserCreation:
    """Tests for User entity creation and initialization"""

    def test_user_default_initialization(self, valid_user_data):
        """Test User creation with default values"""
        user = User(**valid_user_data)
        
        assert isinstance(user.id, UUID)
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == ""
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.role == UserRole.BASIC
        assert user.preferred_currency == Currency.USD
        assert user.is_active is True
        assert user.email_verified is False
        assert user.two_factor_enabled is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.last_login is None

    def test_user_with_parameters(self):
        """Test User creation with custom parameters"""
        test_id = uuid4()
        test_time = datetime.now(timezone.utc)
        
        user = User(
            id=test_id,
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            first_name="John",
            last_name="Doe",
            role=UserRole.PREMIUM,
            preferred_currency=Currency.EUR,
            is_active=False,
            email_verified=True,
            two_factor_enabled=True,
            created_at=test_time,
            updated_at=test_time,
            last_login=test_time
        )
        
        assert user.id == test_id
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.role == UserRole.PREMIUM
        assert user.preferred_currency == Currency.EUR
        assert user.is_active is False
        assert user.email_verified is True
        assert user.two_factor_enabled is True
        assert user.created_at == test_time
        assert user.updated_at == test_time
        assert user.last_login == test_time

    def test_user_id_uniqueness(self):
        """Test that each user gets a unique ID"""
        user1 = User(
            email="user1@example.com",
            username="user1",
            first_name="User",
            last_name="One"
        )
        user2 = User(
            email="user2@example.com",
            username="user2", 
            first_name="User",
            last_name="Two"
        )
        
        assert user1.id != user2.id
        assert isinstance(user1.id, UUID)
        assert isinstance(user2.id, UUID)


class TestUserFactoryMethod:
    """Tests for User.create() factory method"""

    def test_user_create_factory_method(self):
        """Test User.create() factory method"""
        user = User.create(
            email="factory@example.com",
            username="factoryuser",
            password_hash="hashed_password",
            first_name="Factory",
            last_name="User",
            role=UserRole.PREMIUM,
            preferred_currency=Currency.GBP
        )
        
        assert user.email == "factory@example.com"
        assert user.username == "factoryuser"
        assert user.password_hash == "hashed_password"
        assert user.first_name == "Factory"
        assert user.last_name == "User"
        assert user.role == UserRole.PREMIUM
        assert user.preferred_currency == Currency.GBP
        assert user.is_active is True
        assert user.email_verified is False

    def test_user_create_with_defaults(self):
        """Test User.create() with default role and currency"""
        user = User.create(
            email="default@example.com",
            username="defaultuser",
            password_hash="hashed_password",
            first_name="Default",
            last_name="User"
        )
        
        assert user.role == UserRole.BASIC
        assert user.preferred_currency == Currency.USD

    def test_user_create_generates_domain_event(self):
        """Test User.create() generates UserCreatedEvent"""
        user = User.create(
            email="event@example.com",
            username="eventuser",
            password_hash="hashed_password",
            first_name="Event",
            last_name="User",
            role=UserRole.PREMIUM
        )
        
        events = user.get_domain_events()
        assert len(events) == 1
        
        event = events[0]
        assert isinstance(event, UserCreatedEvent)
        assert event.user_id == user.id
        assert event.email == "event@example.com"
        assert event.role == "premium"


class TestUserValidation:
    """Tests for User entity validation rules"""

    def test_validation_empty_email(self):
        """Test validation fails for empty email"""
        with pytest.raises(ValueError, match="Email is required"):
            User(email="", username="test", first_name="Test", last_name="User")

    def test_validation_invalid_email_format(self):
        """Test validation fails for invalid email format"""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid_email", username="test", first_name="Test", last_name="User")

    def test_validation_valid_email_format(self):
        """Test validation passes for valid email format"""
        # Should not raise exception
        user = User(email="valid@example.com", username="test", first_name="Test", last_name="User")
        assert user.email == "valid@example.com"

    def test_validation_empty_username(self):
        """Test validation fails for empty username"""
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            User(email="test@example.com", username="", first_name="Test", last_name="User")

    def test_validation_short_username(self):
        """Test validation fails for username too short"""
        with pytest.raises(ValueError, match="Username must be at least 3 characters"):
            User(email="test@example.com", username="ab", first_name="Test", last_name="User")

    def test_validation_minimum_username_length(self):
        """Test validation passes for minimum username length"""
        user = User(email="test@example.com", username="abc", first_name="Test", last_name="User")
        assert user.username == "abc"

    def test_validation_empty_first_name(self):
        """Test validation fails for empty first name"""
        with pytest.raises(ValueError, match="First name is required"):
            User(email="test@example.com", username="testuser", first_name="", last_name="User")

    def test_validation_empty_last_name(self):
        """Test validation fails for empty last name"""
        with pytest.raises(ValueError, match="Last name is required"):
            User(email="test@example.com", username="testuser", first_name="Test", last_name="")

    def test_validation_create_method_requires_password_hash(self):
        """Test User.create() validates password hash is required"""
        with pytest.raises(ValueError, match="Password hash is required for new users"):
            User.create(
                email="test@example.com",
                username="testuser",
                password_hash="",  # Empty password hash
                first_name="Test",
                last_name="User"
            )


class TestUserEquality:
    """Tests for User equality and hashing"""

    def test_user_equality_same_id(self, valid_user_data):
        """Test users with same ID are equal"""
        user_id = uuid4()
        user1 = User(id=user_id, username="user1", **{k:v for k,v in valid_user_data.items() if k != 'username'})
        user2 = User(id=user_id, username="user2", **{k:v for k,v in valid_user_data.items() if k != 'username'})  # Different username but same ID
        
        assert user1 == user2

    def test_user_inequality_different_id(self, valid_user_data):
        """Test users with different IDs are not equal"""
        user1 = User(username="user1", **{k:v for k,v in valid_user_data.items() if k != 'username'})
        user2 = User(username="user1", **{k:v for k,v in valid_user_data.items() if k != 'username'})  # Same username but different ID
        
        assert user1 != user2

    def test_user_inequality_with_non_user(self, basic_user):
        """Test user is not equal to non-User object"""
        assert basic_user != "not a user"
        assert basic_user != 42
        assert basic_user != None

    def test_user_hashable(self, valid_user_data):
        """Test users can be hashed and used in sets/dicts"""
        user1 = User(**valid_user_data)
        user2 = User(email="user2@example.com", username="user2", first_name="Test", last_name="User")
        
        # Should not raise exception
        user_set = {user1, user2}
        assert len(user_set) == 2
        
        user_dict = {user1: "first", user2: "second"}
        assert len(user_dict) == 2


class TestUserPermissions:
    """Tests for user permission checks"""

    def test_has_permission_active_basic_user(self, basic_user):
        """Test has_permission for active basic user"""
        basic_user.is_active = True
        
        assert basic_user.has_permission("view_analytics") is True
        assert basic_user.has_permission("view_basic_analytics") is True
        assert basic_user.has_permission("create_portfolio") is False  # Premium permission

    def test_has_permission_inactive_user(self, admin_user):
        """Test has_permission returns False for inactive user"""
        admin_user.is_active = False
        
        # Even admin permissions should return False when inactive
        assert admin_user.has_permission("view_analytics") is False
        assert admin_user.has_permission("manage_system") is False

    def test_has_permission_premium_user(self, premium_user):
        """Test has_permission for premium user"""
        premium_user.is_active = True
        
        # Basic permissions
        assert premium_user.has_permission("view_analytics") is True
        assert premium_user.has_permission("view_portfolios") is True
        
        # Premium permissions
        assert premium_user.has_permission("create_portfolio") is True
        assert premium_user.has_permission("manage_own_portfolios") is True
        assert premium_user.has_permission("access_premium_features") is True
        
        # Admin permissions should be False
        assert premium_user.has_permission("manage_system") is False
        assert premium_user.has_permission("delete_user") is False

    def test_has_permission_admin_user(self, admin_user):
        """Test has_permission for admin user"""
        admin_user.is_active = True
        
        # Should have all permissions
        assert admin_user.has_permission("view_analytics") is True
        assert admin_user.has_permission("create_portfolio") is True
        assert admin_user.has_permission("manage_system") is True
        assert admin_user.has_permission("delete_user") is True


class TestUserActivation:
    """Tests for user activation/deactivation"""

    def test_activate_inactive_user(self, basic_user):
        """Test activating an inactive user"""
        basic_user.is_active = False
        
        basic_user.activate()
        
        assert basic_user.is_active is True

    def test_activate_already_active_user(self, basic_user):
        """Test activating already active user (no-op)"""
        basic_user.is_active = True
        
        basic_user.activate()  # Should be no-op
        
        assert basic_user.is_active is True

    def test_deactivate_active_user(self, basic_user):
        """Test deactivating an active user"""
        basic_user.is_active = True
        
        basic_user.deactivate()
        
        assert basic_user.is_active is False
        
        # Should generate deactivation event
        events = basic_user.get_domain_events()
        assert len(events) == 1
        
        event = events[0]
        assert isinstance(event, UserDeactivatedEvent)
        assert event.user_id == basic_user.id
        assert event.email == "test@example.com"

    def test_deactivate_already_inactive_user(self, basic_user):
        """Test deactivating already inactive user (no-op)"""
        basic_user.is_active = False
        initial_events_count = len(basic_user.get_domain_events())
        
        basic_user.deactivate()  # Should be no-op
        
        assert basic_user.is_active is False
        # Should not generate additional events
        assert len(basic_user.get_domain_events()) == initial_events_count


class TestUserEmailVerification:
    """Tests for email verification functionality"""

    def test_verify_email(self, basic_user):
        """Test email verification"""
        basic_user.email_verified = False
        
        basic_user.verify_email()
        
        assert basic_user.email_verified is True

    def test_verify_already_verified_email(self, basic_user):
        """Test verifying already verified email"""
        basic_user.email_verified = True
        
        basic_user.verify_email()  # Should not cause issues
        
        assert basic_user.email_verified is True


class TestUserTwoFactorAuth:
    """Tests for two-factor authentication"""

    def test_enable_two_factor_verified_email(self, basic_user):
        """Test enabling 2FA with verified email"""
        basic_user.email_verified = True
        basic_user.two_factor_enabled = False
        
        basic_user.enable_two_factor()
        
        assert basic_user.two_factor_enabled is True

    def test_enable_two_factor_unverified_email(self, basic_user):
        """Test enabling 2FA fails with unverified email"""
        basic_user.email_verified = False
        basic_user.two_factor_enabled = False
        
        with pytest.raises(ValueError, match="Email must be verified before enabling 2FA"):
            basic_user.enable_two_factor()

    def test_disable_two_factor(self, basic_user):
        """Test disabling 2FA"""
        basic_user.two_factor_enabled = True
        
        basic_user.disable_two_factor()
        
        assert basic_user.two_factor_enabled is False


class TestUserLogin:
    """Tests for login-related functionality"""

    def test_update_last_login(self, basic_user):
        """Test updating last login timestamp"""
        basic_user.last_login = None
        
        before = datetime.now(timezone.utc)
        basic_user.update_last_login()
        after = datetime.now(timezone.utc)
        
        assert basic_user.last_login is not None
        assert before <= basic_user.last_login <= after

    def test_update_last_login_overwrites_previous(self, basic_user):
        """Test updating last login overwrites previous timestamp"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=1)
        basic_user.last_login = old_time
        
        basic_user.update_last_login()
        
        assert basic_user.last_login is not None
        assert basic_user.last_login > old_time


class TestUserPasswordManagement:
    """Tests for password management"""

    def test_change_password_valid_hash(self, basic_user):
        """Test changing password with valid hash"""
        basic_user.password_hash = "old_hash"
        old_updated_at = basic_user.updated_at
        
        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        basic_user.change_password("new_hash")
        
        assert basic_user.password_hash == "new_hash"
        assert basic_user.updated_at > old_updated_at

    def test_change_password_empty_hash(self, basic_user):
        """Test changing password fails with empty hash"""
        basic_user.password_hash = "old_hash"
        
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            basic_user.change_password("")


class TestUserRoleManagement:
    """Tests for role management"""

    def test_change_role_different_role(self, basic_user):
        """Test changing to different role"""
        basic_user.role = UserRole.BASIC
        
        basic_user.change_role(UserRole.PREMIUM)
        
        assert basic_user.role == UserRole.PREMIUM

    def test_change_role_same_role(self, basic_user):
        """Test changing to same role (no-op)"""
        basic_user.role = UserRole.BASIC
        
        basic_user.change_role(UserRole.BASIC)  # Should be no-op
        
        assert basic_user.role == UserRole.BASIC


class TestUserDisplayProperties:
    """Tests for user display properties"""

    def test_full_name_both_names(self, basic_user):
        """Test full_name with both first and last name"""
        assert basic_user.full_name == "Test User"

    def test_full_name_first_only(self, valid_user_data):
        """Test full_name with only first name"""
        user = User(**valid_user_data)
        user.last_name = ""
        
        assert user.full_name == "Test"

    def test_display_name_with_full_name(self, basic_user):
        """Test display_name returns full name when available"""
        assert basic_user.display_name == "Test User"

    def test_display_name_fallback_to_username(self, valid_user_data):
        """Test display_name falls back to username when no names"""
        user = User(**valid_user_data)
        user.first_name = ""
        user.last_name = ""
        
        assert user.display_name == "testuser"


class TestUserDomainEventsIntegration:
    """Tests for domain events integration"""

    def test_aggregate_root_inheritance(self, basic_user):
        """Test User inherits from AggregateRoot"""
        from boursa_vision.domain.entities.base import AggregateRoot
        
        assert isinstance(basic_user, AggregateRoot)
        assert hasattr(basic_user, '_domain_events')
        assert hasattr(basic_user, 'get_domain_events')
        assert hasattr(basic_user, 'clear_domain_events')

    def test_clear_domain_events(self):
        """Test clearing domain events"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            first_name="Test",
            last_name="User"
        )
        
        # Should have creation event
        assert len(user.get_domain_events()) == 1
        
        user.clear_domain_events()
        
        assert len(user.get_domain_events()) == 0

    def test_multiple_domain_events(self):
        """Test accumulating multiple domain events"""
        user = User.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash",
            first_name="Test",
            last_name="User"
        )
        
        # Creation event
        assert len(user.get_domain_events()) == 1
        
        # Deactivation event
        user.deactivate()
        
        events = user.get_domain_events()
        assert len(events) == 2
        
        # Check event types
        event_types = [type(event).__name__ for event in events]
        assert "UserCreatedEvent" in event_types
        assert "UserDeactivatedEvent" in event_types


class TestUserEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_user_with_unicode_characters(self):
        """Test user with unicode characters in names"""
        user = User(
            email="jose@example.com",
            first_name="José",
            last_name="García",
            username="jose_garcia"
        )
        
        assert user.full_name == "José García"
        assert "José García" in str(user)

    def test_user_currency_all_types(self):
        """Test user with different currency types"""
        currencies = [Currency.USD, Currency.EUR, Currency.GBP]
        
        for currency in currencies:
            user = User(
                email=f"test_{currency.value}@example.com",
                username=f"testuser_{currency.value}",
                first_name="Test",
                last_name="User", 
                preferred_currency=currency
            )
            assert user.preferred_currency == currency

    def test_user_role_all_types(self):
        """Test user with all role types"""
        roles = [UserRole.BASIC, UserRole.PREMIUM, UserRole.ADMIN]
        
        for role in roles:
            user = User(
                email=f"test_{role.value}@example.com",
                username=f"testuser_{role.value}",
                first_name="Test",
                last_name="User",
                role=role
            )
            assert user.role == role
            assert isinstance(user.role.permissions, list)
            assert len(user.role.permissions) > 0
