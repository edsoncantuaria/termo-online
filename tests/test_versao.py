from nucleo.versao import ROTULO, VERSAO, InfoVersao


def test_versao_producao_v1():
    assert VERSAO == "1.0.0"
    assert ROTULO == "v1.0"
    assert InfoVersao() == {"versao": "1.0.0", "rotulo": "v1.0"}
