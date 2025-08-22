"""
Tests for User Entity - Domain Layer  
====================================

Comprehensive tests for User aggregate root following DDD principles.
Tests user roles, permissions hierarchy, business validation, factory methods,
domain events, and entity behavior.
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

    def test_role_enum_inheritance(self):
        """Test UserRole inherits from str and Enum"""
        assert isinstance(UserRole.BASIC, str)
        assert UserRole.BASIC == "basic"


class TestUserCreation:
    """Tests for User entity creation and initialization"""

    def test_user_default_initialization(self):
        """Test User creation with default values"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
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

    def test_user_timestamps_auto_generation(self):
        """Test that created_at and updated_at are automatically set"""
        before = datetime.now(timezone.utc)
        user = User(
            email="test@example.com",
            username="testuser", 
            first_name="Test",
            last_name="User"
        )
        after = datetime.now(timezone.utc)
        
        assert before <= user.created_at <= after
        assert before <= user.updated_at <= after

    def test_password_hash_hidden_in_repr(self):
        """Test that password_hash is hidden from repr for security"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test", 
            last_name="User",
            password_hash="secret_hash"
        )
        repr_str = repr(user)
        
        assert "secret_hash" not in repr_str
        assert "password_hash" not in repr_str


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

    def test_validation_valid_user(self):
        """Test validation passes for valid user data"""
        user = User(
            email="valid@example.com",
            username="validuser",
            first_name="Valid",
            last_name="User"
        )
        
        # Should not raise any exception
        assert user.email == "valid@example.com"


class TestUserEquality:
    """Tests for User equality and hashing"""

    def test_user_equality_same_id(self):
        """Test users with same ID are equal"""
        user_id = uuid4()
        user1 = User(id=user_id, email="user1@example.com", username="user1", first_name="User1", last_name="Test")
        user2 = User(id=user_id, email="user2@example.com", username="user2", first_name="User2", last_name="Test")  # Different username but same ID
        
        assert user1 == user2

    def test_user_inequality_different_id(self):
        """Test users with different IDs are not equal"""
        user1 = User(email="user1@example.com", username="user1", first_name="User1", last_name="Test")
        user2 = User(email="user1@example.com", username="user1", first_name="User1", last_name="Test")  # Same username but different ID
        
        assert user1 != user2

    def test_user_inequality_with_non_user(self):
        """Test user is not equal to non-User object"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        assert user != "not a user"
        assert user != 42
        assert user != None

    def test_user_hashable(self):
        """Test users can be hashed and used in sets/dicts"""
        user1 = User(email="user1@example.com", username="user1", first_name="User1", last_name="Test")
        user2 = User(email="user2@example.com", username="user2", first_name="User2", last_name="Test")
        
        # Should not raise exception
        user_set = {user1, user2}
        assert len(user_set) == 2
        
        user_dict = {user1: "first", user2: "second"}
        assert len(user_dict) == 2

    def test_user_hash_consistency(self):
        """Test user hash is consistent and based on ID"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        hash1 = hash(user)
        hash2 = hash(user)
        
        assert hash1 == hash2
        assert hash1 == hash(user.id)


class TestUserPermissions:
    """Tests for user permission checks"""

    def test_has_permission_active_user(self):
        """Test has_permission for active user"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.BASIC,
            is_active=True
        )
        
        assert user.has_permission("view_analytics") is True
        assert user.has_permission("view_basic_analytics") is True
        assert user.has_permission("create_portfolio") is False  # Premium permission

    def test_has_permission_inactive_user(self):
        """Test has_permission returns False for inactive user"""
        user = User(
            email="test@example.com",
            username="testuser", 
            first_name="Test",
            last_name="User",
            role=UserRole.ADMIN,
            is_active=False
        )
        
        # Even admin permissions should return False when inactive
        assert user.has_permission("view_analytics") is False
        assert user.has_permission("manage_system") is False

    def test_has_permission_premium_user(self):
        """Test has_permission for premium user"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test", 
            last_name="User",
            role=UserRole.PREMIUM,
            is_active=True
        )
        
        # Basic permissions
        assert user.has_permission("view_analytics") is True
        assert user.has_permission("view_portfolios") is True
        
        # Premium permissions
        assert user.has_permission("create_portfolio") is True
        assert user.has_permission("manage_own_portfolios") is True
        assert user.has_permission("access_premium_features") is True
        
        # Admin permissions should be False
        assert user.has_permission("manage_system") is False
        assert user.has_permission("delete_user") is False

    def test_has_permission_admin_user(self):
        """Test has_permission for admin user"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User", 
            role=UserRole.ADMIN,
            is_active=True
        )
        
        # Should have all permissions
        assert user.has_permission("view_analytics") is True
        assert user.has_permission("create_portfolio") is True
        assert user.has_permission("manage_system") is True
        assert user.has_permission("delete_user") is True


class TestUserActivation:
    """Tests for user activation/deactivation"""

    def test_activate_inactive_user(self):
        """Test activating an inactive user"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=False
        )
        
        user.activate()
        
        assert user.is_active is True

    def test_activate_already_active_user(self):
        """Test activating already active user (no-op)"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        
        user.activate()  # Should be no-op
        
        assert user.is_active is True

    def test_deactivate_active_user(self):
        """Test deactivating an active user"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=True
        )
        
        user.deactivate()
        
        assert user.is_active is False
        
        # Should generate deactivation event
        events = user.get_domain_events()
        assert len(events) == 1
        
        event = events[0]
        assert isinstance(event, UserDeactivatedEvent)
        assert event.user_id == user.id
        assert event.email == "test@example.com"

    def test_deactivate_already_inactive_user(self):
        """Test deactivating already inactive user (no-op)"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            is_active=False
        )
        initial_events_count = len(user.get_domain_events())
        
        user.deactivate()  # Should be no-op
        
        assert user.is_active is False
        # Should not generate additional events
        assert len(user.get_domain_events()) == initial_events_count


class TestUserEmailVerification:
    """Tests for email verification functionality"""

    def test_verify_email(self):
        """Test email verification"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test", 
            last_name="User",
            email_verified=False
        )
        
        user.verify_email()
        
        assert user.email_verified is True

    def test_verify_already_verified_email(self):
        """Test verifying already verified email"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            email_verified=True
        )
        
        user.verify_email()  # Should not cause issues
        
        assert user.email_verified is True


class TestUserTwoFactorAuth:
    """Tests for two-factor authentication"""

    def test_enable_two_factor_verified_email(self):
        """Test enabling 2FA with verified email"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            email_verified=True,
            two_factor_enabled=False
        )
        
        user.enable_two_factor()
        
        assert user.two_factor_enabled is True

    def test_enable_two_factor_unverified_email(self):
        """Test enabling 2FA fails with unverified email"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            email_verified=False,
            two_factor_enabled=False
        )
        
        with pytest.raises(ValueError, match="Email must be verified before enabling 2FA"):
            user.enable_two_factor()

    def test_disable_two_factor(self):
        """Test disabling 2FA"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            two_factor_enabled=True
        )
        
        user.disable_two_factor()
        
        assert user.two_factor_enabled is False

    def test_disable_already_disabled_two_factor(self):
        """Test disabling already disabled 2FA"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            two_factor_enabled=False
        )
        
        user.disable_two_factor()  # Should not cause issues
        
        assert user.two_factor_enabled is False


class TestUserLogin:
    """Tests for login-related functionality"""

    def test_update_last_login(self):
        """Test updating last login timestamp"""
        user = User(
            email="test@example.com", 
            username="testuser", 
            first_name="Test",
            last_name="User",
            last_login=None
        )
        
        before = datetime.now(timezone.utc)
        user.update_last_login()
        after = datetime.now(timezone.utc)
        
        assert user.last_login is not None
        assert before <= user.last_login <= after

    def test_update_last_login_overwrites_previous(self):
        """Test updating last login overwrites previous timestamp"""
        old_time = datetime.now(timezone.utc) - timedelta(hours=1)
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="User", 
            last_login=old_time
        )
        
        user.update_last_login()
        
        assert user.last_login is not None
        assert user.last_login > old_time


class TestUserPasswordManagement:
    """Tests for password management"""

    def test_change_password_valid_hash(self):
        """Test changing password with valid hash"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password_hash="old_hash"
        )
        old_updated_at = user.updated_at
        
        # Wait a bit to ensure timestamp difference
        import time
        time.sleep(0.01)
        
        user.change_password("new_hash")
        
        assert user.password_hash == "new_hash"
        assert user.updated_at > old_updated_at

    def test_change_password_empty_hash(self):
        """Test changing password fails with empty hash"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            password_hash="old_hash"
        )
        
        with pytest.raises(ValueError, match="Password hash cannot be empty"):
            user.change_password("")


class TestUserRoleManagement:
    """Tests for role management"""

    def test_change_role_different_role(self):
        """Test changing to different role"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            role=UserRole.BASIC
        )
        
        user.change_role(UserRole.PREMIUM)
        
        assert user.role == UserRole.PREMIUM

    def test_change_role_same_role(self):
        """Test changing to same role (no-op)"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="User", 
            role=UserRole.BASIC
        )
        
        user.change_role(UserRole.BASIC)  # Should be no-op
        
        assert user.role == UserRole.BASIC


class TestUserProfileManagement:
    """Tests for profile update functionality"""

    def test_update_profile_first_name(self):
        """Test updating first name"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Old",
            last_name="User"
        )
        
        user.update_profile(first_name="New")
        
        assert user.first_name == "New"

    def test_update_profile_last_name(self):
        """Test updating last name"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="Old"
        )
        
        user.update_profile(last_name="New")
        
        assert user.last_name == "New"

    def test_update_profile_currency(self):
        """Test updating preferred currency"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="User", 
            preferred_currency=Currency.USD
        )
        
        user.update_profile(preferred_currency=Currency.EUR)
        
        assert user.preferred_currency == Currency.EUR

    def test_update_profile_multiple_fields(self):
        """Test updating multiple profile fields"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Old",
            last_name="Name",
            preferred_currency=Currency.USD
        )
        
        user.update_profile(
            first_name="New",
            last_name="Updated",
            preferred_currency=Currency.GBP
        )
        
        assert user.first_name == "New"
        assert user.last_name == "Updated"
        assert user.preferred_currency == Currency.GBP

    def test_update_profile_empty_first_name(self):
        """Test updating with empty first name fails"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Valid",
            last_name="User"
        )
        
        with pytest.raises(ValueError, match="First name cannot be empty"):
            user.update_profile(first_name="")

    def test_update_profile_empty_last_name(self):
        """Test updating with empty last name fails"""
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="Valid"
        )
        
        with pytest.raises(ValueError, match="Last name cannot be empty"):
            user.update_profile(last_name="")

    def test_update_profile_none_values_ignored(self):
        """Test None values are ignored in profile update"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="Original",
            last_name="Name",
            preferred_currency=Currency.USD
        )
        
        user.update_profile(
            first_name=None,  # Should be ignored
            last_name="Updated"  # Should be applied
        )
        
        assert user.first_name == "Original"  # Unchanged
        assert user.last_name == "Updated"    # Changed


class TestUserDisplayProperties:
    """Tests for user display properties"""

    def test_full_name_both_names(self):
        """Test full_name with both first and last name"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="John",
            last_name="Doe"
        )
        
        assert user.full_name == "John Doe"

    def test_full_name_first_only(self):
        """Test full_name with only first name"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name="John",
            last_name=" "
        )
        
        assert user.full_name.strip() == "John"

    def test_full_name_last_only(self):
        """Test full_name with only last name"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name=" ",
            last_name="Doe"
        )
        
        assert user.full_name.strip() == "Doe"

    def test_full_name_empty(self):
        """Test full_name with empty names"""
        user = User(
            email="test@example.com",
            username="testuser",
            first_name=" ",
            last_name=" "
        )
        
        assert user.full_name.strip() == ""

    def test_display_name_with_full_name(self):
        """Test display_name returns full name when available"""
        user = User(
            email="test@example.com",
            username="johndoe",
            first_name="John",
            last_name="Doe"
        )
        
        assert user.display_name == "John Doe"

    def test_display_name_fallback_to_username(self):
        """Test display_name falls back to username when no names"""
        user = User(
            email="test@example.com",
            username="johndoe",
            first_name=" ",
            last_name=" "
        )
        
        assert user.display_name == "johndoe"


class TestUserStringRepresentation:
    """Tests for string representation methods"""

    def test_str_representation(self):
        """Test __str__ method"""
        user = User(
            username="johndoe",
            email="john@example.com",
            first_name="John",
            last_name="Doe"
        )
        
        str_repr = str(user)
        
        assert "johndoe" in str_repr
        assert "john@example.com" in str_repr
        assert "John Doe" in str_repr

    def test_repr_representation(self):
        """Test __repr__ method"""
        user = User(
            username="johndoe",
            email="john@example.com",
            first_name="John",
            last_name="Doe",
            role=UserRole.PREMIUM
        )
        
        repr_str = repr(user)
        
        assert "User(" in repr_str
        assert "username='johndoe'" in repr_str
        assert "email='john@example.com'" in repr_str
        assert "role='premium'" in repr_str
        assert str(user.id) in repr_str


class TestUserDomainEventsIntegration:
    """Tests for domain events integration"""

    def test_aggregate_root_inheritance(self):
        """Test User inherits from AggregateRoot"""
        from boursa_vision.domain.entities.base import AggregateRoot
        
        user = User(
            email="test@example.com", 
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        assert isinstance(user, AggregateRoot)
        assert hasattr(user, '_domain_events')
        assert hasattr(user, 'get_domain_events')
        assert hasattr(user, 'clear_domain_events')

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
            username="jose_garcia",
            first_name="José",
            last_name="García"
        )
        
        assert user.full_name == "José García"
        assert "José García" in str(user)

    def test_user_with_very_long_names(self):
        """Test user with very long names"""
        long_name = "A" * 100
        user = User(
            email="test@example.com",
            first_name=long_name,
            last_name=long_name,
            username="longname"
        )
        
        assert user.first_name == long_name
        assert user.last_name == long_name
        assert user.full_name == f"{long_name} {long_name}"

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
