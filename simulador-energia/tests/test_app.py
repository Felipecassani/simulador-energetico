"""Testes do site (sem browser, via AppTest).

1. Cada página abre sem rebentar.
2. O site é para qualquer pessoa: nenhuma página mostra fórmulas, blocos de
   código ou texto de desenvolvimento. Isso fica no guia PDF (docs/).
"""
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PASTA = Path(__file__).resolve().parents[1]
PAGINAS = sorted(p.relative_to(PASTA).as_posix()
                 for p in (PASTA / "paginas").rglob("*.py") if not p.name.startswith("._"))

# Marcas de código (maiúsculas exatas: "todo" também é palavra portuguesa)
MARCAS_DE_CODIGO = ["TODO(", "NotImplementedError", "<sub>", "nucleo/", "pytest",
                    "```", ".py", "()", "$", "\\", "Implementa o passo", "Claude"]
# Frases de desenvolvimento (sem distinguir maiúsculas)
FRASES_TECNICAS = ["por implementar", "caso de validação", "conta à mão", "equaç"]

# Tudo o que o visitante pode ler: texto, avisos, rótulos e ajudas dos campos, ligações
TIPOS_VISIVEIS = ["markdown", "caption", "subheader", "title", "header", "text",
                  "info", "warning", "error", "success", "toast", "exception",
                  "metric", "expander", "html", "page_link",
                  "number_input", "text_input", "text_area", "selectbox", "multiselect",
                  "slider", "select_slider", "radio", "checkbox", "toggle", "button",
                  "date_input", "time_input", "tabs"]
CAMPOS = ("body", "label", "help", "value", "text", "placeholder")


def _abrir(pagina, monkeypatch):
    monkeypatch.chdir(PASTA)
    app = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    app.run()
    app.switch_page(pagina).run()
    return app


def _texto_visivel(app):
    partes = []
    for tipo in TIPOS_VISIVEIS:
        for elemento in app.get(tipo):
            proto = getattr(elemento, "proto", None)
            for campo in CAMPOS:
                valor = getattr(proto, campo, None) if proto is not None else None
                if isinstance(valor, str) and valor:
                    # o CSS do tema não é texto visível (e tem parênteses de var(...))
                    partes.append(re.sub(r"<(style|script)>.*?</\1>", "", valor, flags=re.S))
    return "\n".join(partes)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_pagina_abre_sem_erros(pagina, monkeypatch):
    app = _abrir(pagina, monkeypatch)
    assert not app.exception, app.exception


@pytest.mark.parametrize("pagina", PAGINAS)
def test_site_sem_conteudo_tecnico(pagina, monkeypatch):
    app = _abrir(pagina, monkeypatch)
    assert not app.get("latex"), "fórmulas LaTeX no site"
    assert not app.get("code"), "blocos de código no site"
    texto = _texto_visivel(app)
    assert texto, "não foi possível ler o texto da página"
    encontradas = ([m for m in MARCAS_DE_CODIGO if m in texto]
                   + [f for f in FRASES_TECNICAS if f in texto.lower()])
    assert not encontradas, f"texto técnico no site: {encontradas}"


# ---------- com dados do mercado (OMIE simulado com o ficheiro real de tests/dados) ----------

@pytest.fixture
def omie_simulado(monkeypatch):
    import streamlit as st

    from nucleo import mercado

    bruto = (PASTA / "tests" / "dados" / "marginalpdbcpt_20260930.1").read_bytes()

    def falso(url, tempo=None):
        if "omie" in url:
            return bruto
        raise mercado.SemRede("só o OMIE está simulado")

    monkeypatch.setenv("SIMULADOR_OFFLINE", "0")
    monkeypatch.setattr(mercado, "_descarregar", falso)
    st.cache_data.clear()
    yield
    st.cache_data.clear()


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_com_mercado_sem_erros_nem_conteudo_tecnico(pagina, monkeypatch, omie_simulado):
    app = _abrir(pagina, monkeypatch)
    assert not app.exception, app.exception
    texto = _texto_visivel(app)
    encontradas = ([m for m in MARCAS_DE_CODIGO if m in texto]
                   + [f for f in FRASES_TECNICAS if f in texto.lower()])
    assert not encontradas, f"texto técnico no site: {encontradas}"


def test_fatura_mostra_recomendacoes_e_a_comparacao_com_a_erse(monkeypatch, omie_simulado):
    app = _abrir("paginas/fatura.py", monkeypatch)
    texto = _texto_visivel(app)
    assert "Recomendações para ti" in texto and "Na tarifa regulada da ERSE" in texto
    assert "simulador da ERSE" in texto
    assert "As ofertas mais baratas para ti" in texto and "🥇" in texto


def test_o_perfil_passa_da_fatura_para_as_outras_paginas(monkeypatch):
    app = _abrir("paginas/fatura.py", monkeypatch)
    app.number_input(key="f_consumo__0").set_value(258.0).run()
    app.number_input(key="f_dias__0").set_value(31).run()
    app.switch_page("paginas/eficiencia.py").run()
    assert app.number_input(key="e_consumo__0").value == 258.0
    assert app.number_input(key="e_dias__0").value == 31
    app.switch_page("paginas/bi_horario.py").run()
    assert app.number_input(key="b_consumo__0").value == 258.0
    assert not app.exception


def test_opcoes_horarias_com_ponta_no_maximo(monkeypatch):
    app = _abrir("paginas/bi_horario.py", monkeypatch)
    app.slider(key="b_vazio__0").set_value(23.0).run()
    app.slider(key="b_ponta__0").set_value(77.0).run()
    assert not app.exception


def test_fatura_carregada_depois_de_visitar_outra_pagina(monkeypatch):
    """Carregar a fatura (perfil novo + revisão) renova os campos já criados noutras páginas."""
    app = _abrir("paginas/eficiencia.py", monkeypatch)
    assert app.number_input(key="e_consumo__0").value == 300.0
    app.session_state["perfil"] = {**app.session_state["perfil"], "consumo_kwh": 258.0, "dias": 31,
                                   "kva": 4.6, "modalidade": "indexado", "da_fatura": True,
                                   "fonte": "a tua fatura"}
    app.session_state["perfil_rev"] = 1
    app.run()
    assert app.number_input(key="e_consumo__1").value == 258.0
    texto = _texto_visivel(app)
    assert "O MEU TARIFÁRIO" in texto and "Indexado ao mercado" in texto
    assert "Usa as horas mais baratas do mercado" in texto      # dica só para indexados
    app.switch_page("paginas/bi_horario.py").run()
    assert app.number_input(key="b_consumo__1").value == 258.0
    assert not app.exception


def test_fatura_indexada_mostra_perdas_e_margem(monkeypatch, omie_simulado):
    app = _abrir("paginas/fatura.py", monkeypatch)
    app.radio(key="f_modalidade__0").set_value("indexado").run()
    assert app.number_input(key="f_perdas__0").value == 0.0
    assert app.number_input(key="f_margem__0").value == 0.0
    assert "Com o mercado de agora" in _texto_visivel(app)
    assert not app.exception


def test_fatura_com_impostos_e_primeiro_ano(monkeypatch, omie_simulado):
    app = _abrir("paginas/fatura.py", monkeypatch)
    app.toggle(key="f_impostos__0").set_value(True).run()
    texto = _texto_visivel(app)
    assert "Total com IVA" in texto and "Com IVA e taxas." in texto
    app.button_group(key="f_vista_ofertas").set_value("No 1.º ano").run() if hasattr(app, "button_group") else None
    assert not app.exception


def test_tarifarios_mostra_todas_as_ofertas_e_os_indexados(monkeypatch, omie_simulado):
    app = _abrir("paginas/tarifarios.py", monkeypatch)
    texto = _texto_visivel(app)
    assert "Todas as ofertas do mercado" in texto
    assert "Ofertas indexadas · estimativa por empresa" in texto
    app.toggle(key="t_sem_fid").set_value(True).run()
    assert not app.exception


def test_glossario_marca_cada_termo_uma_vez_e_escapa_o_texto():
    from interface import componentes as ui
    html = ui.com_glossario("A tarifa regulada e o vazio; outra vez vazio <b>")
    assert html.count('class="lc-termo"') == 2 and "&lt;b&gt;" in html
    assert 'data-def="O preço fixo definido pela ERSE' in html


def test_relatorio_pdf():
    from nucleo import recomendacoes as rc, relatorio
    pdf = relatorio.gerar(
        {"empresa": "Exemplo", "tipo": "Preço fixo", "opcao": "Simples", "kva": 6.9, "consumo_kwh": 300,
         "dias": 30, "preco_energia": 0.2, "preco_diario": 0.3659},
        {"energia": 60.0, "potencia": 10.98, "total": 70.98, "total_com_iva": 88.0},
        {"opcao": "simples", "total": 60.6},
        [rc.Recomendacao("x", "Título", "Texto com acentos: ação, €", 5.0)],
        [("Empresa A", "Oferta A", "Simples", 50.0)])
    assert pdf.startswith(b"%PDF") and len(pdf) > 1500


def test_acesso_so_pede_senha_a_quem_vem_de_fora():
    from interface import acesso
    assert not acesso.vem_de_fora({"Host": "localhost:8501"})
    assert not acesso.vem_de_fora({"Host": "127.0.0.1:8501"})
    assert not acesso.vem_de_fora({"Host": "[::1]:8501"})
    assert not acesso.vem_de_fora({})                              # testes (sem cabeçalhos)
    assert acesso.vem_de_fora({"Host": "simulador-energia.tailfb284d.ts.net"})
    # mesmo que um proxy reescrevesse o Host, o X-Forwarded-For denuncia o acesso de fora
    assert acesso.vem_de_fora({"Host": "127.0.0.1:8501", "X-Forwarded-For": "203.0.113.9"})
    assert acesso.senha_certa("abc", "abc") and not acesso.senha_certa("abd", "abc")
    assert not acesso.senha_certa("", "")                          # sem senha configurada: nunca entra


def test_de_fora_sem_senha_nao_mostra_o_site(monkeypatch):
    from interface import acesso
    monkeypatch.setattr(acesso, "vem_de_fora", lambda headers: True)
    monkeypatch.chdir(PASTA)
    app = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    app.secrets["acesso"] = {"senha": "teste-certo"}
    app.run()
    texto = _texto_visivel(app)
    assert "Acesso de teste" in texto and "Ferramentas" not in texto
    app.text_input[0].input("errada").run()
    app.button[0].click().run()
    assert "Palavra-passe errada" in _texto_visivel(app)
    app.text_input[0].input("teste-certo").run()
    app.button[0].click().run()
    assert "Ferramentas" in _texto_visivel(app) and not app.exception


def test_fatura_sem_precos_lidos_nao_rebenta(monkeypatch):
    """Erro real de um testador: fatura de outra empresa sem preço lido → campos vazios → TypeError."""
    app = _abrir("paginas/fatura.py", monkeypatch)
    perfil = {k: v for k, v in app.session_state["perfil"].items() if k not in ("preco_energia", "preco_diario")}
    app.session_state["perfil"] = {**perfil, "consumo_kwh": 210.0, "kva": 3.45, "da_fatura": True,
                                   "preco_energia": None, "fonte": "a tua fatura"}
    app.session_state["perfil_rev"] = 1
    app.run()
    assert not app.exception
    texto = _texto_visivel(app)
    assert "Não consegui ler o preço da energia nem o preço da potência" in texto
    assert app.number_input(key="f_preco_diario__1").value > 0      # potência regulada de 3,45 kVA


def test_config_da_raiz_igual_a_do_simulador():
    """O Streamlit Cloud só lê .streamlit/config.toml na raiz do repositório: tem de ser igual."""
    raiz = PASTA.parent / ".streamlit" / "config.toml"
    assert raiz.read_text(encoding="utf-8") == (PASTA / ".streamlit" / "config.toml").read_text(encoding="utf-8"), \
        "Copia simulador-energia/.streamlit/config.toml para .streamlit/config.toml (raiz)"


def test_requirements_do_site_cobrem_os_imports():
    import re
    pedidos = (PASTA / "requirements.txt").read_text(encoding="utf-8").lower()
    for modulo, pacote in {"streamlit": "streamlit", "pandas": "pandas", "plotly": "plotly",
                           "pypdf": "pypdf", "reportlab": "reportlab", "openpyxl": "openpyxl"}.items():
        assert re.search(rf"^{pacote}\b", pedidos, re.M), f"falta {pacote} em simulador-energia/requirements.txt"


def test_acesso_pode_ser_desligado_de_proposito(monkeypatch):
    from interface import acesso
    monkeypatch.setattr(acesso, "vem_de_fora", lambda headers: True)
    monkeypatch.chdir(PASTA)
    app = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    app.secrets["acesso"] = {"exigir": False}
    app.run()
    assert "Ferramentas" in _texto_visivel(app) and not app.exception


def test_segredos_com_maiuscula_e_numa_linha(monkeypatch):
    """No Cloud, colar no Safari pode dar "Acesso" e tudo numa linha: acesso = { senha = "…" }."""
    from interface import acesso
    monkeypatch.setattr(acesso, "vem_de_fora", lambda headers: True)
    monkeypatch.chdir(PASTA)
    app = AppTest.from_file(str(PASTA / "app.py"), default_timeout=30)
    app.secrets["Acesso"] = {"senha": "certa"}
    app.run()
    assert "Acesso de teste" in _texto_visivel(app)
    app.text_input[0].input("certa").run()
    app.button[0].click().run()
    assert "Ferramentas" in _texto_visivel(app)
