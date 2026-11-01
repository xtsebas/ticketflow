import pytest

from app.api.dependencies import usuario_actual
from app.main import app


@pytest.fixture(autouse=True)
def sesion_agente():
    app.dependency_overrides[usuario_actual] = lambda: "soporte1"
    yield
    app.dependency_overrides.pop(usuario_actual, None)
