"""Verificação final antes do commit: abre o jogo inteiro sem janela e roda os testes.

    python tools/verificar_jogo.py            verificação completa (~2 a 3 min)
    python tools/verificar_jogo.py --rapido   só as telas, sem a suíte de testes

O que confere:
  1. ambiente (Python e pygame);
  2. arquivos: imagens, músicas, todas as skins e todos os cenários do catálogo;
  3. telas: menu, os quatro mapas, casas de cada mapa (comum e chefão), Modo Livre
     atravessando a Galaga e o Donkey com os bônus, clássico, loja (abas, filtros e
     vistas), Equipamentos (fixo e aleatório), configurações e pausa;
  4. a suíte de testes (python -m pytest), inclusive o golden master do clássico.

Usa uma pasta de dados temporária: o seu save de verdade não é tocado.
Termina com PRONTO PARA O COMMIT ou com a lista do que corrigir.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['FLAPPY_DATA_DIR'] = tempfile.mkdtemp(prefix='flappy-verificacao-')
sys.path.insert(0, str(RAIZ / 'src'))

import pygame  # noqa: E402

resultados = []          # (grupo, item, ok, detalhe)


def marcar(grupo, item, ok, detalhe=''):
    resultados.append((grupo, item, ok, detalhe))
    print(f"  {'OK ' if ok else 'ERRO'}  {item}{'  — ' + detalhe if detalhe else ''}")


def checar(grupo, item):
    """Decorador: roda a verificação e registra OK ou o erro (sem parar as outras)."""
    def decorar(funcao):
        inicio = time.perf_counter()
        try:
            detalhe = funcao() or ''
            marcar(grupo, item, True, f'{detalhe} ({time.perf_counter() - inicio:.1f} s)'.strip())
        except Exception as erro:            # noqa: BLE001 — queremos relatar qualquer falha
            marcar(grupo, item, False, f'{type(erro).__name__}: {erro}')
            traceback.print_exc(limit=3)
        return funcao
    return decorar


# ---------------------------------------------------------------- 1. ambiente
def ambiente():
    print('\n1. Ambiente')

    @checar('ambiente', f'Python {sys.version.split()[0]}')
    def _():
        assert sys.version_info >= (3, 10), 'use Python 3.10 ou mais novo'

    @checar('ambiente', f'pygame {pygame.version.ver}')
    def _():
        assert pygame.version.vernum >= (2, 5), 'use pygame 2.5 ou mais novo (requirements.txt)'


# ---------------------------------------------------------------- 2. arquivos
def arquivos():
    print('\n2. Arquivos')
    from flappy_arcade.config.scenarios import CENARIOS, ORIGINAL
    from flappy_arcade.config.skins import SKINS
    from flappy_arcade.core.paths import ARTES_CENARIOS, ARTES_SKINS, IMAGENS, MUSICA_JOGO, MUSICA_MENU

    @checar('arquivos', 'imagens e músicas do jogo')
    def _():
        faltando = [p.name for p in (IMAGENS / 'bg.png', IMAGENS / 'base.png', IMAGENS / 'pipe.png',
                                     MUSICA_MENU, MUSICA_JOGO) if not p.exists()]
        assert not faltando, f'faltam: {", ".join(faltando)}'

    @checar('arquivos', 'skins do catálogo')
    def _():
        artes = [s for s in SKINS if s.tipo == 'arte']
        faltando = [s.id for s in artes if not (ARTES_SKINS / f'{s.sprite}.png').exists()]
        assert not faltando, f'faltam {len(faltando)}: {", ".join(faltando[:5])}'
        return f'{len(SKINS)} skins ({len(artes)} artes)'

    @checar('arquivos', 'cenários do catálogo')
    def _():
        faltando = [c.id for c in CENARIOS
                    if not ((IMAGENS if c.tipo == ORIGINAL else ARTES_CENARIOS) / c.arquivo).exists()]
        assert not faltando, f'faltam: {", ".join(faltando)}'
        return f'{len(CENARIOS)} cenários'


# ---------------------------------------------------------------- 3. telas
def telas():
    print('\n3. Telas (sem janela)')
    import flappy_arcade.core.app as modulo_app
    from flappy_arcade.config.levels import ORDEM_MAPAS
    from flappy_arcade.config.scenarios import CENARIOS
    from flappy_arcade.scenes.equipment_scene import EquipmentScene
    from flappy_arcade.scenes.game_scene import GameScene
    from flappy_arcade.scenes.level_scene import LevelScene
    from flappy_arcade.scenes.main_menu import MainMenuScene
    from flappy_arcade.scenes.map_scene import MapScene
    from flappy_arcade.scenes.pause_scene import PauseScene
    from flappy_arcade.scenes.settings_scene import SettingsScene
    from flappy_arcade.scenes.shop_scene import ShopScene

    ctx = modulo_app.App().ctx
    tela = pygame.Surface((575, 860))
    espaco = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=' ', scancode=44)
    pior = {'tempo': 0.0, 'tela': ''}

    def rodar(cena, quadros, dt, acao=None, nome=''):
        ctx.scenes.push(cena)
        try:
            for i in range(quadros):
                if acao:
                    acao(cena, i)
                inicio = time.perf_counter()
                cena.update(dt)
                cena.draw(tela)
                gasto = time.perf_counter() - inicio
                if gasto > pior['tempo'] and i > 5:
                    pior.update(tempo=gasto, tela=nome)
        finally:
            while ctx.scenes.top is not cena and not ctx.scenes.empty:
                ctx.scenes.pop()
            if not ctx.scenes.empty:
                ctx.scenes.pop()

    ctx.wallet.depositar(100_000)                     # para abrir tudo na loja (save temporário)
    for c in CENARIOS[1:9]:
        ctx.scenarios.comprar(c.id)

    @checar('telas', 'menu principal')
    def _():
        rodar(MainMenuScene(ctx), 90, 1 / 60, nome='menu')

    # o Combina 3 entra no menu na Fase 17; até lá é conferido aqui pelo nome
    for mapa in dict.fromkeys((*ORDEM_MAPAS, 'combina3', 'arcade')):
        @checar('telas', f'mapa {mapa}')
        def _(mapa=mapa):
            rodar(MapScene(ctx, mapa), 40, 1 / 60, nome=f'mapa {mapa}')

        for casa in (1, 5):
            @checar('telas', f'casa {casa} de {mapa}')
            def _(mapa=mapa, casa=casa):
                def jogar(cena, i):
                    if i == 0:
                        cena.handle_event(espaco)
                    elif i % 9 == 0:
                        cena.session.acao_principal()
                rodar(LevelScene(ctx, mapa, casa), 240, 1 / 30, jogar, f'casa {casa} {mapa}')

    for fase in ('GALAGA', 'DONKEY'):
        @checar('telas', f'Modo Livre atravessando {fase.title()} com bônus e cenários')
        def _(fase=fase):
            ctx.scenarios.definir_modo('aleatorio')

            def jogar(cena, i):
                s = cena.session
                if s.estado == 'MENU' or (s.estado in ('JOGO', 'DONKEY') and s.passaro.y > 420 and i % 2):
                    s.acao_principal()
                if i == 60:
                    s.iniciar_alerta(fase)
                if s.estado == 'GALAGA' and s.galaga and i % 90 == 0:
                    for bonus in ('GEMEO', 'TURBO', 'BOMBA'):
                        s.galaga._aplicar_bonus(bonus)
                if s.estado == 'DONKEY' and s.donkey and i % 90 == 0:
                    s.donkey.efeitos.ativar('MOLA', 7.0)
                    s.donkey.cargas = 3
                    s.donkey.lancar_bumerangue(s.passaro)
            cena = GameScene(ctx, 'livre')
            rodar(cena, 600, 1 / 30, jogar, f'Modo Livre {fase}')
            assert getattr(cena.session, fase.lower()) is not None, f'a fase {fase} não começou'

    @checar('telas', 'clássico (original)')
    def _():
        rodar(GameScene(ctx, 'classico'), 120, 1 / 30, nome='clássico')

    @checar('telas', 'loja: abas, filtros e vistas')
    def _():
        def navegar(cena, i):
            if i == 60:
                cena.trocar_aba('cenarios')
            if i % 20 == 0:
                cena.passar_filtro(1)
                cena.ver_em(('flappy', 'galaga', 'donkey')[i // 20 % 3])
            if i % 5 == 0:
                cena._selecionar((cena.indice + 1) % len(cena.itens))
        rodar(ShopScene(ctx), 160, 1 / 60, navegar, 'loja')

    @checar('telas', 'Equipamentos: fixo e aleatório')
    def _():
        def alternar(cena, i):
            if i == 20:
                cena.definir_modo('fixo')
                cena.escolher(1)
            if i == 50:
                cena.definir_modo('aleatorio')
                cena.escolher(2)
        rodar(EquipmentScene(ctx), 90, 1 / 60, alternar, 'equipamentos')

    @checar('telas', 'configurações e pausa')
    def _():
        rodar(SettingsScene(ctx), 30, 1 / 60, nome='configurações')
        rodar(PauseScene(ctx, 'MENU PRINCIPAL', ao_sair=lambda: None), 30, 1 / 60, nome='pausa')

    marcar('telas', 'quadro mais lento', pior['tempo'] < 0.1,
           f'{pior["tempo"] * 1000:.0f} ms em "{pior["tela"]}"')


# ---------------------------------------------------------------- 4. testes
def testes():
    print('\n4. Testes (python -m pytest) — pode levar uns 2 minutos')
    inicio = time.perf_counter()
    processo = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'no:warnings', '-p', 'no:cacheprovider'],
                              cwd=RAIZ, capture_output=True, text=True)
    ultima = (processo.stdout.strip().splitlines() or ['(sem saída)'])[-1]
    marcar('testes', 'suíte completa', processo.returncode == 0,
           f'{ultima} ({time.perf_counter() - inicio:.0f} s)')
    if processo.returncode != 0:
        print('\n'.join(processo.stdout.splitlines()[-25:]))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--rapido', action='store_true', help='não roda a suíte de testes')
    args = parser.parse_args()
    print('VERIFICAÇÃO DO JOGO')
    pygame.init()
    pygame.display.set_mode((575, 860))
    ambiente()
    arquivos()
    telas()
    pygame.quit()
    if not args.rapido:
        testes()
    erros = [r for r in resultados if not r[2]]
    print('\n' + '=' * 60)
    if erros:
        print(f'NÃO FAÇA O COMMIT AINDA: {len(erros)} problema(s)')
        for grupo, item, _, detalhe in erros:
            print(f'  - [{grupo}] {item}: {detalhe}')
        sys.exit(1)
    print(f'PRONTO PARA O COMMIT: {len(resultados)} verificações OK'
          + (' (sem a suíte de testes: rode sem --rapido antes do commit)' if args.rapido else ''))


if __name__ == '__main__':
    main()
