"""Tests del control de acceso por chat_id (allowlist)."""
import auth


def test_allowlist_vacia_deja_pasar_a_todos():
    # Sin variables configuradas: bot ABIERTO (dev/demo), todos pasan.
    allow = auth.load_allowlist(env={})
    assert allow == set()
    assert auth.is_allowed("123", allow) is True
    assert auth.is_allowed(999, allow) is True


def test_allowlist_configurada_solo_deja_a_los_autorizados():
    allow = auth.load_allowlist(env={"ADMIN_CHAT_ID": "111", "BODEGA_CHAT_ID": "222"})
    assert allow == {"111", "222"}
    assert auth.is_allowed("111", allow) is True
    assert auth.is_allowed(222, allow) is True          # acepta int o str
    assert auth.is_allowed("333", allow) is False        # ajeno: denegado


def test_allowlist_admite_lista_separada_por_comas_y_espacios():
    allow = auth.load_allowlist(
        env={"TELEGRAM_ALLOWED_CHAT_IDS": " 10 , 20 ,", "ADMIN_CHAT_ID": ""}
    )
    assert allow == {"10", "20"}  # vacios ignorados, espacios recortados


def test_describe_avisa_cuando_esta_abierto():
    assert "ABIERTO" in auth.describe(set())
    assert "RESTRINGIDO" in auth.describe({"111"})
