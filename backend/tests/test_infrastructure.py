import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.logging import StructuredLogger
from infrastructure.monitoring import APIMonitor
from infrastructure.health_checks import HealthCheckService
from infrastructure.cache import CacheService
from infrastructure.security import SecurityService

def test_logging():
    logger = StructuredLogger("test")
    assert logger.logger.name == "test"
    
def test_metrics():
    monitor = APIMonitor()
    monitor.log_request(150, 20)
    assert monitor.metrics.token_usage == 20
    assert len(monitor.metrics.latency_ms) == 1

def test_health_checks():
    health = HealthCheckService()
    status = health.get_system_status()
    assert status["status"] == "healthy"
    
def test_cache():
    cache = CacheService()
    cache.set("key1", "val1")
    assert cache.get("key1") == "val1"
    
def test_security():
    sec = SecurityService()
    assert sec.rate_limit("user1") == True
    assert sec.mask_phi("Here is the patient data") == "MASKED_DATA"
