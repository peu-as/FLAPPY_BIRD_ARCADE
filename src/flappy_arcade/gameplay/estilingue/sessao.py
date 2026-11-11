"""Sessão do Estilingue: uma casa do mapa, do primeiro lançamento ao resultado.

Cumpre o mesmo contrato das outras sessões de casa (veja scenes/level_scene.py):
atualizar, desenhar, tratar_evento, resultado, estrelas, moedas_coletadas,
objetivo, chefe, preparar_recompensas e preparar_cenarios.

Etapas: SOBREVOO (a câmera mostra a fortaleza e volta) -> MIRA -> VOO ->
ESPERA (o mundo acalmar) -> MIRA ... até não sobrar inseto (VITÓRIA) ou
pássaro (DERROTA).

Controles
  Mouse: arraste para trás em qualquer lugar e solte; clique no ar = habilidade;
         roda = olhar a fortaleza.
  Teclado: setas mudam ângulo (cima/baixo) e força (esquerda/direita);
           ESPAÇO lança e, no ar, usa a habilidade; A/D olham para os lados.
"""
import math

import pygame

from ...config import estilingue as cfg
from ...config.constants import ALTURA, LARGURA, Y_CHAO
from ...ui.theme import Palette
from ...ui.widgets import desenhar_texto, texto
from ..coins import icone_moeda
from ..tutorial import GuiaDicas
from .mundo import BARRIL, BLOCO, CHEFE, INSETO, Mundo
from .visual import Visual

SOBREVOO, MIRA, VOO, ESPERA = 'SOBREVOO', 'MIRA', 'VOO', 'ESPERA'
SOM_DO_MATERIAL = {'gelo': 'gelo', 'madeira': 'madeira', 'pedra': 'pedra'}
DICA_DO_PASSARO = {'pena': 'est_pena', 'foguete': 'est_foguete', 'ovo': 'est_ovo'}
DT = 1 / 30                        # a física anda um quadro de 30 FPS por chamada
ANCORA = (cfg.X_ESTILINGUE, Y_CHAO - cfg.ALTURA_ESTILINGUE)
CAMERA_MAXIMA = cfg.LARGURA_MUNDO - LARGURA
TEMPO_SOBREVOO = (1.4, 1.2)        # parado na fortaleza, depois volta
LIMITE_ESPERA = 5.0                # s esperando o mundo acalmar depois do voo
PUXADA_MINIMA = 22
PONTOS_MIRA = 14


def _suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class EstilingueSession:
    estado = 'JOGO'                # para a pausa: a partida está em andamento
    pausado = False
    TEXTO_ATALHOS = 'P ou ESC: Pausa'

    def __init__(self, recursos, audio, clock, casa):
        self.recursos, self.audio, self.clock = recursos, audio, clock
        self.casa = casa
        self.definicao = cfg.casa_estilingue(casa)
        self.mundo = Mundo(self.definicao)
        self.visual = Visual(recursos)
        self.tela = pygame.Surface((LARGURA, ALTURA))
        self.fila = list(self.definicao.passaros)
        self.guia = GuiaDicas()                 # sem registro: nenhuma dica (testes, robôs)
        self.total_passaros = len(self.fila)
        self.usados = 0
        self.etapa = SOBREVOO
        self.tempo_etapa = 0.0
        self.tempo = 0.0
        self.camera = float(self._camera_fortaleza())
        self.olhar = 0.0                       # deslocamento pedido pelo jogador na mira
        self.puxada = None                     # vetor (dx, dy) do elástico, em px
        self.arrastando = False
        self.origem_arraste = (0, 0)
        self.calma = 0.0
        self.mira_teclado = None               # (ângulo em graus, força 0..1)
        self.atual = None                      # pássaro voando (o que recebe a habilidade)
        self.pontos = 0
        self.moedas_coletadas = 0
        self.blocos_quebrados = 0
        self.resultado = None
        self.estrelas = 0
        self.banner_tempo = 3.0 if self.definicao.dica else 0.0
        self.skin = None
        self.efeitos = True
        self.efeitos_bonus = True
        self.saldo_inicial = 0

    # ------------------------------------------------------------ contrato da casa
    @property
    def chefe(self):
        return bool(self.definicao.chefe)

    @property
    def objetivo(self):
        alvos = len(self.mundo.alvos)
        chefes = sum(1 for p in self.mundo.alvos if p.tipo == CHEFE)
        insetos = alvos - chefes
        if chefes:
            quem = ('os dois chefões' if chefes > 1 else 'o chefão') + (
                f' e {"o inseto" if insetos == 1 else f"os {insetos} insetos"}' if insetos else '')
        else:
            quem = 'o inseto' if alvos == 1 else f'os {alvos} insetos'
        return f'Derrube {quem} com {self.total_passaros} pássaros. 3 estrelas: sobrando 2.'

    def preparar_recompensas(self, skin=None, saldo=0, efeitos=True, moedas=True):
        self.skin = skin
        self.saldo_inicial = saldo
        self.efeitos = self.visual.efeitos = efeitos

    def preparar_tutorial(self, registro):
        """Dicas na primeira vez de cada coisa (a cena da casa entrega o registro do save)."""
        self.guia = GuiaDicas(registro)

    def _pedir_dicas(self):
        self.guia.pedir('est_mirar')
        if self.fila and self.fila[0] in DICA_DO_PASSARO:
            self.guia.pedir(DICA_DO_PASSARO[self.fila[0]])
        if any(p.tipo == BARRIL for p in self.mundo.pecas):
            self.guia.pedir('est_barril')
        if self.chefe:
            self.guia.pedir('est_chefe')

    def preparar_cenarios(self, diretor, efeitos=True):
        self.visual.preparar_fundo(diretor.gerenciador.fundo(diretor.atual))

    # ------------------------------------------------------------ geometria
    def _camera_fortaleza(self):
        xs = [p.posicao.x for p in self.mundo.pecas if not p.morta]
        return min(CAMERA_MAXIMA, max(0, (max(xs) if xs else cfg.LARGURA_MUNDO) - LARGURA + 80))

    def _ancora_tela(self):
        return (ANCORA[0] - self.camera, ANCORA[1])

    def velocidade_da_puxada(self, puxada):
        return (-puxada[0] * cfg.FORCA_LANCAMENTO, -puxada[1] * cfg.FORCA_LANCAMENTO)

    @staticmethod
    def puxada_do_teclado(angulo, forca):
        r = cfg.PUXADA_MAXIMA * forca
        return (-r * math.cos(math.radians(angulo)), r * math.sin(math.radians(angulo)))

    @staticmethod
    def _limitar(dx, dy):
        tamanho = math.hypot(dx, dy)
        if tamanho > cfg.PUXADA_MAXIMA:
            dx, dy = dx / tamanho * cfg.PUXADA_MAXIMA, dy / tamanho * cfg.PUXADA_MAXIMA
        return dx, dy

    def trajetoria(self, puxada):
        """Pontos da mira: o começo do voo (balística simples, sem colisões)."""
        vx, vy = self.velocidade_da_puxada(puxada)
        pontos = []
        for i in range(1, PONTOS_MIRA + 1):
            t = i * 0.055
            x, y = ANCORA[0] + vx * t, ANCORA[1] + vy * t + cfg.GRAVIDADE * t * t / 2
            if y > Y_CHAO:
                break
            pontos.append((x, y))
        return pontos

    # ------------------------------------------------------------ ações
    def lancar(self, puxada):
        """Solta o elástico (puxada em px, relativa à âncora)."""
        if self.etapa != MIRA or not self.fila or math.hypot(*puxada) < PUXADA_MINIMA:
            return False
        tipo = self.fila.pop(0)
        self.usados += 1
        # O elástico solta o pássaro pela forquilha (a âncora): é dali que a mira desenha o
        # voo e de onde o robô de calibração lança. Também nunca nasce encostado no chão.
        self.atual = self.mundo.lancar(tipo, ANCORA, self.velocidade_da_puxada(puxada))
        self.visual.rastro_anterior, self.visual.rastro = self.visual.rastro, []
        self.puxada, self.arrastando, self.mira_teclado = None, False, None
        self._mudar(VOO)
        self.guia.acao()
        self.audio.play_sfx('lancar', 0.55)
        return True

    def usar_habilidade(self):
        if self.etapa == VOO and self.atual is not None and self.mundo.ativar(self.atual):
            if self.atual.nome == 'pena':
                filhotes = [p for p in self.mundo.passaros_no_ar if p.filhote]
                self.atual = filhotes[len(filhotes) // 2] if filhotes else None
            self.audio.play_sfx('habilidade', 0.45)
            return True
        return False

    def acao_principal(self):
        """O mesmo que o ESPAÇO: pula o sobrevoo, lança com a mira do teclado ou usa a habilidade."""
        self._tecla(pygame.K_SPACE)

    def _mudar(self, etapa):
        self.etapa, self.tempo_etapa = etapa, 0.0

    # ------------------------------------------------------------ entrada
    def tratar_evento(self, evento):
        """Mouse e teclado. Retorna False para sair (nunca: a saída é pela pausa)."""
        if self.resultado:
            return True
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            if self.etapa == SOBREVOO:
                self._mudar(MIRA)                        # pular o sobrevoo
            elif self.etapa == MIRA and self.fila:
                self.arrastando, self.olhar = True, 0.0
                self.origem_arraste, self.puxada = evento.pos, (0.0, 0.0)
            elif self.etapa == VOO:
                self.usar_habilidade()
        elif evento.type == pygame.MOUSEMOTION and self.arrastando:
            if not getattr(evento, 'buttons', (1,))[0]:          # o botão foi solto fora daqui (pausa)
                self.puxada, self.arrastando = None, False
            else:
                self._puxar(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1 and self.arrastando:
            if not (self.puxada and self.lancar(self.puxada)):
                self.puxada, self.arrastando = None, False
        elif evento.type == pygame.MOUSEWHEEL and self.etapa == MIRA:
            self.olhar = max(0.0, min(CAMERA_MAXIMA, self.olhar - evento.y * 90))
        elif evento.type == pygame.KEYDOWN:
            self._tecla(evento.key)
        return True

    def _puxar(self, pos):
        """Puxar para trás (e para baixo) a partir de onde o clique começou mira para a frente (e para cima)."""
        dx, dy = pos[0] - self.origem_arraste[0], pos[1] - self.origem_arraste[1]
        self.puxada = self._limitar(dx, dy)

    def _tecla(self, tecla):
        if self.etapa == SOBREVOO and tecla in (pygame.K_SPACE, pygame.K_RETURN):
            self._mudar(MIRA)
            return
        if self.etapa == VOO and tecla in (pygame.K_SPACE, pygame.K_RETURN):
            self.usar_habilidade()
            return
        if self.etapa != MIRA:
            return
        if tecla in (pygame.K_a, pygame.K_d):
            self.olhar = max(0.0, min(CAMERA_MAXIMA, self.olhar + (360 if tecla == pygame.K_d else -360)))
            return
        angulo, forca = self.mira_teclado or (35.0, 0.8)
        if tecla == pygame.K_UP:
            angulo = min(80.0, angulo + 2)
        elif tecla == pygame.K_DOWN:
            angulo = max(-10.0, angulo - 2)
        elif tecla == pygame.K_RIGHT:
            forca = min(1.0, forca + 0.04)
        elif tecla == pygame.K_LEFT:
            forca = max(0.25, forca - 0.04)
        elif tecla in (pygame.K_SPACE, pygame.K_RETURN):
            self.lancar(self.puxada_do_teclado(angulo, forca))
            return
        else:
            return
        self.mira_teclado, self.olhar = (angulo, forca), 0.0
        self.puxada = self.puxada_do_teclado(angulo, forca)

    # ------------------------------------------------------------ quadro
    def atualizar(self, dt=DT, agora_ms=0):
        if self.resultado:
            return
        self.tempo += DT
        self.tempo_etapa += DT
        self.banner_tempo = max(0.0, self.banner_tempo - DT)
        if self.etapa == SOBREVOO:
            if self.tempo_etapa >= sum(TEMPO_SOBREVOO):
                self._mudar(MIRA)
        else:
            self.mundo.passo(DT)
            self._eventos()
            self._seguir_etapas()
        if self.etapa == MIRA:
            self._pedir_dicas()
        self.guia.atualizar(DT)
        self.visual.atualizar(DT)
        self._mover_camera()

    def _eventos(self):
        for tipo, dado in self.mundo.consumir_eventos():
            if tipo == 'quebrou':
                self.pontos += dado.pontos
                self.visual.ao_quebrar(dado)
                if dado.tipo == BLOCO:
                    self.audio.play_sfx(SOM_DO_MATERIAL.get(dado.material, 'madeira'), 0.45)
                    self.blocos_quebrados += 1
                    if self.blocos_quebrados % cfg.BLOCOS_POR_MOEDA == 0:
                        self._ganhar_moedas(1, dado.posicao)
                elif dado.tipo in (INSETO, CHEFE):
                    self._ganhar_moedas(cfg.MOEDAS_POR_CHEFE if dado.tipo == CHEFE else cfg.MOEDAS_POR_INSETO,
                                        dado.posicao)
                    self.audio.play_sfx('inseto', 0.5)
                    self.audio.play_sfx('ponto', 0.35)
                else:
                    self.audio.play_sfx('colisao', 0.4)
            elif tipo == 'explodiu':
                self.visual.ao_explodir(*dado)
                self.audio.play_sfx('explosao', 0.6)
            elif tipo == 'bateu':
                self.audio.play_sfx('colisao', 0.3)

    def _ganhar_moedas(self, quantidade, posicao):
        self.moedas_coletadas += quantidade
        self.visual.texto(posicao[0], posicao[1] - 56, f'+{quantidade}', Palette.COIN)

    def _seguir_etapas(self):
        if self.etapa == VOO:
            if self.atual is not None and not self.atual.morta:
                self.visual.rastro.append(tuple(self.atual.posicao))
            elif self.mundo.passaros_no_ar:
                self.atual = self.mundo.passaros_no_ar[-1]
            if not self.mundo.passaros_no_ar or not self.mundo.alvos:   # sem insetos: nem espera o pássaro
                self._mudar(ESPERA)
        elif self.etapa == ESPERA:
            self.calma = self.calma + DT if not self.mundo.em_movimento() else 0.0
            acabou = self.calma >= cfg.SEGUNDOS_PARA_ACALMAR or self.tempo_etapa >= LIMITE_ESPERA
            if acabou or not self.mundo.alvos:           # sem insetos: vitória sem esperar
                self.calma = 0.0
                self._fim_da_jogada()

    def _fim_da_jogada(self):
        if not self.mundo.alvos:
            sobrando = len(self.fila)
            self.pontos += sobrando * cfg.PONTOS_PASSARO_SOBRANDO
            self.moedas_coletadas += sobrando * cfg.MOEDAS_POR_PASSARO_SOBRANDO + cfg.MOEDAS_POR_VITORIA
            self.estrelas = cfg.estrelas_estilingue(self.total_passaros, self.usados)
            self.resultado = 'VITORIA'
        elif not self.fila:
            self.resultado = 'DERROTA'
            self.audio.play_sfx('morte', 0.5)
        else:
            self.atual = None
            self._mudar(MIRA)

    def _mover_camera(self):
        if self.etapa == SOBREVOO:
            parado, volta = TEMPO_SOBREVOO
            inicio = self._camera_fortaleza()
            alvo = inicio * (1 - _suave((self.tempo_etapa - parado) / volta))
            self.camera = alvo
            return
        if self.etapa == VOO and self.atual is not None and not self.atual.morta:
            alvo = self.atual.posicao.x - LARGURA * 0.4
        elif self.etapa == ESPERA:
            alvo = self.camera
        else:
            alvo = self.olhar
        alvo = max(0.0, min(CAMERA_MAXIMA, alvo))
        self.camera += (alvo - self.camera) * (0.25 if self.etapa == VOO else 0.12)

    # ------------------------------------------------------------ desenho
    def desenhar(self):
        tela, camera = self.tela, self.camera
        v = self.visual
        v.desenhar_fundo(tela, camera)
        v.desenhar_rastros(tela, camera)
        puxada_tela = None
        if self.etapa == MIRA and self.fila:
            ax, ay = self._ancora_tela()
            dx, dy = self.puxada or (0, 0)
            puxada_tela = (round(ax + dx), round(ay + dy))
        v.desenhar_estilingue(tela, camera, ANCORA, puxada_tela, frente=False)
        if puxada_tela is not None:
            angulo = 0.0
            if self.puxada and math.hypot(*self.puxada) > 4:          # o pássaro olha para onde vai
                angulo = math.degrees(math.atan2(self.puxada[1], -self.puxada[0]))
            v.desenhar_passaro_no_estilingue(tela, puxada_tela, self.fila[0], self.skin, angulo)
        v.desenhar_estilingue(tela, camera, ANCORA, puxada_tela, frente=True)
        if self.puxada and math.hypot(*self.puxada) >= PUXADA_MINIMA and self.etapa == MIRA:
            v.desenhar_mira(tela, camera, self.trajetoria(self.puxada))
        v.desenhar_fila(tela, camera, self.fila, self.skin, preparado=self.etapa == MIRA)
        v.desenhar_pecas(tela, camera, self.mundo, self.skin, self.tempo)
        v.desenhar_passaros(tela, camera, self.mundo, self.skin)
        v.desenhar_efeitos(tela, camera)
        self._hud(tela)

    def _hud(self, tela):
        desenhar_texto(tela, f'{self.pontos:,}'.replace(',', '.'), 34, topo_esquerdo=(14, 10),
                       cor=Palette.WHITE, espessura=3)
        icone = icone_moeda(10)
        tela.blit(icone, (16, 52))
        desenhar_texto(tela, f'+{self.moedas_coletadas}', 24, topo_esquerdo=(40, 48), cor=Palette.COIN)
        chefes = sum(1 for p in self.mundo.alvos if p.tipo == CHEFE)
        insetos = len(self.mundo.alvos) - chefes
        contador = f'INSETOS: {insetos}' + (f'  CHEFÕES: {chefes}' if chefes else '')
        img = texto(contador, 26, Palette.WHITE)
        tela.blit(img, img.get_rect(topright=(LARGURA - 14, 12)))
        x = LARGURA - 18
        for tipo in reversed(self.fila):
            item = cfg.PASSAROS[tipo].item
            mini = (self.visual.estilo.itens[item] if item else
                    self.visual.sprite_passaro(tipo, self.skin, 12))
            mini = pygame.transform.smoothscale(mini, (24, round(24 * mini.get_height() / mini.get_width())))
            tela.blit(mini, mini.get_rect(topright=(x, 44)))
            x -= 30
        tela.blit(texto(self.TEXTO_ATALHOS, 20, Palette.WHITE), (14, ALTURA - 30))
        dica = self._dica()
        if dica:
            img = texto(dica, 22, Palette.WHITE)
            tela.blit(img, img.get_rect(center=(LARGURA // 2, ALTURA - 60)))
        if self.banner_tempo > 0 and self.definicao.dica:
            img = texto(self.definicao.dica, 28, Palette.BIRD_YELLOW, Palette.INK, 3)
            img.set_alpha(min(255, int(self.banner_tempo * 255)))
            tela.blit(img, img.get_rect(center=(LARGURA // 2, 120)))
        self.guia.desenhar(tela, 190)

    def _dica(self):
        if self.etapa == SOBREVOO:
            return 'Clique ou ESPAÇO para pular'
        if self.etapa == MIRA and self.fila:
            tipo = cfg.PASSAROS[self.fila[0]]
            base = 'Arraste para trás e solte  -  setas + ESPAÇO'
            return f'{tipo.nome}: {tipo.dica}' if tipo.item else base
        if self.etapa == VOO and self.atual is not None and self.mundo.pode_ativar(self.atual):
            return 'Clique ou ESPAÇO: habilidade!'
        return ''
