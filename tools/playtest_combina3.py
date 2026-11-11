"""Robô do Combina 3: calibra as casas jogando partidas inteiras só com as regras (sem tela).

Três jogadores:
  aleatorio   qualquer troca válida
  medio       metade das vezes a troca que mais avança o objetivo, metade uma qualquer
  bom         quase sempre a troca que mais avança o objetivo

    python tools/playtest_combina3.py                      pontos por partida (30 jogadas, sem obstáculos)
    python tools/playtest_combina3.py --casas              % de vitória e estrelas em cada casa
    python tools/playtest_combina3.py --casas 5 10 25      só essas casas

As casas usam gameplay/combina3/partida.py, as mesmas regras do jogo (objetivos,
obstáculos, chefões e ataques).
"""
import argparse
import copy
import os
import random
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from flappy_arcade.config import combina3 as cfg  # noqa: E402
from flappy_arcade.gameplay.combina3.partida import Partida  # noqa: E402
from flappy_arcade.gameplay.combina3.tabuleiro import TIPOS, Tabuleiro  # noqa: E402

JOGADORES = {'aleatorio': 0.0, 'medio': 0.5, 'bom': 0.9}


# ---------------------------------------------------------------- pontos (sem objetivos)
def escolher(tab, sorteio, capricho):
    """Uma troca: com chance `capricho`, a que mais pontua; senão, uma qualquer."""
    jogadas = tab.jogadas()
    if sorteio.random() >= capricho:
        return sorteio.choice(jogadas)
    melhor, pontos_melhor = None, -1
    for a, b in jogadas:
        copia = copy.deepcopy(tab)
        pontos = copia.jogar(a, b)
        if pontos > pontos_melhor:
            melhor, pontos_melhor = (a, b), pontos
    return melhor


def partida(jogadas, tipos, capricho, semente, meta=None, **obstaculos):
    """Joga até acabarem as jogadas (ou bater a meta). Devolve (pontos, jogadas usadas)."""
    tab = Tabuleiro(tipos=TIPOS[:tipos], semente=semente, **obstaculos)
    sorteio = random.Random(semente * 31 + 7)
    for usadas in range(1, jogadas + 1):
        tab.jogar(*escolher(tab, sorteio, capricho))
        if meta is not None and tab.pontos >= meta:
            return tab.pontos, usadas
    return tab.pontos, jogadas


def distribuicao(args):
    print(f'{args.jogadas} jogadas, {args.tipos} tipos de peça, {args.partidas} partidas por jogador')
    print('jogador     p10    p25  mediana    p75    p90   por jogada')
    for nome, capricho in JOGADORES.items():
        pontos = sorted(partida(args.jogadas, args.tipos, capricho, s)[0] for s in range(args.partidas))
        q = lambda f: pontos[int(f * (len(pontos) - 1))]  # noqa: E731
        print(f'{nome:10s} {q(.1):5d}  {q(.25):5d}  {q(.5):7d}  {q(.75):5d}  {q(.9):5d}   {statistics.mean(pontos) / args.jogadas:6.0f}')


# ---------------------------------------------------------------- casas (com objetivos)
def valor(p):
    """O que o robô quer: avançar os objetivos; os pontos só desempatam."""
    return p.fracao() * 1_000_000 + p.tab.pontos


def escolher_na_casa(p, sorteio, capricho):
    jogadas = p.tab.jogadas()
    if sorteio.random() >= capricho:
        return sorteio.choice(jogadas)
    melhor, valor_melhor = None, -1
    for a, b in jogadas:
        copia = copy.deepcopy(p)
        copia.jogar(a, b)
        v = valor(copia)
        if v > valor_melhor:
            melhor, valor_melhor = (a, b), v
    return melhor


def jogar_casa(numero, capricho, semente):
    """Uma partida inteira numa casa. Devolve (estrelas, fração feita) — 0 estrelas = derrota."""
    casa = cfg.casa_combina3(numero)
    p = Partida(casa, semente=semente)
    sorteio = random.Random(semente * 31 + 7)
    while not p.vitoria and not p.derrota:
        p.jogar(*escolher_na_casa(p, sorteio, capricho))
    estrelas = cfg.estrelas_combina3(casa.jogadas, p.usadas) if p.vitoria else 0
    return estrelas, p.fracao()


def _medir(pedido):
    numero, nome, partidas = pedido
    resultados = [jogar_casa(numero, JOGADORES[nome], numero * 1000 + s) for s in range(partidas)]
    return numero, nome, resultados


def casas(args):
    numeros = args.casas or range(1, len(cfg.CASAS_COMBINA3) + 1)
    pedidos = [(n, nome, args.partidas) for n in numeros for nome in ('medio', 'bom')]
    with ProcessPoolExecutor(max_workers=os.cpu_count() or 2) as pool:
        medidas = {(n, nome): r for n, nome, r in pool.map(_medir, pedidos)}
    print(f'{args.partidas} partidas por casa e jogador')
    print('casa  jogadas  objetivos                     médio: vitórias / estrelas / feito   '
          'bom: vitórias / estrelas / feito')
    for n in numeros:
        casa = cfg.casa_combina3(n)
        resumo = ' + '.join(o[0] if o[0] != cfg.COLETAR else f'{o[1]} {o[2]}' for o in casa.objetivos)
        if casa.chefao:
            resumo = f'chefe {casa.chefao.nome} {casa.chefao.vida}'
        elif cfg.PONTOS in (o[0] for o in casa.objetivos):
            resumo += f' {casa.objetivos[0][1]}'
        linha = f'{n:4d}  {casa.jogadas:7d}  {resumo:28s}'
        for nome in ('medio', 'bom'):
            r = medidas[(n, nome)]
            vitorias = [e for e, _ in r if e]
            media = statistics.mean(vitorias) if vitorias else 0
            feito = statistics.mean(f for _, f in r)
            linha += f'   {len(vitorias) * 100 // len(r):3d}% / {media:.1f} / {feito * 100:3.0f}%        '
        print(linha, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--jogadas', type=int, default=30)
    parser.add_argument('--tipos', type=int, default=6)
    parser.add_argument('--partidas', type=int, default=30)
    parser.add_argument('--casas', type=int, nargs='*', default=None)
    args = parser.parse_args()
    (casas if args.casas is not None else distribuicao)(args)


if __name__ == '__main__':
    main()
