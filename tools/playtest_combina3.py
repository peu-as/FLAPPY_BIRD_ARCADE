"""Robô do Combina 3: quantos pontos uma partida rende, para calibrar as metas das casas.

Joga partidas inteiras só com as regras (sem tela). Três jogadores:
  aleatorio   qualquer troca válida
  medio       metade das vezes a melhor troca, metade uma qualquer
  bom         quase sempre a troca que mais pontua

    python tools/playtest_combina3.py                      distribuição de pontos (30 jogadas, 6 tipos)
    python tools/playtest_combina3.py --casas              % de vitória e estrelas em cada casa
"""
import argparse
import copy
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from flappy_arcade.gameplay.combina3.tabuleiro import TIPOS, Tabuleiro  # noqa: E402

JOGADORES = {'aleatorio': 0.0, 'medio': 0.5, 'bom': 0.9}


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


def casas(args):
    from flappy_arcade.config import combina3 as cfg
    print('casa  jogadas  tipos   meta    médio: vitórias / estrelas    bom: vitórias / estrelas')
    for numero in range(1, len(cfg.CASAS_COMBINA3) + 1):
        casa = cfg.casa_combina3(numero)
        linha = f'{numero:4d}  {casa.jogadas:7d}  {casa.tipos:5d}  {casa.meta:5d}  '
        for nome in ('medio', 'bom'):
            estrelas = []
            for s in range(args.partidas):
                pontos, usadas = partida(casa.jogadas, casa.tipos, JOGADORES[nome], numero * 1000 + s, casa.meta)
                estrelas.append(cfg.estrelas_combina3(casa.jogadas, usadas) if pontos >= casa.meta else 0)
            vitorias = [e for e in estrelas if e]
            media = statistics.mean(vitorias) if vitorias else 0
            linha += f'   {len(vitorias) * 100 // len(estrelas):3d}% / {media:.1f}              '
        print(linha)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--jogadas', type=int, default=30)
    parser.add_argument('--tipos', type=int, default=6)
    parser.add_argument('--partidas', type=int, default=40)
    parser.add_argument('--casas', action='store_true')
    args = parser.parse_args()
    (casas if args.casas else distribuicao)(args)


if __name__ == '__main__':
    main()
