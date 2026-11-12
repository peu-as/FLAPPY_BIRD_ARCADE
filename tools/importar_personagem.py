"""Importa a folha do personagem lendário (Wilson Luciano) para assets/personagens/.

    python tools/importar_personagem.py                 importa e mostra o relatório
    python tools/importar_personagem.py --previa X.png  também gera uma prévia para conferir

Entrada: artes/wilson_luciano.png (folha de 1536 x 1024 com fundo ciano liso:
um corpo inteiro grande, oito poses com o nome numa caixa embaixo, o retrato
numa moldura azul e a paleta). Fica em artes/, fora de assets: não vai no .exe.

Saída: assets/personagens/wilson/<pose>.png, pixel art nítida com fundo
transparente. Todas as poses usam a MESMA escala (tamanhos coerentes entre si);
o retrato tem escala própria (é o rosto, usado nos cartões da loja e no Estilingue).

Para trocar a arte: substitua a folha e, se as poses mudarem de lugar, ajuste
CAIXAS (x0, y0, x1, y1 em pixels da folha). Requer Pillow e numpy (requirements-dev.txt).
"""
import argparse
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from importar_artes import nitida  # noqa: E402  (mesma redução para a grade de pixels das outras skins)

RAIZ = Path(__file__).resolve().parents[1]
FOLHA = RAIZ / 'artes' / 'wilson_luciano.png'
SAIDA = RAIZ / 'assets' / 'personagens' / 'wilson'

# Onde cada pose está na folha (as caixas ficam ACIMA das etiquetas com o nome).
CAIXAS = {
    'idle': (395, 145, 615, 500),
    'correr': (645, 155, 910, 500),
    'pular': (945, 115, 1195, 470),
    'desviar': (1195, 235, 1505, 500),
    'atacar': (415, 610, 735, 925),
    'tomba': (728, 640, 950, 925),
    'vitoria': (980, 605, 1230, 925),
    'morrer': (1222, 770, 1510, 925),
    'retrato': (36, 684, 288, 948),       # por dentro da moldura azul
}
ALTURA_NATIVA = 34          # altura da pose 'idle' na grade de pixels do jogo (x2 na tela = 68 px)
LARGURA_RETRATO = 32        # largura do retrato na grade (x2 = 64 px: cabe no cartão da loja)
SOBRA_MINIMA = 0.02         # pedaços menores que 2% do desenho principal são sujeira (traços de impacto)


def eh_fundo(a):
    """Ciano do fundo, a sombra embaixo dos pés e o azul do retrato.

    O personagem é preto, pele e dourado: em nenhum deles o azul passa do
    vermelho por mais de 70 e o verde por mais de 45.
    """
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (b - r > 70) & (g - r > 45)


def componentes(mascara):
    """Rótulo de cada pedaço conectado (4 vizinhos) e o tamanho de cada um."""
    altura, largura = mascara.shape
    rotulo = np.zeros(mascara.shape, int)
    tamanhos = []
    for y in range(altura):
        for x in range(largura):
            if not mascara[y, x] or rotulo[y, x]:
                continue
            atual = len(tamanhos) + 1
            fila, total = deque([(y, x)]), 0
            rotulo[y, x] = atual
            while fila:
                cy, cx = fila.popleft()
                total += 1
                for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                    if 0 <= ny < altura and 0 <= nx < largura and mascara[ny, nx] and not rotulo[ny, nx]:
                        rotulo[ny, nx] = atual
                        fila.append((ny, nx))
            tamanhos.append(total)
    return rotulo, np.array(tamanhos)


def recortar(folha, caixa):
    """Pose com fundo transparente, sem sujeira, cortada rente ao desenho."""
    x0, y0, x1, y1 = caixa
    a = np.asarray(folha.crop(caixa).convert('RGB')).astype(int)
    desenho = ~eh_fundo(a)
    rotulo, tamanhos = componentes(desenho)
    grandes = 1 + np.where(tamanhos >= SOBRA_MINIMA * tamanhos.max())[0]
    manter = np.isin(rotulo, grandes)
    rgba = np.dstack([a, manter * 255]).astype(np.uint8)
    rgba[~manter, :3] = 0
    peca = Image.fromarray(rgba, 'RGBA')
    return peca.crop(peca.getbbox())


def importar(previa=None):
    if not FOLHA.exists():
        sys.exit(f'Folha não encontrada: {FOLHA}')
    folha = Image.open(FOLHA)
    pecas = {nome: recortar(folha, caixa) for nome, caixa in CAIXAS.items()}
    escala = ALTURA_NATIVA / pecas['idle'].height
    SAIDA.mkdir(parents=True, exist_ok=True)
    finais = {}
    for nome, peca in pecas.items():
        fator = LARGURA_RETRATO / peca.width if nome == 'retrato' else escala
        nativa = nitida(peca, fator)
        finais[nome] = nativa.resize((nativa.width * 2, nativa.height * 2), Image.NEAREST)
        finais[nome].save(SAIDA / f'{nome}.png', optimize=True)
    print(f'{"pose":<10} {"tamanho":>9}  cores')
    for nome, img in finais.items():
        print(f'{nome:<10} {img.width:>4}x{img.height:<4}  {len(img.getcolors(4096) or [])}')
    print(f'{len(finais)} imagens em {SAIDA.relative_to(RAIZ)}')
    if previa:
        largura = sum(i.width + 12 for i in finais.values()) + 12
        altura = max(i.height for i in finais.values()) + 24
        tela = Image.new('RGBA', (largura, altura), (110, 200, 220, 255))
        x = 12
        for img in finais.values():
            tela.alpha_composite(img, (x, altura - 12 - img.height))
            x += img.width + 12
        tela.save(previa)
        print(f'prévia: {previa}')
    return finais


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--previa', help='salva uma prévia com todas as poses')
    importar(parser.parse_args().previa)


if __name__ == '__main__':
    main()
