"""Tests de la clasificacion best-effort de pendientes (data/clasificar_pendientes.py).

Logica pura (offline): no toca Medusa ni la red. Verifica que las reglas asignan lo
esperado y que lo genuinamente ambiguo queda 'revisar' (no se fuerza un tipo).
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "data"))
import clasificar_pendientes as cp  # noqa: E402


def test_reglas_de_alta_confianza():
    tipo, conf, _ = cp.clasificar_pendiente("Espaciador alum colores", "6-CL")
    assert tipo == "Manubrios y potencias" and conf == "alta"
    tipo, conf, _ = cp.clasificar_pendiente("Paral lateral graduacion mtb", "6-CL")
    assert tipo == "Soportes y portacelular" and conf == "alta"


def test_pitillos_por_codigo_interno_aunque_el_nombre_sea_un_color():
    # "1 Gris" no dice 'pitillo', pero su codigo interno es PITILLOS.
    tipo, conf, _ = cp.clasificar_pendiente("1 Gris", "PITILLOS")
    assert tipo == "Llantas, rines y aros" and conf == "baja"


def test_reglas_de_confianza_media_y_baja():
    assert cp.clasificar_pendiente("Tornillos lujo alum colores", "6-CL")[0] == "Kits y herramientas"
    assert cp.clasificar_pendiente("Abrazadera alum 35mm Dor", "3-RR")[0] == "Sillines y tijas"


def test_ambiguos_quedan_a_revisar_sin_forzar_tipo():
    for nombre in ("Tapabocas antipolucion", "Llavero bici antiguo",
                   "Bicicleta mini exhibicion con reloj", "Accesorio para instalacion multiproposito"):
        tipo, conf, _ = cp.clasificar_pendiente(nombre, "6-CL")
        assert tipo is None and conf == "revisar", f"{nombre} no debe forzarse a un tipo"


def test_norm_quita_acentos_y_baja():
    assert cp.norm("EspaccióN") == "espaccion"
