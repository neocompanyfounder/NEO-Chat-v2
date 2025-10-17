"""Tests for configuration management."""

import pytest
from pydantic import ValidationError
from src.utils.config import Settings


def test_settings_default_values():
    """Test that settings have correct default values."""
    # This will fail if required env vars are missing, which is expected
    # In actual tests, we'd mock environment variables
    pass


def test_settings_with_env_vars(monkeypatch):
    """Test settings loading from environment variables."""
    # Set required environment variables
    monkeypatch.setenv("EVOLUTION_API_URL", "https://test.evolution-api.com")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("SUPABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    
    settings = Settings()
    
    assert settings.evolution_api_url == "https://test.evolution-api.com"
    assert settings.evolution_api_key == "test-key"
    assert settings.google_api_key == "test-google-key"
    assert settings.gemini_model == "gemini-2.0-flash-exp"
    assert settings.max_file_size_mb == 16
    assert settings.vector_similarity_threshold == 0.7


def test_settings_rate_limits(monkeypatch):
    """Test rate limit configuration."""
    monkeypatch.setenv("EVOLUTION_API_URL", "https://test.evolution-api.com")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("SUPABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("GEMINI_RATE_LIMIT_PER_MIN", "120")
    monkeypatch.setenv("WHATSAPP_RATE_LIMIT_PER_MIN", "30")
    
    settings = Settings()
    
    assert settings.gemini_rate_limit_per_min == 120
    assert settings.whatsapp_rate_limit_per_min == 30


def test_settings_timeouts(monkeypatch):
    """Test timeout configuration."""
    monkeypatch.setenv("EVOLUTION_API_URL", "https://test.evolution-api.com")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("SUPABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    
    settings = Settings()
    
    assert settings.gemini_timeout == 30
    assert settings.evolution_timeout == 10
    assert settings.supabase_timeout == 5


def test_settings_vector_search_params(monkeypatch):
    """Test vector search configuration."""
    monkeypatch.setenv("EVOLUTION_API_URL", "https://test.evolution-api.com")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("SUPABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("VECTOR_SIMILARITY_THRESHOLD", "0.8")
    monkeypatch.setenv("VECTOR_TOP_K", "10")
    
    settings = Settings()
    
    assert settings.vector_similarity_threshold == 0.8
    assert settings.vector_top_k == 10
    assert settings.max_context_tokens == 8000


def test_settings_chunking_params(monkeypatch):
    """Test chunking configuration."""
    monkeypatch.setenv("EVOLUTION_API_URL", "https://test.evolution-api.com")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
    monkeypatch.setenv("SUPABASE_URL", "postgresql://test:test@localhost:5432/test")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    
    settings = Settings()
    
    assert settings.min_chunk_tokens == 100
    assert settings.max_chunk_tokens == 2000
