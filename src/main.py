"""Ponto de entrada do jogo.

    python src/main.py            jogo clássico (com vidas e ranking)
    python src/main.py --livre    Modo Livre (treino, sem vidas)

Para os atalhos de teste do desenvolvedor (PowerShell):
    $env:FLAPPY_DEBUG=1; python src/main.py
"""
import argparse

from flappy_arcade.core.app import App
from flappy_arcade.scenes.game_scene import GameScene


def main():
    parser = argparse.ArgumentParser(description='Flappy Arcade')
    parser.add_argument('--livre', action='store_true',
                        help='Modo Livre: sem vidas, dificuldade sobe com o tempo')
    args = parser.parse_args()
    app = App()
    app.run(GameScene(app.ctx, 'livre' if args.livre else 'classico'))


if __name__ == '__main__':
    main()
