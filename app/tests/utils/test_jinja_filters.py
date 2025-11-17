import pytest
from flask import Flask
from app.utils.filters import register_filters


@pytest.fixture
def app_with_filters():
    app = Flask(__name__)

    # Definisco un endpoint fittizio per test
    @app.route("/test")
    def test_route():
        return "Test"

    register_filters(app)
    return app


def test_has_endpoint_filter_registered(app_with_filters):
    assert "has_endpoint" in app_with_filters.jinja_env.filters


def test_has_endpoint_existing_and_nonexisting(app_with_filters):
    has_endpoint = app_with_filters.jinja_env.filters["has_endpoint"]

    # Endpoint esistente
    assert has_endpoint("test_route") is True

    # Endpoint inesistente
    assert has_endpoint("nonexistent") is False


def test_has_endpoint_handles_runtime_error(monkeypatch, app_with_filters):
    def fake_iter_rules():
        raise RuntimeError("Simulated runtime error")

    monkeypatch.setattr(app_with_filters.url_map, "iter_rules", fake_iter_rules)

    has_endpoint = app_with_filters.jinja_env.filters["has_endpoint"]

    # Dovrebbe catturare RuntimeError e tornare False
    assert has_endpoint("any_endpoint") is False


def test_template_rendering_with_has_endpoint(app_with_filters):
    with app_with_filters.app_context():
        template = (
            "{{ 'test_route' | has_endpoint }} {{ 'nonexistent' | has_endpoint }}"
        )
        rendered = app_with_filters.jinja_env.from_string(template).render()
        assert "True" in rendered
        assert "False" in rendered
