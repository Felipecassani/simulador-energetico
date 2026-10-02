"""Fórmulas publicadas pelos comercializadores para os tarifários indexados (opção simples).

Cada fórmula dá o preço da energia em €/kWh a partir do OMIE médio (€/kWh); a tarifa de
acesso às redes (TAR, ERSE) soma-se à parte. Fontes e data de consulta em cada fórmula:
os parâmetros mudam, por isso cada um tem a sua origem. "Perdas ERSE" ≈ 16 % é a média das
perdas acumuladas em baixa tensão com os fatores ERSE de 2026 (ponta 17,9 %, cheias 16,5 %,
vazio 15,0 %, super vazio 12,7 %); quem usa o perfil horário real fica perto desse valor.

Estimativa pela média: nos indexados horários ou quarto-horários o valor real depende das
horas a que se consome.
"""
from dataclasses import dataclass

PERDAS_ERSE = 0.16
# Goldenergy: perdas mensais da ficha normalizada (jan … dez)
PERDAS_GOLDENERGY = (0.29, 0.18, 0.18, 0.15, 0.11, 0.10, 0.15, 0.13, 0.10, 0.10, 0.16, 0.25)


@dataclass(frozen=True)
class Formula:
    comercializador: str
    oferta: str
    descricao: str          # a fórmula em palavras, para a nota
    fonte: str
    consultado: str
    procurar: str           # texto no nome da oferta da ERSE (para ir buscar a potência)
    calcular: object        # (omie_kwh, mes) → €/kWh sem TAR
    aproximado: bool = False


FORMULAS = [
    Formula("Goldenergy", "Tarifa Index 04/25",
            "OMIE × (1 + perdas do mês) + 0,02425 + 0,03 €/kWh",
            "https://goldenergy.pt/resources/data/website/documentos/ficha-normalizada-indexados.pdf",
            "01/10/2026", "Index 04/25",
            lambda omie, mes: omie * (1 + PERDAS_GOLDENERGY[mes - 1]) + 0.02425 + 0.03),
    Formula("Goldenergy", "Index 100% Online",
            "OMIE × (1 + perdas do mês) + 0,02425 + 0,005 €/kWh (débito direto e fatura eletrónica)",
            "https://goldenergy.pt/resources/data/website/documentos/ficha-normalizada-indexados.pdf",
            "01/10/2026", "100% Online",
            lambda omie, mes: omie * (1 + PERDAS_GOLDENERGY[mes - 1]) + 0.02425 + 0.005),
    Formula("Coopérnico", "BASE 2.0",
            "(OMIE + 0,009) × (1 + perdas ≈ 16 %) + custos de sistema ≈ 0,003 + regulatórios ≈ 0,006",
            "https://www.coopernico.org/artigo/377", "01/10/2026", "BASE",
            lambda omie, mes: (omie + 0.009) * (1 + PERDAS_ERSE) + 0.003 + 0.006, aproximado=True),
    Formula("G9", "Smart Index",
            "OMIE × 1,02 × (1 + perdas ≈ 16 %) + 0,0185 + 0,008 €/kWh",
            "https://www.g9.pt/perguntasfrequentes/", "01/10/2026", "Index",
            lambda omie, mes: omie * 1.02 * (1 + PERDAS_ERSE) + 0.0185 + 0.008, aproximado=True),
    Formula("LUZiGÁS", "Poupança+",
            "(OMIE + 0,01 + 0,01833) × (1 + perdas ≈ 16 %)",
            "https://www.luzigas.pt/plano-luz-tarifario-dinamico", "01/10/2026", "Poupan",
            lambda omie, mes: (omie + 0.01 + 0.01833) * (1 + PERDAS_ERSE), aproximado=True),
    Formula("Galp", "Plano Flexível",
            "(OMIE + 0,0191) × (1 + perdas ≈ 16 %)",
            "https://www.galp.com/pt/casa/planos-e-precos", "01/10/2026", "Flex",
            lambda omie, mes: (omie + 0.0191) * (1 + PERDAS_ERSE), aproximado=True),
]


def estimar(omie_mwh, mes, tar_kwh, consumo_kwh, dias, potencia_dia):
    """[(formula, €/kWh com TAR, custo no período)] do mais barato para o mais caro.

    potencia_dia: {comercializador: €/dia} (da ERSE) — quem não tiver usa a chave None.
    """
    omie = omie_mwh / 1000
    linhas = []
    for f in FORMULAS:
        preco = f.calcular(omie, mes) + tar_kwh
        pot = potencia_dia.get((f.comercializador, f.procurar), potencia_dia.get(None, 0.0))
        linhas.append((f, preco, preco * consumo_kwh + pot * dias))
    return sorted(linhas, key=lambda l: l[2])
