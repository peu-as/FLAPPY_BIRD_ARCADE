"""Playtest automatizado: um robô com limites humanos joga as casas dos mapas.

    python tools/playtest.py                    Flappy e Galaga, casas 1 a 25
    python tools/playtest.py --tentativas 30    mais tentativas (mais preciso, mais lento)
    python tools/playtest.py --mapas flappy     só um mapa
    python tools/playtest.py --habilidade experiente

Use depois de mexer em config/difficulty_profiles.py: a taxa de vitória deve
cair de forma gradual, sem degraus bruscos entre casas vizinhas.

Limites humanos do robô:
  * reação: decide com o que "viu" alguns quadros atrás;
  * ritmo: no máximo um toque a cada QUADROS_ENTRE_TOQUES (o mesmo do cálculo
    de justiça do jogo);
  * imprecisão: mira um ponto sorteado em volta do centro da passagem.
O Donkey Kong fica de fora: desviar de salvas de barris exige planejamento que
um robô simples faria mal, e o número enganaria mais do que ajudaria.
"""
import argparse
import json
import os
import random
import statistics
import sys
from collections import deque
import multiprocessing
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('FLAPPY_DATA_DIR', str(Path(os.environ.get('TEMP', '/tmp')) / 'flappy-playtest'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

import pygame  # noqa: E402

from flappy_arcade.config.constants import QUADROS_ENTRE_TOQUES, Y_NAVE  # noqa: E402
from flappy_arcade.config.levels import CASAS  # noqa: E402

FPS = 30
LIMITE_QUADROS = 30 * FPS * 6        # 3 minutos por tentativa, no máximo

# reação (quadros), imprecisão da mira (px) e intervalo das decisões na Galaga (quadros)
HABILIDADES = {
    'casual': {'reacao': 6, 'imprecisao': 22, 'decisao_galaga': 9},
    'medio': {'reacao': 4, 'imprecisao': 16, 'decisao_galaga': 6},
    'experiente': {'reacao': 2, 'imprecisao': 7, 'decisao_galaga': 3},
}


class Relogio:
    def __init__(self):
        self.quadro = 0

    def now(self):
        return 1000.0 + self.quadro / FPS

    def ticks(self):
        return round(self.quadro * 1000 / FPS)


class RoboFlappy:
    MARGEM = 6

    def __init__(self, aleatorio, habilidade):
        self.aleatorio = aleatorio
        self.REACAO = habilidade['reacao']
        self.IMPRECISAO = habilidade['imprecisao']
        self.visto = deque(maxlen=self.REACAO + 1)
        self.ultimo_toque = -99
        self.mirado, self.desvio = None, 0.0

    def jogar(self, sessao, quadro):
        if sessao.estado != 'JOGO':
            return
        p = sessao.passaro
        alvo = next((o for o in sessao.obstaculos if o.x + o.largura > p.x), None)
        if alvo is not None and alvo is not self.mirado:
            self.mirado, self.desvio = alvo, self.aleatorio.gauss(0, self.IMPRECISAO)
        centro = alvo.topo_passagem + alvo.abertura / 2 + self.desvio if alvo else 400
        self.visto.append((p.y + p.sprite.get_height() / 2, p.vy, centro))
        if len(self.visto) <= self.REACAO:
            return
        y, vy, mira = self.visto[0]
        if quadro - self.ultimo_toque >= QUADROS_ENTRE_TOQUES and y > mira + self.MARGEM and vy >= 0:
            sessao.acao_principal()
            self.ultimo_toque = quadro


class RoboGalaga:
    def __init__(self, aleatorio, habilidade):
        self.aleatorio = aleatorio
        self.REACAO = habilidade['decisao_galaga']

    def jogar(self, sessao, quadro):
        fase = sessao.galaga
        if sessao.estado != 'GALAGA' or fase is None:
            return
        sessao.acao_principal()                       # atira sempre que o canhão deixa
        if quadro % self.REACAO:
            return
        perigo = [t for t in fase.tiros if not t.do_jogador and 0 < Y_NAVE - t.y < 160
                  and abs(t.x - fase.nave_x) < 34]
        perigo += [i for i in fase.inimigos if Y_NAVE - 200 < i.y < Y_NAVE + 20
                   and abs(i.x - fase.nave_x) < 50]          # mergulhos chegando
        if perigo:
            lado = 1 if perigo[0].x < fase.nave_x else -1
            fase.alvo_x = max(30, min(545, fase.nave_x + lado * 90))
            return
        if fase.chefe is not None:
            fase.alvo_x = fase.chefe.x
            return
        vivos = [i for i in fase.inimigos if i.y > 0]
        if vivos:
            fase.alvo_x = max(vivos, key=lambda i: i.y).x + self.aleatorio.uniform(-8, 8)


ROBOS = {'flappy': RoboFlappy, 'galaga': RoboGalaga}


def tentar(args):
    mapa, casa, semente, habilidade = args
    pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((575, 860))
    from flappy_arcade.core.event_bus import EventBus
    from flappy_arcade.gameplay.level_session import criar_sessao
    from flappy_arcade.gameplay.resources import Recursos
    from flappy_arcade.systems.audio_manager import AudioManager
    from flappy_arcade.systems.save_manager import SaveManager
    from flappy_arcade.systems.settings_store import SettingsStore
    global _RECURSOS, _AUDIO
    if '_RECURSOS' not in globals():
        _RECURSOS = Recursos()
        bus = EventBus()
        save = SaveManager(Path(os.environ['FLAPPY_DATA_DIR']) / 'playtest.json')
        save.load()
        settings = SettingsStore(save, bus)
        settings.set_many({'sfx': False, 'music': False})
        _AUDIO = AudioManager(settings, _RECURSOS.sons, bus)
    random.seed(semente)
    relogio = Relogio()
    sessao = criar_sessao(mapa, casa, _RECURSOS, _AUDIO, relogio)
    sessao.preparar_recompensas()
    robo = ROBOS[mapa](random.Random(semente * 7919), HABILIDADES[habilidade])
    for quadro in range(LIMITE_QUADROS):
        robo.jogar(sessao, quadro)
        relogio.quadro += 1
        sessao.atualizar(1 / FPS, relogio.ticks())
        if sessao.resultado:
            break
    return {'mapa': mapa, 'casa': casa, 'venceu': sessao.resultado == 'VITORIA',
            'danos': sessao.danos, 'segundos': quadro / FPS, 'moedas': sessao.moedas_coletadas}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--tentativas', type=int, default=12)
    parser.add_argument('--mapas', nargs='+', default=['flappy', 'galaga'], choices=list(ROBOS))
    parser.add_argument('--habilidade', default='medio', choices=list(HABILIDADES))
    parser.add_argument('--json', help='grava os resultados brutos neste arquivo')
    args = parser.parse_args()
    tarefas = [(m, c, s, args.habilidade) for m in args.mapas for c in range(1, CASAS + 1)
               for s in range(args.tentativas)]
    # 'spawn': cada processo começa limpo (fork depois do SDL carregado pode travar)
    with multiprocessing.get_context('spawn').Pool() as pool:
        resultados = pool.map(tentar, tarefas, chunksize=4)
    for mapa in args.mapas:
        print(f'\n{mapa.upper()}  robô {args.habilidade}, {args.tentativas} tentativas por casa, 3 vidas cada')
        print('casa  vitória  estrelas(média nas vitórias)  tempo médio  moedas médias')
        for casa in range(1, CASAS + 1):
            r = [x for x in resultados if x['mapa'] == mapa and x['casa'] == casa]
            vitorias = [x for x in r if x['venceu']]
            taxa = len(vitorias) / len(r)
            estrelas = statistics.mean(max(1, 3 - x['danos']) for x in vitorias) if vitorias else 0
            barra = '#' * round(taxa * 20)
            chefe = '*' if casa % 5 == 0 else ' '
            print(f'{casa:>3}{chefe}  {taxa:6.0%}  {estrelas:4.1f}  {barra:<20s}  '
                  f'{statistics.mean(x["segundos"] for x in r):6.1f} s  {statistics.mean(x["moedas"] for x in r):6.1f}')
    if args.json:
        Path(args.json).write_text(json.dumps(resultados), encoding='utf-8')


if __name__ == '__main__':
    main()
