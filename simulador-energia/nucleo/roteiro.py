"""Roteiro do projeto: as ferramentas, o que cada uma pede e como se valida.

Duas audiências, dois conjuntos de campos:
- site (público):  titulo, emoji, icone, pagina, descricao
- guia PDF (só para o programador, docs/gerar_pdf.py):
  objetivo, formulas, conta, testes, comando

As fórmulas usam a marcação do reportlab (<sub>…</sub>) porque só aparecem no PDF.
Sem Streamlit: também é usado pelos testes.
"""
from dataclasses import dataclass, field

from nucleo import calculos, mercado, tarifas

VALIDADO = "validado"
POR_IMPLEMENTAR = "por implementar"
A_REVER = "a rever"
ERRO = "erro"

TOLERANCIA = 1e-6


@dataclass(frozen=True)
class Passo:
    numero: int
    titulo: str
    emoji: str
    icone: str          # ícone Material do Streamlit, ex.: ":material/receipt_long:"
    pagina: str         # caminho da página, relativo a app.py
    descricao: str      # texto do site, para qualquer pessoa
    objetivo: str       # texto técnico do guia PDF
    formulas: list = field(default_factory=list)
    conta: list = field(default_factory=list)      # conta à mão do caso principal
    testes: list = field(default_factory=list)     # (entradas, resultado esperado)
    comando: str = ""   # sugestão de pedido ao Claude para arrancar o passo


PASSOS = [
    Passo(
        1, "A minha fatura", "🧾", ":material/receipt_long:", "paginas/fatura.py",
        "Carrega a tua fatura (PDF ou foto) ou escreve os números, e vê quanto pagas e que ofertas te saem "
        "mais baratas. Começa aqui.",
        "Calcular uma fatura simplificada a partir do consumo, do preço da energia, do preço "
        "diário da potência e dos dias de faturação. Os valores podem vir de uma fatura "
        "carregada (PDF ou foto, lida localmente) ou ser preenchidos à mão; os preços de "
        "referência são os da tarifa regulada da ERSE.",
        ["C<sub>energia</sub> = E<sub>consumida</sub> × p<sub>energia</sub>",
         "C<sub>potência</sub> = p<sub>diário</sub> × dias",
         "C<sub>total</sub> = C<sub>energia</sub> + C<sub>potência</sub>"],
        ["Energia: 500 kWh × 0,16 €/kWh = 80,00 €",
         "Potência: 0,35 €/dia × 30 dias = 10,50 €",
         "Total: 80,00 € + 10,50 € = 90,50 €"],
        [("A · 500 kWh · 0,16 €/kWh · 0,35 €/dia · 30 dias", "90,50 €"),
         ("B · 0 kWh, resto igual", "só custo de potência (10,50 €)"),
         ("C · 1000 kWh (o dobro)", "custo da energia duplica (160,00 €)"),
         ("D · qualquer valor negativo", "rejeitado"),
         ("E · 31 dias em vez de 30", "só a potência varia: 90,85 €")],
        "Explica-me fatura_simplificada() em nucleo/calculos.py bloco a bloco e confirma com o "
        "caso de validação: 500 kWh · 0,16 €/kWh · 0,35 €/dia · 30 dias = 90,50 €.",
    ),
    Passo(
        2, "Poupar em casa", "🌿", ":material/eco:", "paginas/eficiencia.py",
        "Dicas para gastar menos na tua casa e quanto poupas por mês e por ano.",
        "Sugerir dicas de eficiência conforme o consumo por pessoa e os equipamentos da casa, e "
        "comparar antes e depois de uma redução entre 0 % e 100 %: kWh evitados, custos, "
        "poupança mensal e anual e payback simples.",
        ["E<sub>depois</sub> = E<sub>antes</sub> × (1 − redução / 100)",
         "kWh evitados = E<sub>antes</sub> − E<sub>depois</sub>",
         "Poupança = C<sub>antes</sub> − C<sub>depois</sub>",
         "Poupança anual = poupança mensal × 12",
         "Payback simples = custo da medida ÷ poupança anual"],
        ["Depois: 500 kWh × (1 − 15/100) = 425 kWh",
         "Evitados: 500 − 425 = 75 kWh",
         "Poupança mensal: 75 kWh × 0,20 €/kWh = 15,00 €",
         "Poupança anual: 15,00 € × 12 = 180,00 €",
         "Payback de uma medida de 900 €: 900 € ÷ 180 €/ano = 5 anos"],
        [("500 kWh/mês · 0,20 €/kWh · 0,35 €/dia · 30 dias · 15 %",
          "75 kWh evitados · 15,00 €/mês · 180,00 €/ano"),
         ("6000 kWh/ano com redução de 15 %", "5100 kWh/ano · 900 kWh evitados"),
         ("medida de 900 € a poupar 180 €/ano", "payback simples de 5 anos"),
         ("redução abaixo de 0 % ou acima de 100 %", "rejeitada")],
        "Implementa consumo_depois() e cenario_eficiencia() em nucleo/calculos.py e a página "
        "paginas/eficiencia.py. Entradas: consumo (kWh), preço da energia (€/kWh), preço "
        "diário (€/dia), dias e redução (%). Rejeita reduções fora de 0 a 100 % (ValueError). "
        "Validação: 500 kWh, 0,20 €/kWh, 15 % = 75 kWh evitados e 15,00 €/mês. "
        "Mostra as equações primeiro e explica cada bloco.",
    ),
    Passo(
        3, "Comparar ofertas", "⚖️", ":material/compare_arrows:", "paginas/tarifarios.py",
        "Vê se há um tarifário mais barato do que o teu, com as ofertas de todas as empresas.",
        "Mostrar o mercado OMIE de hoje e de amanhã e a tarifa regulada da ERSE (com leitura "
        "ao vivo do documento oficial), e comparar até três ofertas do utilizador com a regulada "
        "e uma estimativa indexada, com o mesmo consumo e os mesmos dias, do mais barato para o "
        "mais caro. Sem nomes de comercializadores reais e sem declarar um vencedor.",
        ["C<sub>total,i</sub> = E × p<sub>energia,i</sub> + p<sub>diário,i</sub> × dias",
         "p<sub>indexado</sub> = OMIE<sub>médio</sub> ÷ 1000 × (1 + perdas) + margem + TAR<sub>energia</sub>"],
        ["A: 500 × 0,16 + 0,35 × 30 = 80,00 + 10,50 = 90,50 €",
         "B: 500 × 0,14 + 0,45 × 30 = 70,00 + 13,50 = 83,50 €",
         "C: 500 × 0,18 + 0,30 × 30 = 90,00 + 9,00 = 99,00 €",
         "Ordem: B, A, C"],
        [("500 kWh · 30 dias · A 0,16 / 0,35 · B 0,14 / 0,45 · C 0,18 / 0,30",
          "B 83,50 € · A 90,50 € · C 99,00 €")],
        "Implementa comparar_tarifarios() em nucleo/calculos.py e a página paginas/tarifarios.py: "
        "três tarifários A, B, C (nome, €/kWh, €/dia) com o mesmo consumo e dias, ordenados do "
        "mais barato ao mais caro, sem declarar o melhor. Validação: B 83,50 € · A 90,50 € · "
        "C 99,00 €.",
    ),
    Passo(
        4, "Preço hora a hora", "📊", ":material/bar_chart:", "paginas/graficos.py",
        "A que horas a eletricidade está mais barata hoje e amanhã, e as opções lado a lado em gráficos.",
        "Preço OMIE hora a hora (hoje e amanhã) com o vazio assinalado, custo de cada opção "
        "horária (energia + potência), repartição do consumo por período e os tarifários numa "
        "tabela pandas com a diferença para o mais barato e um gráfico de barras.",
        ["Diferença<sub>i</sub> = C<sub>total,i</sub> − mín(C<sub>total</sub>)"],
        ["Mais barato: B, com 83,50 €",
         "A: 90,50 − 83,50 = 7,00 €",
         "C: 99,00 − 83,50 = 15,50 €"],
        [("os três tarifários do passo 3", "diferenças 0,00 € · 7,00 € · 15,50 €")],
        "Implementa tabela_comparativa() em nucleo/calculos.py (DataFrame com as colunas do "
        "contrato) e a página paginas/graficos.py com a tabela e um gráfico de barras Plotly "
        "(interface/graficos.py, com a paleta). "
        "Validação: diferenças 0,00 € · 7,00 € · 15,50 €.",
    ),
    Passo(
        5, "Bi-horário compensa?", "🌙", ":material/schedule:", "paginas/bi_horario.py",
        "Pagar o mesmo a qualquer hora ou menos à noite? Vê se o bi-horário ou o tri-horário compensa para ti.",
        "Consumo e preço separados por período (vazio, fora de vazio, ponta, cheias) e as seis "
        "combinações simples/bi/tri × fixo/indexado, com a poupança face ao simples fixo. A "
        "repartição do consumo vem do utilizador ou da fatura, nunca de um 50/50 automático.",
        ["C<sub>energia</sub> = E<sub>vazio</sub> × p<sub>vazio</sub> + "
         "E<sub>fora</sub> × p<sub>fora</sub>",
         "C<sub>energia,tri</sub> = E<sub>vazio</sub> × p<sub>vazio</sub> + E<sub>ponta</sub> × "
         "p<sub>ponta</sub> + E<sub>cheias</sub> × p<sub>cheias</sub>",
         "C<sub>total</sub> = C<sub>energia</sub> + p<sub>diário</sub> × dias",
         "Poupança = C<sub>simples fixo</sub> − C<sub>opção</sub>"],
        ["Vazio: 200 kWh × 0,10 €/kWh = 20,00 €",
         "Fora de vazio: 300 kWh × 0,20 €/kWh = 60,00 €",
         "Potência: 0,35 €/dia × 30 dias = 10,50 €",
         "Total: 20,00 + 60,00 + 10,50 = 90,50 €",
         "Tri fixo (ERSE): 120 × 0,1087 + 45 × 0,2495 + 135 × 0,1690 + 0,3659 × 30 = 58,06 €"],
        [("200 kWh a 0,10 € + 300 kWh a 0,20 € · 0,35 €/dia · 30 dias", "90,50 €"),
         ("ERSE 2026 · 300 kWh · 40 % vazio · 15 % ponta · 6,9 kVA · 30 dias",
          "simples 60,60 € · bi 59,81 € · tri 58,06 €"),
         ("o mesmo, indexado com OMIE a 100 €/MWh, sem perdas nem margem",
          "simples 59,19 € · bi 57,90 € · tri 59,47 €"),
         ("qualquer valor negativo", "rejeitado")],
        "Implementa fatura_bi_horaria() em nucleo/calculos.py e a página paginas/bi_horario.py, "
        "com consumo e preço separados para vazio e fora de vazio (nunca 50/50 automático). "
        "Validação: 200 kWh a 0,10 € + 300 kWh a 0,20 € · 0,35 €/dia · 30 dias = 90,50 €.",
    ),
]


def _perto(a, b):
    return abs(a - b) < TOLERANCIA


def _verificar_1():
    f = calculos.fatura_simplificada(500, 0.16, 0.35, 30)
    ok = _perto(f["energia"], 80) and _perto(f["potencia"], 10.5) and _perto(f["total"], 90.5)
    return ok, f"total = {f['total']:.2f} € (esperado 90,50 €)"


def _verificar_2():
    r = calculos.cenario_eficiencia(500, 0.20, 0.35, 30, 15)
    ok = _perto(r["kwh_evitados"], 75) and _perto(r["poupanca_mensal"], 15)
    return ok, f"{r['kwh_evitados']:.0f} kWh evitados, {r['poupanca_mensal']:.2f} €/mês (esperado 75 kWh, 15,00 €)"


TARIFARIOS_TESTE = [
    {"nome": "A", "preco_energia": 0.16, "preco_diario": 0.35},
    {"nome": "B", "preco_energia": 0.14, "preco_diario": 0.45},
    {"nome": "C", "preco_energia": 0.18, "preco_diario": 0.30},
]


def _verificar_3():
    r = calculos.comparar_tarifarios(500, 30, TARIFARIOS_TESTE)
    nomes = [t["nome"] for t in r]
    ok = nomes == ["B", "A", "C"] and _perto(r[0]["total"], 83.5)
    return ok, f"ordem {' > '.join(nomes)} (esperado B > A > C)"


def _verificar_4():
    tabela = calculos.tabela_comparativa(calculos.comparar_tarifarios(500, 30, TARIFARIOS_TESTE))
    diferencas = [round(v, 2) for v in tabela["Diferença (€)"]]
    ok = diferencas == [0.0, 7.0, 15.5]
    return ok, f"diferenças {diferencas} (esperado [0.0, 7.0, 15.5])"


def _verificar_5():
    f = calculos.fatura_bi_horaria(200, 0.10, 300, 0.20, 0.35, 30)
    erse = mercado.carregar_erse_local(2026)   # valores de 2026 fixos: é um caso de validação
    opcoes = {(l["opcao"], l["modalidade"]): l["total"]
              for l in tarifas.comparar_opcoes(300, 40, 15, 30, 6.9, erse)}
    ok = _perto(f["total"], 90.5) and abs(opcoes[("tri", "fixo")] - 58.0635) < 1e-6
    return ok, f"bi {f['total']:.2f} € (esperado 90,50 €) · tri fixo {opcoes[('tri', 'fixo')]:.2f} €"


_VERIFICACOES = {1: _verificar_1, 2: _verificar_2, 3: _verificar_3,
                 4: _verificar_4, 5: _verificar_5}


def verificar(numero):
    """Corre o caso de validação do passo. Devolve (estado, detalhe)."""
    try:
        ok, detalhe = _VERIFICACOES[numero]()
    except NotImplementedError:
        return POR_IMPLEMENTAR, "Ainda sem código."
    except Exception as erro:  # a página não deve rebentar por causa de um passo
        return ERRO, f"{type(erro).__name__}: {erro}"
    return (VALIDADO if ok else A_REVER), detalhe


def disponivel(numero):
    """Uma ferramenta só aparece como disponível no site depois de validada."""
    return verificar(numero)[0] == VALIDADO


def passo(numero):
    return next(p for p in PASSOS if p.numero == numero)
