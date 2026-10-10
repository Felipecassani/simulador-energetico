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
    # limites aproximados, em kWh por pessoa e por mês
    if por_pessoa < 60:
        return "baixo"
    if por_pessoa < 120:
        return "medio"
    return "alto"


DICAS = [
    Dica("standby", "Desliga o que fica em espera",
         "A TV, a box, a consola e o computador gastam eletricidade mesmo desligados no comando, "
         "com a luzinha acesa. Liga-os a uma extensão com interruptor e desliga-a à noite.",
         "medio", "Aparelhos"),
    Dica("led", "Lâmpadas LED",
         "Troca as lâmpadas antigas por LED, a começar pelas que ficam mais horas acesas. "
         "Gastam muito menos e duram mais anos.",
         "baixo", "Iluminação"),
    Dica("maquinas_eco", "Máquinas em programa eco e cheias",
         "Lava a roupa e a loiça só com a máquina cheia. "
         "Escolhe o programa «eco» e temperaturas mais baixas.",
         "medio", "Aparelhos"),
    Dica("frio", "Frigorífico e arca em boa forma",
         "Afasta-os um pouco da parede e do fogão. Vê se as borrachas das portas fecham bem "
         "e descongela a arca quando tiver gelo.",
         "medio", "Aparelhos"),
    Dica("termo_vazio", "Água quente sem desperdício",
         "Baixa a temperatura do termoacumulador para o que precisas. Se tens bi-horário ou "
         "tri-horário, programa-o para aquecer só à noite, nas horas de vazio, que são as mais baratas.",
         "alto", "Água quente", lambda p: p.termoacumulador),
    Dica("termo_bomba", "Pensa numa bomba de calor para a água",
         "Se o termoacumulador já é antigo, há uma alternativa: a bomba de calor. Funciona como "
         "um ar condicionado e aquece a mesma água com muito menos eletricidade. Custa mais a "
         "comprar: em «4. Quanto podes poupar», abre «Vais comprar alguma coisa?» e vês em "
         "quanto tempo se paga.",
         "alto", "Água quente", lambda p: p.termoacumulador and nivel_consumo(p) != "baixo"),
    Dica("aquecimento", "Aquecer gastando menos",
         "Os aquecedores a óleo e os ventiladores são os que mais gastam. Um ar condicionado a "
         "aquecer dá o mesmo calor e gasta cerca de 3 vezes menos. Fecha as portas das divisões "
         "que não usas.",
         "alto", "Climatização", lambda p: p.aquecimento_eletrico),
    Dica("isolamento", "Fecha bem a casa",
         "No inverno, fecha as persianas à noite e usa cortinas grossas. Tapa as frinchas das "
         "janelas e portas, por exemplo com fita de vedação. No verão, fecha os estores nas "
         "horas de sol. Assim os aparelhos trabalham menos tempo.",
         "medio", "Climatização", lambda p: p.aquecimento_eletrico or p.ar_condicionado),
    Dica("ac", "Ar condicionado sem exageros",
         "No verão, 25 graus chegam; no inverno, 20 graus. Limpa os filtros de vez em quando e "
         "fecha janelas e portas enquanto está ligado.",
         "medio", "Climatização", lambda p: p.ar_condicionado),
    Dica("carro", "Carrega o carro nas horas baratas",
         "O carro é dos maiores gastos da casa e podes escolher a hora de o carregar. Se tens "
         "bi-horário ou tri-horário, programa o carregamento para a noite, nas horas de vazio, que são as mais "
         "baratas. No preço simples, todas as horas custam o mesmo.",
         "alto", "Mobilidade", lambda p: p.carro_eletrico),
    Dica("secar", "Seca a roupa ao ar",
         "A máquina de secar é dos aparelhos que mais gasta. Estende a roupa sempre que der e "
         "usa a máquina só quando for mesmo preciso. Centrifugar bem antes também ajuda.",
         "medio", "Aparelhos", lambda p: p.maquina_secar),
    Dica("cozinha", "Cozinhar com menos energia",
         "Põe a tampa nos tachos e usa tachos do tamanho da placa. Desliga a placa uns minutos "
         "antes do fim: o calor que fica acaba de cozinhar.",
         "baixo", "Cozinha", lambda p: p.placa_eletrica),
    Dica("horas_baratas", "Usa as horas mais baratas do mercado",
         "O teu tarifário é indexado: o preço muda com o mercado. Se o contrato cobra cada hora "
         "ao preço desse momento, põe as máquinas e o termoacumulador a trabalhar nas horas mais "
         "baratas, muitas vezes a meio do dia e de madrugada. Vês as horas mais baratas de hoje em "
         "«Preço hora a hora». Se o contrato usa a média do mês, mudar de hora não muda o preço.",
         "alto", "Tarifa", lambda p: p.indexado),
    Dica("opcao_horaria", "Vê se o bi-horário compensa",
         "Se gastas muito em coisas que podes pôr a trabalhar à noite, como a água quente, as "
         "máquinas ou o carro, o bi-horário pode sair mais barato. Faz as contas em "
         "«Bi-horário compensa?».",
         "alto", "Tarifa",
         lambda p: p.opcao == "simples" and (p.termoacumulador or p.carro_eletrico
                                              or nivel_consumo(p) == "alto")),
    Dica("auditoria", "Descobre o que gasta mais",
         "Com estes números, gasta-se mais do que é habitual para o número de pessoas da casa. Um medidor de consumo "
         "custa poucos euros: liga-se entre a tomada e o aparelho e mostra quanto ele gasta.",
         "alto", "Diagnóstico", lambda p: nivel_consumo(p) == "alto"),
]

_ORDEM = {"alto": 0, "medio": 1, "baixo": 2}


def dicas_para(perfil):
    """Dicas que se aplicam ao perfil, das de maior impacto para as de menor."""
    aplicaveis = [d for d in DICAS if d.quando is None or d.quando(perfil)]
    return sorted(aplicaveis, key=lambda d: _ORDEM[d.impacto])
