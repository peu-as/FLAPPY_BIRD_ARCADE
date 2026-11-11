"""Regras do Combina 3: tabuleiro, combinações, peças especiais, cascatas e queda.

Não desenha nada e não usa o `random` do jogo (tem o próprio sorteador, com
semente opcional: a mesma semente e as mesmas jogadas dão o mesmo resultado).

Uma jogada acontece em ONDAS, para a tela poder animar cada etapa:

    onda = tab.trocar(a, b)        # None = troca inválida (nada muda)
    while onda:
        tab.aplicar(onda)          # some o que combinou, nascem as especiais
        quedas = tab.cair()        # as peças caem e entram novas
        onda = tab.proxima_onda()  # cascata: o que combinou ao cair

Peças especiais (inspiradas no gênero, com os nomes dos nossos bônus):
    4 em linha  -> PENA-RAIO  (limpa a linha ou a coluna inteira)
    L ou T      -> OVO NOVA   (explode 3x3)
    5 em linha  -> ARCO-ÍRIS  (trocado com uma peça, limpa todas daquele tipo)
Trocar duas especiais entre si combina os efeitos (veja _combo).

Obstáculos (para as casas): gelo (camadas sob a peça: some quando a peça de
cima é limpa), caixa (ocupa a casa; quebra com limpezas ao lado ou efeitos) e
pedra (casa que não existe).
"""
import random
from dataclasses import dataclass, field

LINHA_H, LINHA_V, OVO, ARCO = 'linha_h', 'linha_v', 'ovo', 'arco'
TIPOS = ('pena', 'folha', 'ovo', 'moeda', 'semente', 'fruta')

PONTOS_PECA = 20
PONTOS_ESPECIAL = {LINHA_H: 60, LINHA_V: 60, OVO: 120, ARCO: 200}
PONTOS_GELO, PONTOS_CAIXA = 30, 40


@dataclass(eq=False)
class Peca:
    tipo: str                 # '' no Arco-íris (não combina com nada)
    especial: str = ''
    id: int = 0


@dataclass
class Onda:
    """Tudo o que uma etapa da jogada faz, para aplicar e para animar."""
    limpas: dict = field(default_factory=dict)        # (l, c) -> Peca que some
    criadas: dict = field(default_factory=dict)       # (l, c) -> Peca especial que nasce
    efeitos: list = field(default_factory=list)       # ('linha_h', l) | ('linha_v', c) | ('explosao', l, c, raio)
                                                      # | ('arco', (l, c), [casas])
    gelo: list = field(default_factory=list)          # casas que perdem uma camada
    caixas: list = field(default_factory=list)        # caixas que levam um golpe
    transformadas: dict = field(default_factory=dict)  # (l, c) -> especial (Arco-íris + especial)
    pontos: int = 0
    multiplicador: int = 1


class Tabuleiro:
    def __init__(self, linhas=8, colunas=7, tipos=TIPOS, semente=None, pedras=(), caixas=None, gelo=None):
        self.linhas, self.colunas = linhas, colunas
        self.tipos = tuple(tipos)
        self.sorteio = random.Random(semente)
        self._proximo_id = 1
        self.pedra = [[(l, c) in pedras for c in range(colunas)] for l in range(linhas)]
        self.caixa = [[(caixas or {}).get((l, c), 0) for c in range(colunas)] for l in range(linhas)]
        self.gelo = [[(gelo or {}).get((l, c), 0) for c in range(colunas)] for l in range(linhas)]
        self.grade = [[None] * colunas for _ in range(linhas)]
        self.contagem = {t: 0 for t in self.tipos}        # peças limpas por tipo
        self.pontos = 0
        self.cascata = 0                                   # ondas seguidas na jogada atual
        self.ultima_troca = None
        self._preencher()

    # ------------------------------------------------------------ casas
    def dentro(self, l, c):
        return 0 <= l < self.linhas and 0 <= c < self.colunas

    def livre(self, l, c):
        """Casa onde pode haver peça (não é pedra nem tem caixa)."""
        return self.dentro(l, c) and not self.pedra[l][c] and self.caixa[l][c] == 0

    def casas(self):
        return [(l, c) for l in range(self.linhas) for c in range(self.colunas) if self.livre(l, c)]

    def peca(self, casa):
        return self.grade[casa[0]][casa[1]] if self.dentro(*casa) else None

    def nova_peca(self, tipo=None, especial=''):
        peca = Peca(self.sorteio.choice(self.tipos) if tipo is None else tipo, especial, self._proximo_id)
        self._proximo_id += 1
        return peca

    @property
    def gelo_restante(self):
        return sum(1 for linha in self.gelo for v in linha if v > 0)

    @property
    def caixas_restantes(self):
        return sum(1 for linha in self.caixa for v in linha if v > 0)

    def _preencher(self):
        """Começa sem nenhuma combinação pronta e com pelo menos uma jogada possível."""
        for _ in range(200):
            for l, c in self.casas():
                proibidos = set()
                if c >= 2 and self._mesmo_tipo((l, c - 1), (l, c - 2)):
                    proibidos.add(self.grade[l][c - 1].tipo)
                if l >= 2 and self._mesmo_tipo((l - 1, c), (l - 2, c)):
                    proibidos.add(self.grade[l - 1][c].tipo)
                opcoes = [t for t in self.tipos if t not in proibidos]
                self.grade[l][c] = self.nova_peca(self.sorteio.choice(opcoes))
            if self.dica() is not None:
                return
        raise RuntimeError('não foi possível montar um tabuleiro jogável')

    def _mesmo_tipo(self, a, b):
        pa, pb = self.peca(a), self.peca(b)
        return pa is not None and pb is not None and pa.tipo and pa.tipo == pb.tipo

    # ------------------------------------------------------------ combinações
    def _sequencias(self):
        """Todas as sequências de 3 ou mais iguais: [('h' | 'v', [casas])]."""
        achadas = []
        for l in range(self.linhas):
            achadas += self._varrer([(l, c) for c in range(self.colunas)], 'h')
        for c in range(self.colunas):
            achadas += self._varrer([(l, c) for l in range(self.linhas)], 'v')
        return achadas

    def _varrer(self, fila, orientacao):
        achadas, atual = [], []
        for casa in fila + [None]:
            peca = self.peca(casa) if casa is not None else None
            if atual and peca is not None and peca.tipo and peca.tipo == self.peca(atual[0]).tipo:
                atual.append(casa)
                continue
            if len(atual) >= 3:
                achadas.append((orientacao, atual))
            atual = [casa] if peca is not None and peca.tipo else []
        return achadas

    def _grupos(self):
        """Junta as sequências que se cruzam (L, T, +): [{'casas', 'sequencias'}]."""
        grupos = []
        for seq in self._sequencias():
            casas = set(seq[1])
            juntar = [g for g in grupos if g['casas'] & casas]
            novo = {'casas': casas, 'sequencias': [seq]}
            for g in juntar:
                novo['casas'] |= g['casas']
                novo['sequencias'] += g['sequencias']
                grupos.remove(g)
            grupos.append(novo)
        return grupos

    def _especial_do_grupo(self, grupo):
        """(especial, casa onde nasce) ou None. 5 em linha > L/T > 4 em linha."""
        maior = max(grupo['sequencias'], key=lambda s: len(s[1]))
        cruzamentos = [casa for casa in grupo['casas']
                       if sum(casa in s[1] for s in grupo['sequencias']) >= 2]
        preferidas = [casa for casa in (self.ultima_troca or ()) if casa in grupo['casas']]
        if len(maior[1]) >= 5:
            return ARCO, (preferidas or [maior[1][len(maior[1]) // 2]])[0]
        if cruzamentos:
            return OVO, cruzamentos[0]
        if len(maior[1]) == 4:
            especial = LINHA_H if maior[0] == 'h' else LINHA_V
            return especial, (preferidas or [maior[1][1]])[0]
        return None

    # ------------------------------------------------------------ ondas
    def adjacentes(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    def trocar(self, a, b):
        """Troca duas peças vizinhas. Devolve a Onda (já com a troca feita) ou None se não combina."""
        pa, pb = self.peca(a), self.peca(b)
        if pa is None or pb is None or not self.adjacentes(a, b):
            return None
        self._trocar(a, b)
        self.ultima_troca = (b, a)                     # primeiro onde a peça movida chegou
        self.cascata = 0
        onda = self._combo(pa, b, pb, a) or self._onda()
        if onda is None:
            self._trocar(a, b)
            self.ultima_troca = None
        return onda

    def _trocar(self, a, b):
        (la, ca), (lb, cb) = a, b
        self.grade[la][ca], self.grade[lb][cb] = self.grade[lb][cb], self.grade[la][ca]

    def proxima_onda(self):
        """Depois de cair: há novas combinações (cascata)?"""
        self.ultima_troca = None
        return self._onda()

    def _onda(self):
        grupos = self._grupos()
        if not grupos:
            return None
        self.cascata += 1
        onda = Onda(multiplicador=self.cascata)
        fila = []
        for grupo in grupos:
            for casa in grupo['casas']:
                self._limpar(onda, casa, fila)
            nasce = self._especial_do_grupo(grupo)
            if nasce:
                especial, casa = nasce
                tipo = '' if especial == ARCO else self.peca(next(iter(grupo['casas']))).tipo
                onda.criadas[casa] = self.nova_peca(tipo, especial)
                onda.pontos += PONTOS_ESPECIAL[especial]
        self._ativar_fila(onda, fila)
        return self._fechar(onda)

    def _limpar(self, onda, casa, fila):
        """Marca a casa para limpar; se a peça for especial, entra na fila de ativação."""
        if not self.dentro(*casa) or self.pedra[casa[0]][casa[1]]:
            return
        if self.caixa[casa[0]][casa[1]] > 0:
            if casa not in onda.caixas:
                onda.caixas.append(casa)
            return
        peca = self.peca(casa)
        if peca is None or casa in onda.limpas:
            return
        onda.limpas[casa] = peca
        especial = onda.transformadas.get(casa, peca.especial)
        if especial:
            fila.append((casa, especial))

    def _ativar_fila(self, onda, fila):
        while fila:
            (l, c), especial = fila.pop(0)
            if especial == LINHA_H:
                onda.efeitos.append((LINHA_H, l))
                alvos = [(l, x) for x in range(self.colunas)]
            elif especial == LINHA_V:
                onda.efeitos.append((LINHA_V, c))
                alvos = [(y, c) for y in range(self.linhas)]
            elif especial == OVO:
                onda.efeitos.append(('explosao', l, c, 1))
                alvos = [(l + dl, c + dc) for dl in (-1, 0, 1) for dc in (-1, 0, 1)]
            else:                                   # Arco-íris atingido por outro efeito: leva a cor mais comum
                alvos = self._casas_do_tipo(self._tipo_mais_comum(onda))
                onda.efeitos.append((ARCO, (l, c), alvos))
            for casa in alvos:
                self._limpar(onda, casa, fila)

    def _fechar(self, onda):
        """Vizinhança: caixas ao lado do que foi limpo levam um golpe; gelo sob o que foi limpo perde uma camada."""
        for (l, c) in onda.limpas:
            if self.gelo[l][c] > 0:
                onda.gelo.append((l, c))
            for dl, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                viz = (l + dl, c + dc)
                if self.dentro(*viz) and self.caixa[viz[0]][viz[1]] > 0 and viz not in onda.caixas:
                    onda.caixas.append(viz)
        onda.pontos += (len(onda.limpas) * PONTOS_PECA + len(onda.gelo) * PONTOS_GELO
                        + len(onda.caixas) * PONTOS_CAIXA)
        onda.pontos *= onda.multiplicador
        return onda

    def _casas_do_tipo(self, tipo):
        return [casa for casa in self.casas() if self.peca(casa) is not None and self.peca(casa).tipo == tipo]

    def _tipo_mais_comum(self, onda=None):
        ja = onda.limpas if onda else {}
        contagem = {}
        for casa in self.casas():
            peca = self.peca(casa)
            if peca is not None and peca.tipo and casa not in ja:
                contagem[peca.tipo] = contagem.get(peca.tipo, 0) + 1
        return max(sorted(contagem), key=contagem.get) if contagem else self.tipos[0]

    def _combo(self, movida, destino, outra, origem):
        """Troca entre especiais (ou Arco-íris com qualquer peça). destino = onde a peça movida chegou."""
        ea, eb = movida.especial, outra.especial
        if ARCO not in (ea, eb) and not (ea and eb):
            return None
        self.cascata += 1
        onda = Onda(multiplicador=self.cascata)
        fila = []
        l, c = destino
        onda.limpas[destino], onda.limpas[origem] = movida, outra      # as duas somem sem ativar sozinhas
        if ea == ARCO and eb == ARCO:
            alvos = self.casas()
            onda.efeitos.append((ARCO, destino, alvos))
        elif ARCO in (ea, eb):
            parceira = outra if ea == ARCO else movida
            alvos = self._casas_do_tipo(parceira.tipo)
            onda.efeitos.append((ARCO, destino, alvos))
            if parceira.especial:                    # todas daquele tipo viram a especial e disparam
                for casa in alvos:
                    onda.transformadas[casa] = (self.sorteio.choice((LINHA_H, LINHA_V))
                                                if parceira.especial in (LINHA_H, LINHA_V) else OVO)
        elif OVO in (ea, eb) and ea != eb:           # Pena-Raio + Ovo Nova: 3 linhas e 3 colunas
            alvos = [(y, x) for y in range(self.linhas) for x in range(self.colunas)
                     if abs(y - l) <= 1 or abs(x - c) <= 1]
            onda.efeitos += [(LINHA_H, l + d) for d in (-1, 0, 1) if self.dentro(l + d, 0)]
            onda.efeitos += [(LINHA_V, c + d) for d in (-1, 0, 1) if self.dentro(0, c + d)]
        elif ea == OVO:                              # Ovo Nova + Ovo Nova: 5x5
            alvos = [(l + dl, c + dc) for dl in range(-2, 3) for dc in range(-2, 3)]
            onda.efeitos.append(('explosao', l, c, 2))
        else:                                        # Pena-Raio + Pena-Raio: cruz
            alvos = [(l, x) for x in range(self.colunas)] + [(y, c) for y in range(self.linhas)]
            onda.efeitos += [(LINHA_H, l), (LINHA_V, c)]
        onda.pontos += 150
        for casa in alvos:
            self._limpar(onda, casa, fila)
        self._ativar_fila(onda, fila)
        return self._fechar(onda)

    def aplicar(self, onda):
        """Tira do tabuleiro o que a onda limpou e põe as especiais que nasceram."""
        for (l, c), peca in onda.limpas.items():
            self.grade[l][c] = None
            if peca.tipo:
                self.contagem[peca.tipo] = self.contagem.get(peca.tipo, 0) + 1
        for (l, c) in onda.gelo:
            self.gelo[l][c] -= 1
        for (l, c) in onda.caixas:
            self.caixa[l][c] -= 1
        for (l, c), peca in onda.criadas.items():
            self.grade[l][c] = peca
        self.pontos += onda.pontos

    # ------------------------------------------------------------ queda
    def cair(self):
        """As peças descem e entram novas. Devolve [(peca, linha de onde veio, (l, c) final)];
        peças novas vêm de linhas acima do trecho (negativas no topo do tabuleiro)."""
        movimentos = []
        for c in range(self.colunas):
            l = self.linhas - 1
            while l >= 0:
                if not self.livre(l, c):
                    l -= 1
                    continue
                fim = l                                   # trecho livre [inicio..fim], de baixo para cima
                while l >= 0 and self.livre(l, c):
                    l -= 1
                inicio = l + 1
                pecas = [(y, self.grade[y][c]) for y in range(fim, inicio - 1, -1) if self.grade[y][c] is not None]
                destino = fim
                for origem, peca in pecas:
                    self.grade[origem][c] = None
                    self.grade[destino][c] = peca
                    if origem != destino:
                        movimentos.append((peca, origem, (destino, c)))
                    destino -= 1
                faltam = destino - inicio + 1
                for k in range(faltam):
                    peca = self.nova_peca()
                    self.grade[destino - k][c] = peca
                    movimentos.append((peca, inicio - 1 - k, (destino - k, c)))
        return movimentos

    # ------------------------------------------------------------ jogadas possíveis
    def _valida(self, a, b):
        pa, pb = self.peca(a), self.peca(b)
        if pa is None or pb is None:
            return False
        if ARCO in (pa.especial, pb.especial) or (pa.especial and pb.especial):
            return True
        self._trocar(a, b)
        combina = any(a in seq or b in seq for _, seq in self._sequencias())
        self._trocar(a, b)
        return combina

    def jogadas(self):
        """Todas as trocas que combinam: [((l, c), (l, c))]."""
        achadas = []
        for l, c in self.casas():
            for viz in ((l, c + 1), (l + 1, c)):
                if self.livre(*viz) and self._valida((l, c), viz):
                    achadas.append(((l, c), viz))
        return achadas

    def dica(self):
        for l, c in self.casas():
            for viz in ((l, c + 1), (l + 1, c)):
                if self.livre(*viz) and self._valida((l, c), viz):
                    return (l, c), viz
        return None

    def embaralhar(self):
        """Sem jogadas: mistura as peças (as mesmas) até não haver combinação pronta e haver jogada."""
        casas = [casa for casa in self.casas() if self.peca(casa) is not None]
        pecas = [self.peca(casa) for casa in casas]
        for _ in range(300):
            self.sorteio.shuffle(pecas)
            for (l, c), peca in zip(casas, pecas):
                self.grade[l][c] = peca
            if not self._sequencias() and self.dica() is not None:
                return True
        for l, c in casas:                              # último recurso: peças novas
            self.grade[l][c] = None
        self._preencher()
        return False

    # ------------------------------------------------------------ atalhos (robô e testes)
    def jogar(self, a, b):
        """Faz a jogada inteira de uma vez (todas as ondas). Devolve os pontos ganhos ou None se inválida."""
        onda = self.trocar(a, b)
        if onda is None:
            return None
        antes = self.pontos
        while onda:
            self.aplicar(onda)
            self.cair()
            onda = self.proxima_onda()
        if self.dica() is None:
            self.embaralhar()
        return self.pontos - antes
