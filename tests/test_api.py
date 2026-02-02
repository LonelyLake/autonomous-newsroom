"""
Testy dla API FastAPI (src/main.py).
Testują endpointy HTTP bez wywoływania prawdziwego LLM.
"""

import pytest
from unittest.mock import patch, AsyncMock


class TestHealthEndpoint:
    """Testy endpointu /health."""
    
    def test_health_check(self, test_client):
        """Test podstawowego health check."""
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestApiInfoEndpoint:
    """Testy endpointu /api."""
    
    def test_api_info(self, test_client):
        """Test informacji o API."""
        response = test_client.get("/api")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data


class TestRootEndpoint:
    """Testy endpointu / (HTML)."""
    
    def test_root_returns_html(self, test_client):
        """Test że root zwraca HTML."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Autonomous Newsroom" in response.text


class TestStartCycleEndpoint:
    """Testy endpointu POST /start-cycle."""
    
    def test_start_cycle_valid_request(self, test_client):
        """Test poprawnego żądania start-cycle."""
        response = test_client.post(
            "/start-cycle",
            json={"topic": "AI w medycynie", "max_iterations": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["topic"] == "AI w medycynie"
        assert data["max_iterations"] == 2
    
    def test_start_cycle_default_iterations(self, test_client):
        """Test domyślnej liczby iteracji."""
        response = test_client.post(
            "/start-cycle",
            json={"topic": "Test topic"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["max_iterations"] == 2  # Domyślna wartość
    
    def test_start_cycle_missing_topic(self, test_client):
        """Test braku wymaganego pola topic."""
        response = test_client.post(
            "/start-cycle",
            json={}
        )
        
        assert response.status_code == 422  # Validation Error
    
    def test_start_cycle_empty_topic(self, test_client):
        """Test pustego tematu."""
        response = test_client.post(
            "/start-cycle",
            json={"topic": ""}
        )
        
        # FastAPI/Pydantic może zaakceptować pusty string
        # ale to zależy od walidacji w modelu
        assert response.status_code in [200, 422]


class TestLastResultEndpoint:
    """Testy endpointu GET /last-result."""
    
    def test_last_result_no_result(self, test_client):
        """Test gdy nie ma jeszcze wyników."""
        # Resetujemy stan (importujemy i ustawiamy _last_result = None)
        import src.main as main_module
        main_module._last_result = None
        
        response = test_client.get("/last-result")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "no_result"
    
    def test_last_result_with_result(self, test_client):
        """Test gdy jest wynik."""
        import src.main as main_module
        
        # Ustawiamy przykładowy wynik
        main_module._last_result = {
            "status": "success",
            "topic": "Test topic",
            "iterations": 1,
            "article": {
                "title": "Test Article",
                "lead": "Test lead",
                "body": "Test body content",
                "tags": ["test"],
                "word_count": 10
            }
        }
        
        response = test_client.get("/last-result")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["topic"] == "Test topic"
        assert "article" in data


class TestLogsEndpoint:
    """Testy endpointu GET /logs."""
    
    def test_logs_default(self, test_client):
        """Test pobierania logów z domyślną liczbą linii."""
        response = test_client.get("/logs")
        
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
    
    def test_logs_with_lines_param(self, test_client):
        """Test pobierania logów z parametrem lines."""
        response = test_client.get("/logs?lines=10")
        
        assert response.status_code == 200


class TestStaticFiles:
    """Testy serwowania plików statycznych."""
    
    def test_css_file(self, test_client):
        """Test dostępności pliku CSS."""
        response = test_client.get("/static/style.css")
        
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
    
    def test_js_file(self, test_client):
        """Test dostępności pliku JavaScript."""
        response = test_client.get("/static/app.js")
        
        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
    
    def test_nonexistent_static_file(self, test_client):
        """Test nieistniejącego pliku statycznego."""
        response = test_client.get("/static/nonexistent.xyz")
        
        assert response.status_code == 404


class TestSwaggerDocs:
    """Testy dokumentacji Swagger."""
    
    def test_openapi_json(self, test_client):
        """Test dostępności schematu OpenAPI."""
        response = test_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_docs_endpoint(self, test_client):
        """Test dostępności Swagger UI."""
        response = test_client.get("/docs")
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
