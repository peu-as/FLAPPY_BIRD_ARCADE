"""Ponto de entrada do jogo.

    python src/main.py             tela de escolha de modo (mapas, Modo Livre, clássico)
    python src/main.py --livre     direto no Modo Livre
    python src/main.py --classico  direto no jogo clássico original

Para os atalhos de teste do desenvolvedor (PowerShell):
    $env:FLAPPY_DEBUG=1; python src/main.py
"""
import argparse

from flappy_arcade.core.app import App
from flappy_arcade.scenes.game_scene import GameScene


def main():
    parser = argparse.ArgumentParser(description='Flappy Arcade')
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--livre', action='store_true', help='abre direto no Modo Livre')
    modo.add_argument('--classico', action='store_true', help='abre direto no jogo clássico')
    args = parser.parse_args()
    app = App()
    if args.livre or args.classico:
        app.run(GameScene(app.ctx, 'livre' if args.livre else 'classico'))
    else:
        app.run()


if __name__ == '__main__':
    main()
