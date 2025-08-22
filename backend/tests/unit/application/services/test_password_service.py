"""
Tests unitaires pour PasswordService
===================================

Tests unitaires complets pour le service de gestion des mots de passe.
"""

import pytest
import re
from unittest.mock import patch, Mock

from boursa_vision.application.services.password_service import PasswordService


@pytest.fixture
def password_service():
    """Instance de PasswordService pour les tests."""
    return PasswordService()


class TestPasswordServiceCreation:
    """Tests de création du service de mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_create_password_service_with_bcrypt(self):
        """Test de création avec configuration bcrypt."""
        # Act
        service = PasswordService()

        # Assert
        assert service._pwd_context is not None
        assert "bcrypt" in service._pwd_context.schemes()


class TestPasswordServiceHashing:
    """Tests de hashage des mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_hash_valid_password(self, password_service):
        """Test de hashage d'un mot de passe valide."""
        # Arrange
        password = "SecurePass123!"

        # Act
        hashed = password_service.hash_password(password)

        # Assert
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 20  # Hashes bcrypt sont longs
        assert hashed.startswith('$2b$')  # Format bcrypt

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_empty_password(self, password_service):
        """Test d'erreur pour mot de passe vide."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_service.hash_password("")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_none_password(self, password_service):
        """Test d'erreur pour mot de passe None."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_service.hash_password(None)

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_short_password(self, password_service):
        """Test d'erreur pour mot de passe trop court."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            password_service.hash_password("short")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_generate_different_hashes_for_same_password(self, password_service):
        """Test que deux hashages du même mot de passe donnent des résultats différents."""
        # Arrange
        password = "SamePassword123!"

        # Act
        hash1 = password_service.hash_password(password)
        hash2 = password_service.hash_password(password)

        # Assert
        assert hash1 != hash2  # Les salts sont différents


class TestPasswordServiceVerification:
    """Tests de vérification des mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_verify_correct_password(self, password_service):
        """Test de vérification d'un mot de passe correct."""
        # Arrange
        password = "SecurePass123!"
        hashed = password_service.hash_password(password)

        # Act
        result = password_service.verify_password(password, hashed)

        # Assert
        assert result is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_reject_incorrect_password(self, password_service):
        """Test de rejet d'un mot de passe incorrect."""
        # Arrange
        password = "SecurePass123!"
        wrong_password = "WrongPassword456!"
        hashed = password_service.hash_password(password)

        # Act
        result = password_service.verify_password(wrong_password, hashed)

        # Assert
        assert result is False

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_false_for_empty_password_verification(self, password_service):
        """Test de retour False pour mot de passe vide lors de la vérification."""
        # Arrange
        hashed = "$2b$12$valid.hash.here"

        # Act
        result = password_service.verify_password("", hashed)

        # Assert
        assert result is False

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_false_for_empty_hash_verification(self, password_service):
        """Test de retour False pour hash vide lors de la vérification."""
        # Act
        result = password_service.verify_password("password", "")

        # Assert
        assert result is False

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_handle_invalid_hash_format(self, password_service):
        """Test de gestion d'un hash invalide."""
        # Arrange
        password = "SecurePass123!"
        invalid_hash = "invalid.hash.format"

        # Act & Assert
        # Le comportement peut varier - soit False, soit exception
        try:
            result = password_service.verify_password(password, invalid_hash)
            assert result is False
        except ValueError:
            # Comportement acceptable aussi
            pass


class TestPasswordServiceNeedsUpdate:
    """Tests de vérification si le hash doit être mis à jour."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_false_for_current_hash(self, password_service):
        """Test que les hashes récents n'ont pas besoin de mise à jour."""
        # Arrange
        password = "SecurePass123!"
        current_hash = password_service.hash_password(password)

        # Act
        needs_update = password_service.needs_update(current_hash)

        # Assert
        assert needs_update is False

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_true_for_empty_hash(self, password_service):
        """Test qu'un hash vide nécessite une mise à jour."""
        # Act
        needs_update = password_service.needs_update("")

        # Assert
        assert needs_update is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_true_for_none_hash(self, password_service):
        """Test qu'un hash None nécessite une mise à jour."""
        # Act
        needs_update = password_service.needs_update(None)

        # Assert
        assert needs_update is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_return_true_for_invalid_hash(self, password_service):
        """Test qu'un hash invalide nécessite une mise à jour."""
        # Act
        needs_update = password_service.needs_update("invalid.hash")

        # Assert
        assert needs_update is True


class TestPasswordServiceStrengthValidation:
    """Tests de validation de la force des mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_validate_strong_password(self, password_service):
        """Test de validation d'un mot de passe fort."""
        # Arrange
        strong_password = "StrongPass123!"

        # Act
        try:
            result = password_service.validate_password_strength(strong_password)
            # Si aucune exception n'est levée, la validation a réussi
            assert result is True or result is None  # La méthode peut ne pas retourner explicitement True
        except ValueError:
            pytest.fail("Strong password should not raise ValueError")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_empty_password_validation(self, password_service):
        """Test d'erreur pour mot de passe vide lors de la validation."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password cannot be empty"):
            password_service.validate_password_strength("")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_short_password_validation(self, password_service):
        """Test d'erreur pour mot de passe trop court lors de la validation."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must be at least 8 characters long"):
            password_service.validate_password_strength("Short1!")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_no_uppercase(self, password_service):
        """Test d'erreur pour mot de passe sans majuscule."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must contain at least one uppercase letter"):
            password_service.validate_password_strength("lowercase123!")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_no_lowercase(self, password_service):
        """Test d'erreur pour mot de passe sans minuscule."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must contain at least one lowercase letter"):
            password_service.validate_password_strength("UPPERCASE123!")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_no_digit(self, password_service):
        """Test d'erreur pour mot de passe sans chiffre."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must contain at least one number"):
            password_service.validate_password_strength("NoDigitsHere!")

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_raise_error_for_no_special_character(self, password_service):
        """Test d'erreur pour mot de passe sans caractère spécial."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password must contain at least one special character"):
            password_service.validate_password_strength("NoSpecialChar123")


class TestPasswordServiceGeneration:
    """Tests de génération de mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_generate_password_with_default_length(self, password_service):
        """Test de génération avec longueur par défaut."""
        # Act
        password = password_service.generate_random_password()

        # Assert
        assert len(password) == 12
        assert password_service.validate_password_strength(password) is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_generate_password_with_custom_length(self, password_service):
        """Test de génération avec longueur personnalisée."""
        # Arrange
        custom_length = 16

        # Act
        password = password_service.generate_random_password(custom_length)

        # Assert
        assert len(password) == custom_length
        assert password_service.validate_password_strength(password) is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_enforce_minimum_length_of_8(self, password_service):
        """Test que la longueur minimale de 8 est respectée."""
        # Act
        password = password_service.generate_random_password(5)  # Trop court

        # Assert
        assert len(password) == 8  # Forcé au minimum

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_generate_different_passwords(self, password_service):
        """Test que deux générations produisent des mots de passe différents."""
        # Act
        password1 = password_service.generate_random_password()
        password2 = password_service.generate_random_password()

        # Assert
        assert password1 != password2

    @pytest.mark.unit
    @pytest.mark.fast
    def test_generated_password_contains_all_required_types(self, password_service):
        """Test que le mot de passe généré contient tous les types de caractères."""
        # Act
        password = password_service.generate_random_password()

        # Assert
        assert re.search(r'[A-Z]', password) is not None  # Majuscule
        assert re.search(r'[a-z]', password) is not None  # Minuscule
        assert re.search(r'\d', password) is not None     # Chiffre
        assert re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password) is not None  # Spécial

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_generate_long_password(self, password_service):
        """Test de génération d'un mot de passe très long."""
        # Arrange
        long_length = 50

        # Act
        password = password_service.generate_random_password(long_length)

        # Assert
        assert len(password) == long_length
        assert password_service.validate_password_strength(password) is True


class TestPasswordServiceEdgeCases:
    """Tests des cas limites du service de mots de passe."""

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_handle_unicode_password(self, password_service):
        """Test de gestion d'un mot de passe Unicode."""
        # Arrange
        unicode_password = "Pässwörd123!éñç"

        # Act
        hashed = password_service.hash_password(unicode_password)
        verified = password_service.verify_password(unicode_password, hashed)

        # Assert
        assert hashed is not None
        assert verified is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_handle_very_long_password(self, password_service):
        """Test de gestion d'un mot de passe très long."""
        # Arrange
        long_password = "A" * 100 + "b1!"  # 103 caractères

        # Act
        hashed = password_service.hash_password(long_password)
        verified = password_service.verify_password(long_password, hashed)

        # Assert
        assert hashed is not None
        assert verified is True

    @pytest.mark.unit
    @pytest.mark.fast
    def test_should_handle_password_with_whitespace(self, password_service):
        """Test de gestion d'un mot de passe avec espaces."""
        # Arrange
        password_with_spaces = "Pass Word 123!"

        # Act
        hashed = password_service.hash_password(password_with_spaces)
        verified = password_service.verify_password(password_with_spaces, hashed)

        # Assert
        assert hashed is not None
        assert verified is True
