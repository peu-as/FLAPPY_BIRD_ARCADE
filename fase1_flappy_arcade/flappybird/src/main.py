"""Ponto de entrada do jogo.

    python src/main.py

Para os atalhos de teste do desenvolvedor (PowerShell):
    $env:FLAPPY_DEBUG=1; python src/main.py
"""
from flappy_arcade.core.app import App

if __name__ == '__main__':
    App().run()
