"""Textos do site: Guia, Perguntas frequentes, secções em construção e o autor.

Escrito para qualquer pessoa (tu, português de Portugal), sem fórmulas.
Os horários vêm de nucleo/periodos para não haver dois sítios a dizer coisas diferentes.
"""
from dataclasses import dataclass

from nucleo import periodos

AUTOR = {
    "nome": "Luiz Cassani",
    "linha": "Programação, eletrónica e automação da casa.",
    "ligacoes": [
        ("GitHub", "https://github.com/Felipecassani", "codigo"),
        ("LinkedIn", "https://www.linkedin.com/in/luizfelipecassani/", "linkedin"),
    ],
}

VAZIO = periodos.texto_vazio_curto()

GUIA = [
    ("O que pagas numa fatura",
     "A fatura tem duas partes principais. A energia é o que consomes, em kWh, a um preço por kWh. "
     "A potência é um valor fixo por dia, que depende da potência contratada. Por cima vêm as taxas "
     "e impostos: IVA, contribuição audiovisual, taxa da DGEG e imposto especial de consumo. "
     "Este simulador compara os valores sem IVA nem taxas: as taxas são iguais em todas as ofertas "
     "e o IVA acompanha o preço, por isso quase nunca muda qual é a oferta mais barata."),
    ("Potência contratada",
     "É a potência máxima que podes usar ao mesmo tempo, em kVA. Numa casa vai de 1,15 a 20,7 kVA; "
     "os valores mais comuns são 3,45, 4,6 e 6,9 kVA. Quanto maior, mais pagas por dia, mesmo sem consumir. Se o quadro nunca "
     "dispara, talvez possas descer um escalão; se ligas muitas vezes forno, placa e máquinas ao "
     "mesmo tempo, mantém a que tens."),
    ("Opções horárias",
     f"No simples, o preço é igual a qualquer hora. No bi-horário, as horas de vazio ({VAZIO}) são "
     "mais baratas e as restantes mais caras. No tri-horário há vazio, cheias e ponta, e a ponta "
     "(a mais cara) muda entre o inverno e o verão. Compensa mudar quando grande parte do consumo "
     "é feita no vazio. A ferramenta Opções horárias faz a conta por ti."),
    ("Preço fixo ou indexado",
     "Com preço fixo, pagas sempre o mesmo por kWh durante o contrato. Com preço indexado, o preço "
     "acompanha o mercado ibérico de eletricidade (OMIE), que muda de 15 em 15 minutos. Ao valor do "
     "mercado juntam-se as perdas na rede (energia que se perde no caminho), a margem do "
     "comercializador e as tarifas de acesso às redes (iguais para todos, fixadas pela ERSE). "
     "Alguns contratos cobram cada período ao preço desse momento; outros usam a média do mês. "
     "O indexado costuma compensar quando o mercado está baixo; em troca, corres o risco de o "
     "mercado subir."),
    ("Tarifa regulada",
     "É o preço fixo definido pela ERSE, a entidade reguladora, normalmente uma vez por ano. Podes "
     "aderir a ela através de um comercializador de último recurso. Serve de referência: "
     "se pagas mais do que a regulada, vale a pena comparar ofertas. A ferramenta Fatura mostra "
     "sempre esta comparação."),
    ("Campanhas e descontos",
     "Muitas ofertas têm descontos temporários. A fatura costuma mostrar o preço sem desconto: "
     "confirma até quando dura a campanha e volta a comparar nessa altura."),
    ("Mudar de comercializador",
     "Mudar é gratuito, não corta a luz e não muda o contador. Antes de mudar, vê se o contrato "
     "atual tem fidelização. O simulador oficial da ERSE compara as ofertas de todas as empresas."),
    ("Poupar sem mudar de contrato",
     "Desliga os aparelhos em standby, usa iluminação LED, põe as máquinas a trabalhar cheias e em "
     "programas eco, e seca a roupa ao ar sempre que der. A ferramenta Eficiência mostra as dicas "
     "que mais contam para o teu consumo."),
]

FAQ = [
    ("Preciso de criar conta ou de pagar?",
     "Não. O simulador é gratuito e não tem contas."),
    ("O que acontece aos dados que escrevo ou à fatura que carrego?",
     "A fatura é lida só para preencher os campos e não é guardada. Os valores passam entre as "
     "ferramentas enquanto estás no site e desaparecem quando fechas ou recarregas a página."),
    ("A leitura da fatura falhou ou leu um valor errado. E agora?",
     "Corrige ou preenche os campos à mão: o resultado atualiza na hora. Faturas em foto leem-se "
     "melhor com boa luz e a folha direita."),
    ("De onde vêm os preços?",
     "Da tua fatura, da tarifa regulada publicada pela ERSE e do mercado ibérico (OMIE). "
     "Os preços do mercado para o dia seguinte saem por volta do meio-dia (hora de Portugal continental)."),
    ("Porque é que o total não é igual ao da minha fatura?",
     "Porque o simulador compara os valores sem IVA nem taxas, que são iguais em todas as ofertas. "
     "Arredondamentos e acertos de leituras também podem dar pequenas diferenças."),
    ("A tarifa regulada é de preço fixo ou indexado?",
     "De preço fixo: a ERSE define os preços para o ano inteiro."),
    ("Como sei se a minha fatura é de preço fixo ou indexado?",
     "Uma fatura indexada fala do mercado (OMIE), de perdas e de uma margem ou custo de gestão, e o "
     "preço por kWh muda de mês para mês. Ao carregar a fatura, o simulador tenta perceber sozinho; "
     "podes sempre mudar na ferramenta Fatura."),
    ("Quando é que o bi-horário compensa?",
     f"Quando uma boa parte do consumo cai no vazio ({VAZIO}). Se já estás em bi ou tri-horário, a "
     "fatura mostra essa repartição; no simples, com contador inteligente, vês os consumos no Balcão "
     "Digital da E-REDES. Depois indica-a em Opções horárias."),
    ("Mudar de comercializador corta a luz?",
     "Não. A rede, o contador e a qualidade do serviço são os mesmos; muda só quem te fatura. "
     "Vê apenas se o contrato atual tem fidelização."),
    ("As recomendações são uma garantia de poupança?",
     "Não. São estimativas com os teus dados e os preços oficiais. Confirma sempre as condições na "
     "ficha da oferta antes de decidir."),
]


@dataclass(frozen=True)
class EmConstrucao:
    chave: str
    titulo: str
    icone: str
    emoji: str
    descricao: str
    planos: tuple


EM_CONSTRUCAO = [
    EmConstrucao("gas", "Gás natural", ":material/local_fire_department:", "🔥",
                 "Simular a fatura do gás e comparar a tarifa regulada com as ofertas do mercado.",
                 ("Consumo em kWh ou em metros cúbicos", "Escalões de consumo",
                  "Comparação com a tarifa regulada")),
    EmConstrucao("gas-eletricidade", "Gás + eletricidade", ":material/join_inner:", "🔗",
                 "Juntar as duas faturas e ver se um pacote dual compensa.",
                 ("As duas faturas lado a lado", "Custo total por mês e por ano")),
    EmConstrucao("fotovoltaico", "Fotovoltaico", ":material/solar_power:", "☀️",
                 "Quantos painéis fazem sentido para o teu consumo, quanto poupas e quando recuperas "
                 "o investimento.",
                 ("Produção estimada para a tua zona", "Autoconsumo e excedente",
                  "Tempo de retorno do investimento")),
    EmConstrucao("regulamentacao", "Regulamentação", ":material/gavel:", "⚖️",
                 "As regras do setor explicadas de forma simples.",
                 ("Tarifas de acesso às redes", "Tarifa social", "Perdas na rede")),
    EmConstrucao("europa", "Europa", ":material/public:", "🇪🇺",
                 "Comparar os preços da eletricidade em Portugal com os outros países europeus.",
                 ("Preços por país", "Evolução ao longo do ano")),
    EmConstrucao("mercado", "Mercado", ":material/candlestick_chart:", "📈",
                 "Histórico do mercado ibérico e as horas mais baratas de cada dia.",
                 ("Histórico do OMIE", "Melhor janela horária do dia", "Preços futuros")),
    EmConstrucao("producao", "Produção", ":material/factory:", "🏭",
                 "De onde vem a eletricidade de cada dia.",
                 ("Renováveis, gás e importação", "Balanço diário")),
]


def em_construcao(chave):
    return next(e for e in EM_CONSTRUCAO if e.chave == chave)


# termo → (categoria, definição curta). Os termos aparecem sublinhados no Guia e nas Perguntas
# frequentes e explicam-se ao passar o rato (ou ao tocar, no telemóvel).
GLOSSARIO = {
    "kWh": ("Unidades", "Quilowatt-hora: a energia que gastas. Um aparelho de 1000 W ligado 1 hora gasta 1 kWh."),
    "kVA": ("Unidades", "Quilovolt-ampere: a unidade da potência contratada."),
    "potência contratada": ("Fatura", "A potência máxima que podes usar ao mesmo tempo. Pagas um valor por dia, mesmo sem consumir."),
    "CPE": ("Fatura", "Código de Ponto de Entrega: o número que identifica a tua instalação na rede. Pede-se ao mudar de comercializador."),
    "leitura estimada": ("Fatura", "Quando ninguém leu o contador, a fatura usa uma estimativa; a diferença é acertada mais tarde."),
    "contribuição audiovisual": ("Fatura", "Taxa de 2,85 € por mês que financia o serviço público de rádio e televisão."),
    "tarifa social": ("Fatura", "Desconto para famílias com baixos rendimentos ou que recebem certas prestações sociais."),
    "IVA": ("Fatura", "Imposto sobre o valor acrescentado: 6 % numa parte da energia e da potência, 23 % no resto."),
    "OMIE": ("Mercado", "O mercado ibérico onde se compra e vende a eletricidade de Portugal e Espanha. Dá um preço para cada quarto de hora."),
    "indexado": ("Mercado", "Tarifário em que o preço da energia acompanha o mercado (OMIE), em vez de ser fixo."),
    "perdas": ("Mercado", "A energia que se perde no caminho até tua casa. Nos indexados é cobrada como uma percentagem sobre o preço do mercado."),
    "margem": ("Mercado", "O que o comercializador soma ao preço do mercado para cobrir os seus custos e o lucro."),
    "ERSE": ("Regulação", "Entidade Reguladora dos Serviços Energéticos: define a tarifa regulada e as tarifas de acesso às redes."),
    "tarifas de acesso às redes": ("Regulação", "A parte do preço que paga o uso das redes e outros custos do sistema. É igual em todos os comercializadores."),
    "tarifa regulada": ("Regulação", "O preço fixo definido pela ERSE. Serve de referência para comparar ofertas."),
    "comercializador de último recurso": ("Regulação", "A empresa que vende a tarifa regulada (no continente, a SU Eletricidade)."),
    "comercializador": ("Regulação", "A empresa que te vende a eletricidade e emite a fatura."),
    "fidelização": ("Regulação", "Período mínimo do contrato. Sair antes pode ter custos; vê sempre na ficha da oferta."),
    "E-REDES": ("Regulação", "A empresa que gere a rede e os contadores. Não muda quando mudas de comercializador."),
    "vazio": ("Horários", "O período mais barato do bi e do tri-horário (no ciclo diário, das 22h às 8h)."),
    "ponta": ("Horários", "O período mais caro do tri-horário: 4 horas por dia, que mudam entre o inverno e o verão."),
    "cheias": ("Horários", "No tri-horário, as horas que não são vazio nem ponta."),
    "bi-horário": ("Horários", "Opção com dois preços: vazio (mais barato) e fora de vazio."),
    "tri-horário": ("Horários", "Opção com três preços: vazio, cheias e ponta."),
}

LIGACOES = [
    ("Simulador de preços da ERSE", "https://simuladorprecos.erse.pt/", "Compara as ofertas de todas as empresas."),
    ("ERSE — tarifas e preços", "https://www.erse.pt/atividade/regulacao/tarifas-e-precos-eletricidade/", "As tarifas oficiais de cada ano."),
    ("OMIE — resultados do mercado", "https://www.omie.es/pt/market-results", "Os preços do mercado ibérico, dia a dia."),
    ("Balcão Digital da E-REDES", "https://balcaodigital.e-redes.pt/", "Os teus consumos de 15 em 15 minutos (com contador inteligente)."),
    ("Tarifa social", "https://www.dgeg.gov.pt/pt/areas-transversais/tarifa-social-de-energia/", "Quem tem direito e como se pede."),
]
