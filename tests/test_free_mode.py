"""Regras do Modo Livre (gameplay/free_mode.py)."""
import pygame
import pytest

from scenarios import FakeClock

from flappy_arcade.config.difficulty_profiles import LIVRE_SEGUNDOS_POR_NIVEL, NIVEIS
from flappy_arcade.core.event_bus import EventBus
from flappy_arcade.gameplay.difficulty_curve import CurvaDificuldade
from flappy_arcade.gameplay.free_mode import FreeSession
from flappy_arcade.systems.audio_manager import AudioManager
from flappy_arcade.systems.save_manager import SaveManager
from flappy_arcade.systems.settings_store import SettingsStore

curva = CurvaDificuldade()


def criar(recursos, caminho_save):
    bus = EventBus()
    save = SaveManager(caminho_save)
    save.load()
    audio = AudioManager(SettingsStore(save, bus), recursos.sons, bus)
    clock = FakeClock()
    sessao = FreeSession(recursos, audio, clock, save)

    def passo(n=1, desenhar=False):
        for _ in range(n):
            clock.avancar()
            sessao.atualizar(1 / 30, clock.ticks())
            if desenhar:
                sessao.desenhar()
    return sessao, passo


def espaco(sessao):
    sessao.tratar_evento(pygame.event.Event(
        pygame.KEYDOWN, key=pygame.K_SPACE, unicode=' ', mod=0, scancode=0))


@pytest.fixture
def livre(recursos, tmp_path):
    sessao, passo = criar(recursos, tmp_path / 'save.json')
    espaco(sessao)
    return sessao, passo


def test_espaco_no_menu_comeca_sem_cadastro(recursos, tmp_path):
    sessao, _ = criar(recursos, tmp_path / 'save.json')
    assert sessao.estado == 'MENU'
    espaco(sessao)
    assert sessao.estado == 'JOGO'


def test_nunca_tem_game_over(livre):
    sessao, passo = livre
    passo(3000, desenhar=True)             # sem bater asas: cai sem parar por 100 s
    assert sessao.estado == 'JOGO'
    assert sessao.quedas >= 10


def test_dificuldade_sobe_com_o_tempo_e_para_no_25(livre):
    sessao, passo = livre
    assert sessao.nivel_livre == 1
    sessao.tempo_livre = 3 * LIVRE_SEGUNDOS_POR_NIVEL - 0.01
    passo(2)
    assert sessao.nivel_livre == 4
    assert sessao.params_nivel == curva.flappy(4)
    assert sessao.passaro.gravidade == curva.flappy(4)['gravidade']
    sessao.tempo_livre = 10_000
    passo()
    assert sessao.nivel_livre == NIVEIS


def test_pausa_nao_conta_tempo(livre):
    sessao, passo = livre
    pygame_p = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p, unicode='p', mod=0, scancode=0)
    sessao.tratar_evento(pygame_p)
    antes = sessao.tempo_livre
    passo(90)
    assert sessao.tempo_livre == antes


def test_ciclos_continuam_depois_do_10(livre):
    sessao, passo = livre
    sessao.definir_nivel(10)
    sessao.especial = True                  # fase dos pássaros do ciclo 10...
    sessao.fim_passaros_em = sessao.pontos  # ...já cumprida
    passo()
    assert sessao.estado == 'JOGO' and sessao.nivel == 11
    assert sessao.pendentes == ['DONKEY', 'GALAGA']   # ciclo ímpar começa pelo Donkey


@pytest.mark.parametrize('variante', ['GALAGA', 'DONKEY'])
def test_fases_especiais_usam_a_curva_e_nao_acabam_o_jogo(livre, variante):
    sessao, passo = livre
    sessao.nivel_livre = 12
    sessao.iniciar_fase_especial(variante)
    fase = sessao.galaga if variante == 'GALAGA' else sessao.donkey
    assert fase.cfg == getattr(curva, variante.lower())(12)
    for _ in range(8):                      # várias batidas seguidas
        fase.dano = True
        passo(40)
    assert sessao.estado == variante
    assert sessao.quedas >= 8


def test_recorde_de_sequencia_vai_para_o_save(recursos, tmp_path):
    caminho = tmp_path / 'save.json'
    sessao, passo = criar(recursos, caminho)
    espaco(sessao)
    sessao.pontos += 7
    passo()
    assert (sessao.sequencia, sessao.melhor_sequencia) == (7, 7)
    sessao.perder_vida(sessao.clock.ticks() + 5000)
    assert sessao.sequencia == 0
    assert SaveManager(caminho).load()['records']['free_best_streak'] == 7

    sessao.pontos += 3                      # sequência menor não apaga o recorde
    passo()
    sessao.encerrar()
    assert SaveManager(caminho).load()['records']['free_best_streak'] == 7

    nova, _ = criar(recursos, caminho)      # a tela inicial mostra o recorde salvo
    assert nova.recorde == 7


def test_app_abre_no_modo_livre(monkeypatch, tmp_path):
    import flappy_arcade.core.app as modulo_app
    from flappy_arcade.scenes.game_scene import GameScene
    monkeypatch.setattr(modulo_app, 'ARQUIVO_SAVE', tmp_path / 'save.json')
    app = modulo_app.App()
    cena = GameScene(app.ctx, 'livre')
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=' ', mod=0, scancode=0))
    assert app.run(cena, max_quadros=60) == 60
    assert isinstance(cena.session, FreeSession) and cena.session.estado == 'JOGO'


def test_painel_nao_encosta_no_aviso_central(recursos, tmp_path):
    """Com números grandes, o painel da direita não toca o "FASE DOS PÁSSAROS!"."""
    from flappy_arcade.config.constants import LARGURA
    sessao, _ = criar(recursos, tmp_path / 'save.json')
    espaco(sessao)
    sessao.iniciar_fase_passaros()
    sessao.quedas, sessao.sequencia, sessao.pontos = 888, 888, 888
    sessao.recordes['free_best_streak'] = 888
    sessao.nivel_livre = NIVEIS

    def pixels_acesos(desenhar):
        sessao.tela.fill((0, 0, 0))
        desenhar()
        return _invertida(sessao.tela)

    painel = pixels_acesos(lambda: sessao.desenhar_placar(com_nivel=True))
    aviso = pixels_acesos(lambda: sessao.texto('FASE DOS PÁSSAROS!', LARGURA // 2, 95,
                                               (255, 220, 90), centro=True))
    assert aviso.count() > 0
    assert painel.overlap_area(aviso, (0, 0)) == 0


def _invertida(superficie):
    mascara = pygame.mask.from_threshold(superficie, (0, 0, 0), (1, 1, 1, 255))
    mascara.invert()
    return mascara


def test_atalhos_mais_e_menos_vao_ate_o_25(livre, monkeypatch):
    from flappy_arcade.gameplay import classic_session
    monkeypatch.setattr(classic_session, 'MODO_TESTE', True)
    sessao, passo = livre

    def tecla(key):
        sessao.tratar_evento(pygame.event.Event(pygame.KEYDOWN, key=key, unicode='', mod=0, scancode=0))

    for _ in range(14):
        tecla(pygame.K_EQUALS)
    assert sessao.nivel_livre == 15
    assert sessao.passaro.gravidade == curva.flappy(15)['gravidade']
    for _ in range(30):
        tecla(pygame.K_KP_PLUS)
    assert sessao.nivel_livre == NIVEIS
    tecla(pygame.K_MINUS)
    assert sessao.nivel_livre == NIVEIS - 1
    passo(5)                                 # o tempo não "puxa" o nível de volta
    assert sessao.nivel_livre == NIVEIS - 1
    assert sessao.modo_teste_usado
