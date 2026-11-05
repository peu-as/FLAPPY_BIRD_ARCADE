"""Cenas e pilha de cenas.

Cada tela do jogo (menu, mapa, partida, loja, pausa...) é uma Scene. O
SceneManager guarda uma pilha: só a cena do topo recebe eventos e é
atualizada. Cenas marcadas como overlay (pausa, configurações) deixam a cena
de baixo visível, congelada, por trás delas.
"""


class Scene:
    """Base de todas as telas. Sobrescreva só o que precisar."""

    fps = 60            # taxa de quadros desejada enquanto esta cena está no topo
    is_overlay = False  # True: a cena de baixo continua sendo desenhada

    def __init__(self, ctx):
        self.ctx = ctx
        self.manager = None

    def on_enter(self):
        """Chamado ao entrar no topo da pilha (inclusive ao voltar a ele)."""

    def on_exit(self):
        """Chamado ao sair do topo da pilha."""

    def handle_event(self, event):
        """Recebe eventos do pygame; posições de mouse já são lógicas."""

    def update(self, dt):
        """Avança a lógica; dt em segundos."""

    def draw(self, surface):
        """Desenha na superfície lógica (575x860)."""


class SceneManager:
    def __init__(self):
        self._pilha = []

    @property
    def top(self):
        return self._pilha[-1] if self._pilha else None

    @property
    def empty(self):
        return not self._pilha

    def push(self, cena):
        if self.top:
            self.top.on_exit()
        cena.manager = self
        self._pilha.append(cena)
        cena.on_enter()

    def pop(self):
        if not self._pilha:
            return None
        cena = self._pilha.pop()
        cena.on_exit()
        if self.top:
            self.top.on_enter()
        return cena

    def replace(self, cena):
        """Troca a cena do topo (ex.: menu -> mapa) sem empilhar."""
        if self._pilha:
            self._pilha.pop().on_exit()
        cena.manager = self
        self._pilha.append(cena)
        cena.on_enter()

    def clear(self):
        while self._pilha:
            self._pilha.pop().on_exit()

    def handle_event(self, event):
        if self.top:
            self.top.handle_event(event)

    def update(self, dt):
        if self.top:
            self.top.update(dt)

    def draw(self, surface):
        # desenha a partir da cena opaca mais alta; overlays vão por cima
        inicio = len(self._pilha) - 1
        while inicio > 0 and self._pilha[inicio].is_overlay:
            inicio -= 1
        for cena in self._pilha[max(inicio, 0):]:
            cena.draw(surface)
