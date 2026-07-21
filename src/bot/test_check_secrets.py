"""Tests de la guarda de secretos de produccion (scripts/check_secrets.py)."""
import pathlib
import sys

# El modulo vive en scripts/ (lo usa deploy.sh); lo importamos para testear su logica.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts"))
import check_secrets  # noqa: E402


def test_placeholder_por_defecto_falla():
    problemas = check_secrets.validate(
        {"JWT_SECRET": "cambia-esto-en-produccion", "COOKIE_SECRET": "algo-fuerte-abc123"}
    )
    assert any("JWT_SECRET" in p for p in problemas)
    assert not any("COOKIE_SECRET" in p for p in problemas)


def test_vacio_falla():
    problemas = check_secrets.validate({"JWT_SECRET": "", "COOKIE_SECRET": "x"})
    assert any("JWT_SECRET" in p and "vacio" in p for p in problemas)


def test_ausente_falla():
    problemas = check_secrets.validate({})  # ninguno presente
    assert len(problemas) == 2


def test_secretos_fuertes_pasan():
    problemas = check_secrets.validate(
        {"JWT_SECRET": "9f3ac1b7d2e4", "COOKIE_SECRET": "7b21e0aa5c9f"}
    )
    assert problemas == []


def test_load_env_file_inexistente_devuelve_none():
    assert check_secrets.load_env_file("/no/existe/.env") is None
