"""
Tests for Cache Strategy Implementation
======================================

Tests complets pour le système de cache Redis avec stratégies adaptatives.
Couvre :
- DataFrequency enum
- CacheConfig dataclass
- CacheStrategy ABC et AdaptiveCacheStrategy
- RedisCache avec connection pooling
- CacheKeyBuilder avec pattern Builder
"""

import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

# Import du module à tester
from boursa_vision.infrastructure.external.cache_strategy import (
    AdaptiveCacheStrategy,
    CacheConfig,
    CacheKeyBuilder,
    CacheStrategy,
    DataFrequency,
    RedisCache,
)


@pytest.mark.unit
class TestDataFrequency:
    """Tests pour l'énumération DataFrequency"""

    def test_data_frequency_values(self):
        """Test des valeurs de l'énumération"""
        assert DataFrequency.REAL_TIME.value == "real_time"
        assert DataFrequency.INTRADAY.value == "intraday"
        assert DataFrequency.DAILY.value == "daily"
        assert DataFrequency.WEEKLY.value == "weekly"
        assert DataFrequency.MONTHLY.value == "monthly"

    def test_data_frequency_membership(self):
        """Test d'appartenance à l'énumération"""
        all_frequencies = list(DataFrequency)

        assert DataFrequency.REAL_TIME in all_frequencies
        assert DataFrequency.INTRADAY in all_frequencies
        assert DataFrequency.DAILY in all_frequencies
        assert DataFrequency.WEEKLY in all_frequencies
        assert DataFrequency.MONTHLY in all_frequencies

        assert len(all_frequencies) == 5

    def test_data_frequency_string_representation(self):
        """Test de la représentation string"""
        assert str(DataFrequency.REAL_TIME) == "DataFrequency.REAL_TIME"
        assert repr(DataFrequency.DAILY) == "<DataFrequency.DAILY: 'daily'>"

    def test_data_frequency_comparison(self):
        """Test de comparaison des énumérations"""
        freq1 = DataFrequency.REAL_TIME
        freq2 = DataFrequency.REAL_TIME
        freq3 = DataFrequency.DAILY

        assert freq1 == freq2
        assert freq1 != freq3
        assert freq1 is freq2


@pytest.mark.unit
class TestCacheConfig:
    """Tests pour la configuration du cache"""

    def test_cache_config_default_values(self):
        """Test des valeurs par défaut"""
        config = CacheConfig()

        assert config.host == "localhost"
        assert config.port == 6379
        assert config.db == 0
        assert config.password is None
        assert abs(config.socket_timeout - 5.0) < 0.001
        assert abs(config.socket_connect_timeout - 5.0) < 0.001
        assert config.health_check_interval == 30
        assert config.max_connections == 10
        assert config.key_prefix == "boursa_vision:"

    def test_cache_config_ttl_settings_default(self):
        """Test des paramètres TTL par défaut"""
        config = CacheConfig()

        expected_ttl = {
            "real_time": 30,
            "intraday": 300,
            "daily": 3600,
            "weekly": 21600,
            "monthly": 86400,
        }

        assert config.ttl_settings == expected_ttl
        assert config.ttl_settings["real_time"] == 30
        assert config.ttl_settings["intraday"] == 300
        assert config.ttl_settings["daily"] == 3600

    def test_cache_config_custom_values(self):
        """Test avec des valeurs personnalisées"""
        custom_ttl = {
            "real_time": 60,
            "intraday": 600,
            "daily": 7200,
            "weekly": 43200,
            "monthly": 172800,
        }

        config = CacheConfig(
            host="redis.example.com",
            port=6380,
            db=1,
            password="secret",
            socket_timeout=10.0,
            ttl_settings=custom_ttl,
            key_prefix="test:",
        )

        assert config.host == "redis.example.com"
        assert config.port == 6380
        assert config.db == 1
        assert config.password == "secret"
        assert abs(config.socket_timeout - 10.0) < 0.001
        assert config.ttl_settings == custom_ttl
        assert config.key_prefix == "test:"

    def test_cache_config_dataclass_features(self):
        """Test des fonctionnalités dataclass"""
        config1 = CacheConfig(host="localhost", port=6379)
        config2 = CacheConfig(host="localhost", port=6379)
        config3 = CacheConfig(host="localhost", port=6380)

        # Test d'égalité
        assert config1 == config2
        assert config1 != config3

        # Test de représentation
        assert "CacheConfig" in str(config1)
        assert "localhost" in str(config1)
        assert "6379" in str(config1)

    def test_cache_config_ttl_settings_mutability(self):
        """Test de mutabilité des paramètres TTL"""
        config = CacheConfig()
        original_real_time = config.ttl_settings["real_time"]

        # Modifier la valeur
        config.ttl_settings["real_time"] = 60
        assert config.ttl_settings["real_time"] == 60
        assert config.ttl_settings["real_time"] != original_real_time


@pytest.mark.unit
class TestAdaptiveCacheStrategy:
    """Tests pour la stratégie de cache adaptative"""

    def test_adaptive_cache_strategy_initialization(self):
        """Test d'initialisation de la stratégie adaptative"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        assert strategy.config == config
        assert abs(strategy._market_hours_ttl_multiplier - 0.5) < 0.001

    def test_get_ttl_outside_market_hours(self):
        """Test du TTL en dehors des heures de marché"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch.object(strategy, "_is_market_hours", return_value=False):
            # Test pour chaque fréquence
            assert strategy.get_ttl(DataFrequency.REAL_TIME) == 30
            assert strategy.get_ttl(DataFrequency.INTRADAY) == 300
            assert strategy.get_ttl(DataFrequency.DAILY) == 3600
            assert strategy.get_ttl(DataFrequency.WEEKLY) == 21600
            assert strategy.get_ttl(DataFrequency.MONTHLY) == 86400

    def test_get_ttl_during_market_hours(self):
        """Test du TTL pendant les heures de marché"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch.object(strategy, "_is_market_hours", return_value=True):
            # TTL devrait être réduit de moitié
            assert strategy.get_ttl(DataFrequency.REAL_TIME) == 15  # 30 * 0.5
            assert strategy.get_ttl(DataFrequency.INTRADAY) == 150  # 300 * 0.5
            assert strategy.get_ttl(DataFrequency.DAILY) == 1800  # 3600 * 0.5

    def test_get_ttl_with_custom_config(self):
        """Test du TTL avec configuration personnalisée"""
        custom_ttl = {
            "real_time": 60,
            "intraday": 600,
            "daily": 7200,
            "weekly": 43200,
            "monthly": 172800,
        }
        config = CacheConfig(ttl_settings=custom_ttl)
        strategy = AdaptiveCacheStrategy(config)

        with patch.object(strategy, "_is_market_hours", return_value=False):
            assert strategy.get_ttl(DataFrequency.REAL_TIME) == 60
            assert strategy.get_ttl(DataFrequency.INTRADAY) == 600
            assert strategy.get_ttl(DataFrequency.DAILY) == 7200

    def test_should_cache_valid_data(self):
        """Test de validation des données à mettre en cache"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        # Données valides
        assert strategy.should_cache("valid string") is True
        assert strategy.should_cache(42) is True
        assert strategy.should_cache([1, 2, 3]) is True
        assert strategy.should_cache({"key": "value"}) is True
        assert strategy.should_cache(True) is True

    def test_should_cache_invalid_data(self):
        """Test avec données invalides"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        # Données invalides
        assert strategy.should_cache(None) is False
        assert strategy.should_cache([]) is False
        assert strategy.should_cache({}) is False

    @patch("boursa_vision.infrastructure.external.cache_strategy.datetime")
    def test_is_market_hours_weekday_market_time(self, mock_datetime):
        """Test pendant les heures de marché en semaine"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        # Lundi 10h (jour de semaine, heures de marché)
        mock_now = Mock()
        mock_now.weekday.return_value = 0  # Lundi
        mock_now.hour = 10
        mock_datetime.now.return_value = mock_now

        assert strategy._is_market_hours() is True

    @patch("boursa_vision.infrastructure.external.cache_strategy.datetime")
    def test_is_market_hours_weekday_outside_hours(self, mock_datetime):
        """Test en dehors des heures de marché en semaine"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        # Lundi 8h (avant ouverture)
        mock_now = Mock()
        mock_now.weekday.return_value = 0  # Lundi
        mock_now.hour = 8
        mock_datetime.now.return_value = mock_now

        assert strategy._is_market_hours() is False

        # Lundi 18h (après fermeture)
        mock_now.hour = 18
        assert strategy._is_market_hours() is False

    @patch("boursa_vision.infrastructure.external.cache_strategy.datetime")
    def test_is_market_hours_weekend(self, mock_datetime):
        """Test pendant le week-end"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        # Samedi
        mock_now = Mock()
        mock_now.weekday.return_value = 5  # Samedi
        mock_now.hour = 10
        mock_datetime.now.return_value = mock_now

        assert strategy._is_market_hours() is False

        # Dimanche
        mock_now.weekday.return_value = 6  # Dimanche
        assert strategy._is_market_hours() is False

    @patch("boursa_vision.infrastructure.external.cache_strategy.datetime")
    def test_is_market_hours_boundary_conditions(self, mock_datetime):
        """Test des conditions limites pour les heures de marché"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        mock_now = Mock()
        mock_now.weekday.return_value = 0  # Lundi
        mock_datetime.now.return_value = mock_now

        # Heure de début (9h)
        mock_now.hour = 9
        assert strategy._is_market_hours() is True

        # Heure de fin (16h)
        mock_now.hour = 16
        assert strategy._is_market_hours() is True

        # Avant l'heure de début (8h)
        mock_now.hour = 8
        assert strategy._is_market_hours() is False

        # Après l'heure de fin (17h)
        mock_now.hour = 17
        assert strategy._is_market_hours() is False


@pytest.mark.unit
class TestRedisCache:
    """Tests pour l'implémentation du cache Redis"""

    def test_redis_cache_initialization_success(self):
        """Test d'initialisation réussie du cache Redis"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch(
            "boursa_vision.infrastructure.external.cache_strategy.redis"
        ) as mock_redis:
            # Mock du pool et de la connexion Redis
            mock_pool = Mock()
            mock_redis_instance = Mock()
            mock_redis.ConnectionPool.return_value = mock_pool
            mock_redis.Redis.return_value = mock_redis_instance

            # Mock ping réussi
            mock_redis_instance.ping.return_value = True

            cache = RedisCache(config, strategy)

            assert cache.config == config
            assert cache.strategy == strategy
            assert cache._pool == mock_pool
            assert cache._redis == mock_redis_instance

            # Vérifier l'appel de ping
            mock_redis_instance.ping.assert_called_once()

    def test_redis_cache_initialization_failure(self):
        """Test d'échec d'initialisation du cache Redis"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch(
            "boursa_vision.infrastructure.external.cache_strategy.redis"
        ) as mock_redis:
            from redis.exceptions import RedisError

            # Mock d'une exception Redis lors de l'initialisation
            mock_redis.ConnectionPool.side_effect = RedisError("Connection failed")

            cache = RedisCache(config, strategy)

            assert cache._redis is None

    def test_redis_cache_get_success(self):
        """Test de récupération réussie depuis le cache"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            # Mock Redis instance
            mock_redis = Mock()
            cache._redis = mock_redis

            # Mock des données en cache
            test_data = {"symbol": "AAPL", "price": 150.0}
            mock_redis.get.return_value = json.dumps(test_data)

            result = cache.get("test_key")

            assert result == test_data
            mock_redis.get.assert_called_once_with("boursa_vision:test_key")

    def test_redis_cache_get_not_found(self):
        """Test de récupération avec clé inexistante"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.get.return_value = None

            result = cache.get("nonexistent_key")

            assert result is None

    def test_redis_cache_get_json_decode_error(self):
        """Test avec erreur de décodage JSON"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.get.return_value = "invalid json"

            result = cache.get("test_key")

            assert result is None

    def test_redis_cache_get_no_connection(self):
        """Test de récupération sans connexion Redis"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)
            cache._redis = None

            result = cache.get("test_key")

            assert result is None

    def test_redis_cache_set_success(self):
        """Test de stockage réussi dans le cache"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis

            test_data = {"symbol": "AAPL", "price": 150.0}

            with patch.object(strategy, "should_cache", return_value=True):
                with patch.object(strategy, "get_ttl", return_value=3600):
                    result = cache.set("test_key", test_data, DataFrequency.DAILY)

                    assert result is True
                    mock_redis.setex.assert_called_once_with(
                        "boursa_vision:test_key",
                        3600,
                        json.dumps(test_data, default=str),
                    )

    def test_redis_cache_set_should_not_cache(self):
        """Test avec données qui ne doivent pas être mises en cache"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis

            with patch.object(strategy, "should_cache", return_value=False):
                result = cache.set("test_key", None)

                assert result is False
                mock_redis.setex.assert_not_called()

    def test_redis_cache_set_no_connection(self):
        """Test de stockage sans connexion Redis"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)
            cache._redis = None

            result = cache.set("test_key", {"data": "value"})

            assert result is False

    def test_redis_cache_delete_success(self):
        """Test de suppression réussie"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.delete.return_value = 1  # 1 clé supprimée

            result = cache.delete("test_key")

            assert result is True
            mock_redis.delete.assert_called_once_with("boursa_vision:test_key")

    def test_redis_cache_delete_not_found(self):
        """Test de suppression avec clé inexistante"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.delete.return_value = 0  # 0 clé supprimée

            result = cache.delete("nonexistent_key")

            assert result is False

    def test_redis_cache_exists_true(self):
        """Test de vérification d'existence - clé existe"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.exists.return_value = 1

            result = cache.exists("test_key")

            assert result is True
            mock_redis.exists.assert_called_once_with("boursa_vision:test_key")

    def test_redis_cache_exists_false(self):
        """Test de vérification d'existence - clé n'existe pas"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.exists.return_value = 0

            result = cache.exists("nonexistent_key")

            assert result is False

    def test_redis_cache_get_ttl_success(self):
        """Test de récupération du TTL"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.ttl.return_value = 3600

            result = cache.get_ttl("test_key")

            assert result == 3600
            mock_redis.ttl.assert_called_once_with("boursa_vision:test_key")

    def test_redis_cache_get_ttl_expired(self):
        """Test de récupération du TTL pour clé expirée"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.ttl.return_value = -1  # TTL expiré

            result = cache.get_ttl("test_key")

            assert result is None

    def test_redis_cache_flush_pattern_success(self):
        """Test de suppression par motif"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.keys.return_value = ["key1", "key2", "key3"]
            mock_redis.delete.return_value = 3

            result = cache.flush_pattern("test_*")

            assert result == 3
            mock_redis.keys.assert_called_once_with("boursa_vision:test_*")
            mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    def test_redis_cache_flush_pattern_no_keys(self):
        """Test de suppression par motif sans correspondance"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.keys.return_value = []

            result = cache.flush_pattern("nonexistent_*")

            assert result == 0
            mock_redis.delete.assert_not_called()

    def test_redis_cache_get_stats_success(self):
        """Test de récupération des statistiques"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis

            mock_info = {
                "used_memory_human": "1.2M",
                "connected_clients": 5,
                "total_commands_processed": 1000,
                "keyspace_hits": 800,
                "keyspace_misses": 200,
            }
            mock_redis.info.return_value = mock_info

            stats = cache.get_stats()

            assert stats["status"] == "connected"
            assert stats["used_memory"] == "1.2M"
            assert stats["connected_clients"] == 5
            assert stats["keyspace_hits"] == 800
            assert stats["keyspace_misses"] == 200
            assert abs(stats["hit_rate"] - 80.0) < 0.001  # 800/(800+200) * 100

    def test_redis_cache_get_stats_disconnected(self):
        """Test de statistiques sans connexion"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)
            cache._redis = None

            stats = cache.get_stats()

            assert stats["status"] == "disconnected"

    def test_redis_cache_calculate_hit_rate(self):
        """Test du calcul du taux de réussite"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            # Test avec hits et misses
            hit_rate = cache._calculate_hit_rate(800, 200)
            assert abs(hit_rate - 80.0) < 0.001

            # Test avec zéro total
            hit_rate = cache._calculate_hit_rate(0, 0)
            assert abs(hit_rate - 0.0) < 0.001

            # Test avec seulement des hits
            hit_rate = cache._calculate_hit_rate(100, 0)
            assert abs(hit_rate - 100.0) < 0.001

    def test_redis_cache_is_healthy_true(self):
        """Test de vérification de santé - OK"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            mock_redis = Mock()
            cache._redis = mock_redis
            mock_redis.ping.return_value = True

            assert cache.is_healthy() is True

    def test_redis_cache_is_healthy_false(self):
        """Test de vérification de santé - KO"""
        config = CacheConfig()
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)
            cache._redis = None

            assert cache.is_healthy() is False

    def test_redis_cache_build_key(self):
        """Test de construction des clés de cache"""
        config = CacheConfig(key_prefix="test_prefix:")
        strategy = AdaptiveCacheStrategy(config)

        with patch("boursa_vision.infrastructure.external.cache_strategy.redis"):
            cache = RedisCache(config, strategy)

            key = cache._build_key("my_key")
            assert key == "test_prefix:my_key"


@pytest.mark.unit
class TestCacheKeyBuilder:
    """Tests pour le constructeur de clés de cache"""

    def test_cache_key_builder_empty_initialization(self):
        """Test d'initialisation vide"""
        builder = CacheKeyBuilder()
        assert builder.parts == []
        assert builder.build() == ""

    def test_cache_key_builder_with_base_key(self):
        """Test d'initialisation avec clé de base"""
        builder = CacheKeyBuilder("base_key")
        assert builder.parts == ["base_key"]
        assert builder.build() == "base_key"

    def test_cache_key_builder_add_symbol(self):
        """Test d'ajout de symbole"""
        builder = CacheKeyBuilder()
        result = builder.add_symbol("AAPL")

        assert result is builder  # Fluent interface
        assert "symbol:AAPL" in builder.parts
        assert builder.build() == "symbol:AAPL"

    def test_cache_key_builder_add_timeframe_with_interval(self):
        """Test d'ajout de timeframe avec intervalle"""
        builder = CacheKeyBuilder()
        builder.add_timeframe("1d", "1m")

        assert "timeframe:1d:1m" in builder.parts
        assert builder.build() == "timeframe:1d:1m"

    def test_cache_key_builder_add_timeframe_without_interval(self):
        """Test d'ajout de timeframe sans intervalle"""
        builder = CacheKeyBuilder()
        builder.add_timeframe("1d")

        assert "timeframe:1d" in builder.parts
        assert builder.build() == "timeframe:1d"

    def test_cache_key_builder_add_data_type(self):
        """Test d'ajout de type de données"""
        builder = CacheKeyBuilder()
        builder.add_data_type("price")

        assert "type:price" in builder.parts
        assert builder.build() == "type:price"

    def test_cache_key_builder_add_date_string(self):
        """Test d'ajout de date sous forme de string"""
        builder = CacheKeyBuilder()
        builder.add_date("2024-01-15")

        assert "date:2024-01-15" in builder.parts
        assert builder.build() == "date:2024-01-15"

    def test_cache_key_builder_add_date_datetime(self):
        """Test d'ajout de date sous forme de datetime"""
        builder = CacheKeyBuilder()
        test_date = datetime(2024, 1, 15, 10, 30, 0)
        builder.add_date(test_date)

        assert "date:2024-01-15" in builder.parts
        assert builder.build() == "date:2024-01-15"

    def test_cache_key_builder_add_custom(self):
        """Test d'ajout de paire clé-valeur personnalisée"""
        builder = CacheKeyBuilder()
        builder.add_custom("indicator", "RSI")

        assert "indicator:RSI" in builder.parts
        assert builder.build() == "indicator:RSI"

    def test_cache_key_builder_fluent_interface(self):
        """Test de l'interface fluide"""
        key = (
            CacheKeyBuilder("base")
            .add_symbol("AAPL")
            .add_timeframe("1d", "1m")
            .add_data_type("price")
            .build()
        )

        expected = "base:symbol:AAPL:timeframe:1d:1m:type:price"
        assert key == expected

    def test_cache_key_builder_reset(self):
        """Test de remise à zéro"""
        builder = CacheKeyBuilder("base")
        builder.add_symbol("AAPL")

        assert len(builder.parts) > 0

        result = builder.reset()
        assert result is builder  # Fluent interface
        assert builder.parts == []
        assert builder.build() == ""

    def test_cache_key_builder_for_price_data_with_interval(self):
        """Test de construction de clé pour données de prix avec intervalle"""
        key = CacheKeyBuilder.for_price_data("AAPL", "1d", "1m")
        expected = "price_data:symbol:AAPL:timeframe:1d:1m"
        assert key == expected

    def test_cache_key_builder_for_price_data_without_interval(self):
        """Test de construction de clé pour données de prix sans intervalle"""
        key = CacheKeyBuilder.for_price_data("AAPL", "1d")
        expected = "price_data:symbol:AAPL:timeframe:1d"
        assert key == expected

    def test_cache_key_builder_for_fundamental_data(self):
        """Test de construction de clé pour données fondamentales"""
        key = CacheKeyBuilder.for_fundamental_data("AAPL")
        expected = "fundamental_data:symbol:AAPL"
        assert key == expected

    def test_cache_key_builder_for_technical_indicators(self):
        """Test de construction de clé pour indicateurs techniques"""
        key = CacheKeyBuilder.for_technical_indicators("AAPL", "RSI", "14d")
        expected = "technical_indicators:symbol:AAPL:indicator:RSI:timeframe:14d"
        assert key == expected

    def test_cache_key_builder_complex_key(self):
        """Test de construction de clé complexe"""
        builder = CacheKeyBuilder("market_data")
        key = (
            builder.add_symbol("GOOGL")
            .add_timeframe("1w", "1h")
            .add_data_type("ohlcv")
            .add_date("2024-01-15")
            .add_custom("exchange", "NASDAQ")
            .build()
        )

        expected = "market_data:symbol:GOOGL:timeframe:1w:1h:type:ohlcv:date:2024-01-15:exchange:NASDAQ"
        assert key == expected

    def test_cache_key_builder_empty_parts_handling(self):
        """Test de gestion des parties vides"""
        builder = CacheKeyBuilder("")
        key = builder.build()
        assert key == ""

        builder = CacheKeyBuilder()
        builder.parts = ["", "valid_part", ""]
        key = builder.build()
        assert key == ":valid_part:"  # Garde les parties vides

    def test_cache_key_builder_special_characters(self):
        """Test avec caractères spéciaux"""
        builder = CacheKeyBuilder()
        key = builder.add_symbol("BRK.A").add_custom("exchange", "NYSE:ARCA").build()

        expected = "symbol:BRK.A:exchange:NYSE:ARCA"
        assert key == expected
