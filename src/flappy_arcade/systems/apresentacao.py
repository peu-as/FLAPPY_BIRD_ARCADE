"""Modo Apresentação: tudo liberado para mostrar o jogo, sem mexer no jogo de verdade.

Atalho secreto (no menu principal): Ctrl + Shift + A. O mesmo atalho desliga.

Ligado, o jogo passa a usar um perfil temporário, que fica só na memória:
  * todas as casas de todos os mapas abertas (sem estrelas, para ainda dar
    para mostrar a conquista de estrelas e moedas);
  * todas as skins e todos os cenários comprados, e 99.999 moedas;
  * os atalhos de teste do Clássico e do Modo Livre (G, K, F, B, C, T, V e
    os números; veja config/debug.py).

O save do jogador é gravado como estava e guardado de lado. Nada do perfil de
apresentação vai para o disco: nem o save, nem o ranking do clássico. Ao
desligar (ou ao fechar o jogo), tudo volta exatamente como era. As
configurações (música, efeitos) são as mesmas nos dois perfis.
"""
import copy

import pygame

from ..config.scenarios import POR_ID as CENARIOS_POR_ID
from ..config.skins import POR_ID as SKINS_POR_ID
from .save_manager import PADRAO

MOEDAS = 99_999
TECLA = pygame.K_a

_estado = {'save': None, 'guardado': None}     # save em uso e (dados reais, gravável) guardados de lado


def ligado():
    return _estado['save'] is not None


def eh_atalho(evento):
    """Ctrl + Shift + A (qualquer um dos Ctrl e Shift)."""
    if evento.type != pygame.KEYDOWN or evento.key != TECLA:
        return False
    mod = getattr(evento, 'mod', 0)
    return bool(mod & pygame.KMOD_CTRL) and bool(mod & pygame.KMOD_SHIFT)


def perfil(real):
    """Os dados do perfil de apresentação, a partir do save real (que não é alterado)."""
    dados = copy.deepcopy(PADRAO)
    dados['settings'] = real['settings']               # o mesmo objeto: música e efeitos valem nos dois
    dados['wallet']['coins'] = MOEDAS
    dados['skins'] = {'owned': list(SKINS_POR_ID), 'equipped': real['skins'].get('equipped')}
    cenarios = copy.deepcopy(real['scenarios'])        # mantém o modo, o fixo e a playlist do jogador
    cenarios['owned'] = list(CENARIOS_POR_ID)
    dados['scenarios'] = cenarios
    dados['apresentacao'] = True
    return dados


def ligar(ctx):
    if ligado():
        return
    save = ctx.save
    save.save()                                        # o jogo real fica gravado como estava
    _estado['guardado'] = (save.data, save.gravavel)
    save.data = perfil(save.data)
    save.gravavel = False                              # o perfil de apresentação nunca vai para o disco
    _estado['save'] = save
    ctx.bus.emit('coins_changed', saldo=ctx.wallet.saldo)


def desligar(ctx=None):
    if not ligado():
        return
    save = _estado['save']
    save.data, save.gravavel = _estado['guardado']
    _estado['save'] = _estado['guardado'] = None
    save.save()                                        # guarda as configurações mudadas durante a apresentação
    if ctx is not None:
        ctx.bus.emit('coins_changed', saldo=ctx.wallet.saldo)


def alternar(ctx):
    """Liga ou desliga. Devolve True se ficou ligado."""
    (desligar if ligado() else ligar)(ctx)
    return ligado()
