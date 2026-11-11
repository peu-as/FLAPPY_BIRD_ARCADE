"""Ponto de entrada do jogo.

    python src/main.py             tela de escolha de modo (mapas, Modo Livre, clássico)
    python src/main.py --livre     direto no Modo Livre
    python src/main.py --classico  direto no jogo clássico original
    python src/main.py --casa estilingue 5   direto numa casa de um mapa (para testar)

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
    modo.add_argument('--casa', nargs=2, metavar=('MAPA', 'N'),
                      help='abre direto a casa N de um mapa (ex.: --casa estilingue 5)')
    args = parser.parse_args()
    app = App()
    if args.casa:
        from flappy_arcade.config.levels import CASAS, MAPAS
        from flappy_arcade.scenes.level_scene import LevelScene
        from flappy_arcade.scenes.main_menu import MainMenuScene
        from flappy_arcade.scenes.map_scene import MapScene
        mapa, casa = args.casa[0], int(args.casa[1])
        if mapa not in MAPAS or not 1 <= casa <= CASAS:
            parser.error(f'mapa: {", ".join(MAPAS)}; casa: 1 a {CASAS}')
        app.ctx.scenes.push(MainMenuScene(app.ctx))      # ao sair: mapa e depois o menu
        app.ctx.scenes.push(MapScene(app.ctx, mapa))
        app.run(LevelScene(app.ctx, mapa, casa))
    elif args.livre or args.classico:
        app.run(GameScene(app.ctx, 'livre' if args.livre else 'classico'))
    else:
        app.run()


if __name__ == '__main__':
    main()
