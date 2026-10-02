"""Dicas de eficiência energética adaptadas ao consumo e à casa de cada pessoa.

As dicas são conselhos gerais (qualitativos). O impacto (alto/médio/baixo) é uma
ordem de grandeza para priorizar, não uma promessa de poupança: a poupança em
euros calcula-se depois com a redução que a própria pessoa estimar.
"""
from dataclasses import dataclass, field

NIVEIS = ("baixo", "medio", "alto")


@dataclass(frozen=True)
class Perfil:
    consumo_mensal_kwh: float
    pessoas: int = 2
    opcao: str = "simples"               # simples · bi · tri
    termoacumulador: bool = False        # água quente elétrica
    aquecimento_eletrico: bool = False   # aquecedores / radiadores elétricos
    ar_condicionado: bool = False
    carro_eletrico: bool = False
    maquina_secar: bool = False
    placa_eletrica: bool = False         # placa de cozinha elétrica / vitrocerâmica
    indexado: bool = False               # tarifa indexada ao mercado


@dataclass(frozen=True)
class Dica:
    id: str
    titulo: str
    texto: str
    impacto: str                          # alto · medio · baixo
    categoria: str
    quando: object = field(default=None, compare=False, repr=False)   # função(perfil) → bool


def nivel_consumo(perfil):
    """Classifica o consumo mensal por pessoa em 'baixo', 'medio' ou 'alto'."""
    por_pessoa = perfil.consumo_mensal_kwh / max(perfil.pessoas, 1)
    # TODO(human): definir os limites (kWh/mês por pessoa) de cada nível.
    # Versão provisória, só para a página funcionar.
    if por_pessoa < 60:
        return "baixo"
    if por_pessoa < 120:
        return "medio"
    return "alto"


DICAS = [
    Dica("standby", "Corta o standby",
         "Usa extensões com interruptor na TV, box, consola e computador e desliga-as à noite. "
         "Os aparelhos em espera gastam energia 24 horas por dia.",
         "medio", "Aparelhos"),
    Dica("led", "Iluminação LED",
         "Troca as lâmpadas que ainda não são LED, a começar pelas que ficam mais horas acesas.",
         "baixo", "Iluminação"),
    Dica("maquinas_eco", "Máquinas em programa eco e cheias",
         "Lava roupa e loiça com a máquina cheia, em programas eco e a temperaturas mais baixas.",
         "medio", "Aparelhos"),
    Dica("frio", "Frigorífico e arca em boa forma",
         "Afasta-os da parede e de fontes de calor, verifica as borrachas das portas e "
         "descongela a arca quando tiver gelo acumulado.",
         "medio", "Aparelhos"),
    Dica("termo_vazio", "Água quente nas horas de vazio",
         "Programa o termoacumulador para aquecer nas horas de vazio e evita temperaturas "
         "mais altas do que precisas.",
         "alto", "Água quente", lambda p: p.termoacumulador),
    Dica("termo_bomba", "Pensa numa bomba de calor para a água",
         "Se o termoacumulador for antigo, uma bomba de calor aquece a mesma água com "
         "muito menos eletricidade.",
         "alto", "Água quente", lambda p: p.termoacumulador and nivel_consumo(p) != "baixo"),
    Dica("aquecimento", "Aquecimento mais eficiente",
         "Aquecedores de resistência são os que mais gastam. Prefere ar condicionado em modo "
         "de aquecimento ou bomba de calor e fecha portas das divisões que não usas.",
         "alto", "Climatização", lambda p: p.aquecimento_eletrico),
    Dica("isolamento", "Menos fugas de calor",
         "Cortinas grossas à noite, vedantes nas janelas e portas e persianas fechadas "
         "nas horas de mais frio reduzem o tempo de aquecimento.",
         "medio", "Climatização", lambda p: p.aquecimento_eletrico or p.ar_condicionado),
    Dica("ac", "Ar condicionado com conta",
         "Escolhe temperaturas moderadas, limpa os filtros e fecha janelas e estores ao sol.",
         "medio", "Climatização", lambda p: p.ar_condicionado),
    Dica("carro", "Carrega o carro em vazio",
         "Programa o carregamento para as horas de vazio: é o maior consumo que dá para mudar "
         "de hora sem perder conforto.",
         "alto", "Mobilidade", lambda p: p.carro_eletrico),
    Dica("secar", "Seca a roupa ao ar",
         "A máquina de secar é dos aparelhos que mais gasta; usa-a só quando for mesmo preciso.",
         "medio", "Aparelhos", lambda p: p.maquina_secar),
    Dica("cozinha", "Cozinhar com menos energia",
         "Tapa os tachos, usa recipientes do tamanho da placa e aproveita o calor residual "
         "no fim da cozedura.",
         "baixo", "Cozinha", lambda p: p.placa_eletrica),
    Dica("horas_baratas", "Usa as horas mais baratas do mercado",
         "Se o teu indexado cobra cada hora (ou cada 15 minutos) ao preço do mercado, põe máquinas e o termoacumulador nas horas mais baratas, muitas vezes a meio do dia e de madrugada. A ferramenta Gráficos mostra o mercado de hoje e, a partir do meio-dia, o de amanhã. Se o contrato usa a média do mês, mudar de hora não altera o preço.",
         "alto", "Tarifa", lambda p: p.indexado),
    Dica("opcao_horaria", "Vê se o bi-horário compensa",
         "Com consumos grandes que podes mudar de hora (água quente, máquinas, carro), "
         "o bi-horário pode sair mais barato. Compara na ferramenta Opções horárias.",
         "alto", "Tarifa",
         lambda p: p.opcao == "simples" and (p.termoacumulador or p.carro_eletrico
                                              or nivel_consumo(p) == "alto")),
    Dica("auditoria", "Descobre os grandes consumidores",
         "O teu consumo está acima do habitual para o tamanho da casa. Um medidor de tomada "
         "ajuda a encontrar o aparelho responsável.",
         "alto", "Diagnóstico", lambda p: nivel_consumo(p) == "alto"),
]

_ORDEM = {"alto": 0, "medio": 1, "baixo": 2}


def dicas_para(perfil):
    """Dicas que se aplicam ao perfil, das de maior impacto para as de menor."""
    aplicaveis = [d for d in DICAS if d.quando is None or d.quando(perfil)]
    return sorted(aplicaveis, key=lambda d: _ORDEM[d.impacto])
