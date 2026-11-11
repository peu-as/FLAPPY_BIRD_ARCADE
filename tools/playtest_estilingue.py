"""Robô do Estilingue: confere se cada casa dá para vencer e com quantas estrelas.

Para cada pássaro, testa uma grade de ângulos, forças e momentos de usar a
habilidade e fica com a jogada que mais derruba (alvos primeiro, depois
pontos). O mundo é refeito a cada teste e as jogadas anteriores são
repetidas (a física é determinística).

O robô mira "bem demais" (busca exaustiva): se ele não vence uma casa, um
humano também não vai vencer. Use para balancear a tabela CASAS_ESTILINGUE.

    python tools/playtest_estilingue.py                 todas as casas
    python tools/playtest_estilingue.py --casas 1 5 10
    python tools/playtest_estilingue.py --rapido        grade menor
    python tools/playtest_estilingue.py --humano 8      robô com erro de mira humano, 8 tentativas
                                                        por casa: % de vitória e estrelas médias
"""
import argparse
import math
import multiprocessing
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from flappy_arcade.config import estilingue as cfg  # noqa: E402
from flappy_arcade.config.constants import Y_CHAO  # noqa: E402
from flappy_arcade.gameplay.estilingue.mundo import Mundo  # noqa: E402

DT = 1 / 30
ANCORA = (cfg.X_ESTILINGUE, Y_CHAO - cfg.ALTURA_ESTILINGUE)


def velocidade(angulo, forca):
    v = cfg.PUXADA_MAXIMA * forca * cfg.FORCA_LANCAMENTO
    rad = math.radians(angulo)
    return (v * math.cos(rad), -v * math.sin(rad))


def jogar(mundo, tipo, jogada):
    """Lança um pássaro e roda até o mundo acalmar. Devolve quadros gastos."""
    angulo, forca, quando = jogada
    passaro = mundo.lancar(tipo, ANCORA, velocidade(angulo, forca))
    calmo, quadros = 0.0, 0
    while quadros < int(cfg.LIMITE_JOGADA / DT) + 60:
        if quando is not None and mundo.pode_ativar(passaro) and quadros * DT >= quando:
            mundo.ativar(passaro)
        mundo.passo(DT)
        quadros += 1
        calmo = calmo + DT if not mundo.em_movimento() else 0.0
        if calmo >= cfg.SEGUNDOS_PARA_ACALMAR:
            break
    mundo.consumir_eventos()
    return quadros


def reconstruir(casa, jogadas):
    mundo = Mundo(casa)
    for tipo, jogada in zip(casa.passaros, jogadas):
        jogar(mundo, tipo, jogada)
    return mundo


def grade(tipo, rapido):
    angulos = range(8, 72, 6 if rapido else 4)
    forcas = (0.7, 0.85, 1.0) if rapido else (0.6, 0.7, 0.8, 0.9, 1.0)
    momentos = [None] if tipo == 'comum' else [None, 0.5, 0.8, 1.1] if tipo != 'ovo' else [None, 0.7, 1.0, 1.3]
    return [(a, f, m) for a in angulos for f in forcas for m in momentos]


def resolver(args):
    numero, rapido = args
    casa = cfg.casa_estilingue(numero)
    jogadas = []
    for usados, tipo in enumerate(casa.passaros, start=1):
        melhor, nota_melhor = None, None
        for jogada in grade(tipo, rapido):
            mundo = reconstruir(casa, jogadas + [jogada])
            nota = (-len(mundo.alvos), sum(p.pontos for p in mundo.pecas if p.morta))
            if nota_melhor is None or nota > nota_melhor:
                melhor, nota_melhor = jogada, nota
        jogadas.append(melhor)
        if nota_melhor[0] == 0:
            return numero, True, usados, len(casa.passaros), cfg.estrelas_estilingue(len(casa.passaros), usados)
    return numero, False, len(casa.passaros), len(casa.passaros), 0


ERRO_ANGULO, ERRO_FORCA, ERRO_MOMENTO = 2.5, 0.05, 0.15


def jogar_como_humano(args):
    """Escolhe a melhor jogada (sem erro), mas executa com o erro de mira de uma pessoa."""
    numero, tentativa, rapido = args
    casa = cfg.casa_estilingue(numero)
    sorteio = random.Random(numero * 1000 + tentativa)
    feitas = []
    for usados, tipo in enumerate(casa.passaros, start=1):
        melhor, nota_melhor = None, None
        for jogada in grade(tipo, rapido):
            mundo = reconstruir(casa, feitas + [jogada])
            nota = (-len(mundo.alvos), sum(p.pontos for p in mundo.pecas if p.morta))
            if nota_melhor is None or nota > nota_melhor:
                melhor, nota_melhor = jogada, nota
        angulo, forca, quando = melhor
        feitas.append((angulo + sorteio.gauss(0, ERRO_ANGULO),
                       min(1.0, max(0.3, forca + sorteio.gauss(0, ERRO_FORCA))),
                       None if quando is None else max(0.2, quando + sorteio.gauss(0, ERRO_MOMENTO))))
        if not reconstruir(casa, feitas).alvos:
            return numero, cfg.estrelas_estilingue(len(casa.passaros), usados)
    return numero, 0


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--casas', nargs='*', type=int, default=list(range(1, len(cfg.CASAS_ESTILINGUE) + 1)))
    parser.add_argument('--rapido', action='store_true')
    parser.add_argument('--humano', type=int, default=0, metavar='N', help='N tentativas com erro de mira')
    args = parser.parse_args()
    if args.humano:
        tarefas = [(c, t, args.rapido) for c in args.casas for t in range(args.humano)]
        with ProcessPoolExecutor(mp_context=multiprocessing.get_context('spawn')) as executor:
            resultados = list(executor.map(jogar_como_humano, tarefas, timeout=3600))
        print('casa  vitórias  estrelas médias (nas vitórias)   [robô com erro de mira humano]')
        for numero in args.casas:
            estrelas = [e for n, e in resultados if n == numero]
            vitorias = [e for e in estrelas if e]
            media = sum(vitorias) / len(vitorias) if vitorias else 0
            chefe = '*' if cfg.casa_estilingue(numero).chefe else ' '
            print(f'{numero:4d}{chefe}  {len(vitorias) * 100 // len(estrelas):4d}%    {media:.1f}')
        return
    tarefas = [(c, args.rapido) for c in args.casas]
    with ProcessPoolExecutor(mp_context=multiprocessing.get_context('spawn')) as executor:
        resultados = list(executor.map(resolver, tarefas, timeout=1800))
    print('casa  venceu  pássaros usados  estrelas (robô perfeito)')
    for numero, venceu, usados, total, estrelas in sorted(resultados):
        chefe = '*' if cfg.casa_estilingue(numero).chefe else ' '
        print(f'{numero:4d}{chefe}  {"sim" if venceu else "NÃO":6s}  {usados}/{total:<14d}  {estrelas}')
    if not all(r[1] for r in resultados):
        sys.exit('há casas impossíveis: reveja a tabela CASAS_ESTILINGUE')


if __name__ == '__main__':
    main()
