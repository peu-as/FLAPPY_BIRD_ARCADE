"""Importa as folhas de arte (skins, times e cenários) para assets/.

    python tools/importar_artes.py                 importa e mostra o relatório
    python tools/importar_artes.py --previa X.png  também gera uma prévia para conferir

Entrada (artes/, fora de assets para não ir no .exe):
  skins.png     personagens em grade, fundo de cor lisa, nome numa caixa embaixo
  times.png     idem, com o nome colado embaixo de cada personagem
  cenarios.png  paisagens em grade, separadas por divisórias brancas

Saída:
  assets/skins/<id>.png      sprite pronto (pixel art nítida, fundo transparente)
  assets/cenarios/<id>.png   faixa de horizonte com 575 px de largura

Para acrescentar artes: ponha a folha em artes/, acrescente os nomes
na tabela correspondente abaixo (na ordem esquerda -> direita, cima -> baixo)
e rode o script. Requer Pillow e numpy (requirements-dev.txt).
"""
import argparse
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
FONTES = RAIZ / 'artes'          # folhas originais (fora de assets: não vão no .exe)
SAIDA_SKINS = RAIZ / 'assets' / 'skins'
SAIDA_CENARIOS = RAIZ / 'assets' / 'cenarios'

# Nomes na ordem da folha. None = peça que não entra no jogo.
NOMES_SKINS = [
    None,  # Padrão: igual ao pássaro clássico
    None, None, None, None,  # Super Herói, Cavaleiro, Herói Vermelho, Link: personagens de terceiros
    'Mago', 'Ninja', 'Cowboy',
    'Astronauta', 'Robô', 'Gato', 'Cachorro', 'Sapo', 'Panda', 'Unicórnio', 'Dinossauro',
    'Papai Noel', 'Elfo', 'Rena', 'Boneco de Neve', 'Abóbora', 'Bruxa', 'Fantasminha', 'Vampiro',
    'Abelha', 'Joaninha', 'Borboleta', 'Fada', 'Alien', 'Rockstar', 'Gamer', 'Esportista',
    'Rei', 'Rainha', 'Pirata', 'Chef', 'Verão', 'Aniversário', 'Inverno', 'Futurista',
]
NOMES_TIMES = [
    'Santos', 'Flamengo', 'Palmeiras', 'SPFC', 'Botafogo', 'Fluminense', 'Grêmio', 'Internacional',
    'Vasco', 'Athletico-PR', 'Corinthians', 'Cruzeiro', 'Bahia', 'Fortaleza', 'Ceará', 'Sport',
    'Goiás', 'Atlético-GO', 'Cuiabá', 'Botafogo-SP', 'Novorizontino', 'Paysandu', 'Remo', 'Chapecoense',
    'ABC', 'Criciúma', 'Operário', 'Avaí', 'CSA', 'Ituano', 'Sampaio', 'Mirassol',
]
NOMES_CENARIOS = [
    'Parque', 'Pôr do Sol', 'Cidade Noturna', 'Inverno',
    'Sakura', 'Halloween', 'Praia', 'Deserto',
    'Ilhas Flutuantes', 'Estação Espacial', 'Floresta Mágica', 'Vulcão',
    'Cyberpunk', 'Oceano', 'Castelo', 'Planeta',
    'Outono', 'Templo', 'Doces', 'Galáxia',
]

# o brilho médio erra em alguns: pôr do sol é tarde mesmo sendo claro, etc.
AJUSTE_PERIODO = {'Pôr do Sol': 'tarde', 'Inverno': 'noite', 'Oceano': 'dia'}
LARGURA_JOGO = 575
LARGURA_NATIVA = 36          # largura do corpo na grade de pixels do jogo (o pássaro original tem 34)
CORES = 24                   # paleta por skin (pixel art limpa)
TOLERANCIA_FUNDO = 70        # fundo ligado às bordas
TOLERANCIA_BOLSAO = 48       # fundo cercado pelo desenho (mais estrita: preserva azuis do desenho)


def ident(nome, prefixo=''):
    """'Boneco de Neve' -> 'boneco_de_neve' (sem acentos)."""
    sem_acento = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode()
    limpo = ''.join(c if c.isalnum() else '_' for c in sem_acento.lower())
    return prefixo + '_'.join(p for p in limpo.split('_') if p)


def faixas(perfil, minimo=1):
    """Trechos contínuos onde perfil é verdadeiro: [(início, fim), ...]."""
    saida, inicio = [], None
    for i, v in enumerate(list(perfil) + [False]):
        if v and inicio is None:
            inicio = i
        if not v and inicio is not None:
            if i - inicio >= minimo:
                saida.append((inicio, i))
            inicio = None
    return saida


# ------------------------------------------------------------------ skins
def recortar_personagens(caminho):
    """Folha de personagens -> lista de recortes (sem os nomes) e a cor do fundo."""
    imagem = Image.open(caminho).convert('RGB')
    a = np.asarray(imagem).astype(int)
    fundo = np.median(np.concatenate([a[-24:].reshape(-1, 3), a[:, :8].reshape(-1, 3)]), axis=0)
    ocupado = np.abs(a - fundo).sum(axis=2) > 60
    rotulo = (a[:, :, 2] > 110) & (a[:, :, 0] < 60) & (a[:, :, 1] < 110)     # caixas azul-escuras
    pecas = []
    for y0, y1 in faixas(ocupado.mean(axis=1) > 0.01, 8):
        if rotulo[y0:y1].mean() > 0.25 or y1 - y0 < 100:                     # faixa de nomes ou título
            continue
        linhas_rotulo = np.where(rotulo[y0:y1].mean(axis=1) > 0.25)[0]
        fim = y0 + linhas_rotulo[0] - 2 if len(linhas_rotulo) else y1
        for x0, x1 in faixas(ocupado[y0:fim].mean(axis=0) > 0.02, 10):
            pecas.append(imagem.crop((max(0, x0 - 4), max(0, y0 - 4), x1 + 4, fim)))
    return pecas, tuple(int(v) for v in fundo)


def tirar_fundo(peca, fundo):
    """Fundo das bordas + bolsões cercados pelo desenho -> transparentes."""
    rgba = peca.convert('RGBA')
    marca = (255, 0, 255, 0)
    for canto in ((0, 0), (rgba.width - 1, 0), (0, rgba.height - 1), (rgba.width - 1, rgba.height - 1)):
        ImageDraw.floodfill(rgba, canto, marca, thresh=TOLERANCIA_FUNDO)
    a = np.asarray(rgba).copy()
    externo = (a[:, :, 0] == 255) & (a[:, :, 1] == 0) & (a[:, :, 2] == 255)
    bolsao = np.abs(a[:, :, :3].astype(int) - np.array(fundo)).sum(axis=2) < TOLERANCIA_BOLSAO
    a[externo | bolsao, 3] = 0
    a[a[:, :, 3] == 0, :3] = 0
    limpa = Image.fromarray(a)
    return limpa.crop(limpa.getbbox())


def nitida(skin, escala):
    """Reduz para a grade de pixels do jogo (alfa pré-multiplicado), paleta curta, amplia 2x."""
    largura, altura = max(1, round(skin.width * escala)), max(1, round(skin.height * escala))
    pequeno = skin.convert('RGBa').resize((largura, altura), Image.BOX).convert('RGBA')
    alfa = pequeno.getchannel('A').point(lambda v: 255 if v > 140 else 0)
    cores = pequeno.convert('RGB').quantize(CORES, method=Image.Quantize.MEDIANCUT).convert('RGB')
    cores.putalpha(alfa)
    cores = cores.crop(cores.getbbox())
    return cores


def alinhar_pelo_corpo(nativa, altura_corpo):
    """Chapéus e orelhas sobem a figura; completa embaixo para o CORPO ficar no centro.

    O jogo centraliza a skin no retângulo de colisão do pássaro: sem isso, uma
    skin de chapéu pareceria "afundada" em relação à hitbox. altura_corpo é a
    altura típica da folha (a maioria das skins não tem chapéu).
    """
    sobra = max(0, nativa.height - altura_corpo)
    if not sobra:
        return nativa
    tela = Image.new('RGBA', (nativa.width, nativa.height + sobra), (0, 0, 0, 0))
    tela.paste(nativa, (0, 0))
    return tela


def importar_personagens(arquivo, nomes, prefixo=''):
    pecas, fundo = recortar_personagens(FONTES / arquivo)
    if len(pecas) != len(nomes):
        sys.exit(f'{arquivo}: {len(pecas)} peças encontradas, mas a tabela tem {len(nomes)} nomes')
    limpas = [tirar_fundo(p, fundo) for p in pecas]
    larguras = sorted(p.width for p in limpas)
    escala = LARGURA_NATIVA / larguras[len(larguras) // 2]     # uma escala por folha: tamanhos coerentes
    nativas = [nitida(limpa, escala) for limpa in limpas]
    alturas = sorted(n.height for n in nativas)
    altura_corpo = alturas[len(alturas) // 2]
    relatorio = []
    for nome, nativa in zip(nomes, nativas):
        if nome is None:
            continue
        nativa = alinhar_pelo_corpo(nativa, altura_corpo)
        final = nativa.resize((nativa.width * 2, nativa.height * 2), Image.NEAREST)
        destino = SAIDA_SKINS / f'{ident(nome, prefixo)}.png'
        final.save(destino, optimize=True)
        relatorio.append(validar_skin(nome, destino, final))
    return relatorio


def validar_skin(nome, destino, imagem):
    alfa = np.asarray(imagem.getchannel('A')) > 0
    avisos = []
    if not 50 <= imagem.width <= 96:
        avisos.append(f'largura {imagem.width}px fora de 50-96')
    if imagem.height > 110:
        avisos.append(f'altura {imagem.height}px alta')
    if alfa.mean() > 0.9:
        avisos.append('quase sem transparência: fundo não saiu?')
    cores = len(imagem.getcolors(4096) or [])
    return (nome, destino.name, f'{imagem.width}x{imagem.height}', cores, f'{alfa.mean():.0%}',
            '; '.join(avisos) or 'ok')


# ------------------------------------------------------------------ cenários
def recortar_cenarios(caminho):
    imagem = Image.open(caminho).convert('RGB')
    a = np.asarray(imagem).astype(int)
    branco = a.min(axis=2) > 225
    return [imagem.crop((x0 + 3, y0 + 3, x1 - 3, y1 - 3))          # 3 px: restos da divisória
            for y0, y1 in faixas(branco.mean(axis=1) < 0.5, 20)
            for x0, x1 in faixas(branco.mean(axis=0) < 0.5, 20)]


def importar_cenarios():
    pecas = recortar_cenarios(FONTES / 'cenarios.png')
    if len(pecas) != len(NOMES_CENARIOS):
        sys.exit(f'cenarios.png: {len(pecas)} peças, mas a tabela tem {len(NOMES_CENARIOS)} nomes')
    relatorio = []
    for nome, peca in zip(NOMES_CENARIOS, pecas):
        faixa = peca.resize((peca.width * 2, peca.height * 2), Image.NEAREST)     # 2x: sem borrar
        corte = (faixa.width - LARGURA_JOGO) // 2
        faixa = faixa.crop((corte, 0, corte + LARGURA_JOGO, faixa.height))
        destino = SAIDA_CENARIOS / f'{ident(nome)}.png'
        faixa.save(destino, optimize=True)
        brilho = np.asarray(faixa.convert('L')).mean() / 255
        periodo = 'noite' if brilho < 0.36 else 'tarde' if brilho < 0.5 else 'dia'
        if nome in AJUSTE_PERIODO:
            periodo = f'{AJUSTE_PERIODO[nome]} (ajustado)'
        avisos = [] if faixa.height >= 300 else [f'faixa baixa ({faixa.height}px)']
        relatorio.append((nome, destino.name, f'{faixa.width}x{faixa.height}',
                          f'{destino.stat().st_size // 1024} KB', f'{brilho:.2f} -> {periodo}',
                          '; '.join(avisos) or 'ok'))
    return relatorio


def imprimir(titulo, cabecalho, linhas):
    print(f'\n{titulo}')
    larguras = [max(len(str(x)) for x in col) for col in zip(cabecalho, *linhas)]
    for linha in [cabecalho] + linhas:
        print('  ' + '  '.join(str(x).ljust(l) for x, l in zip(linha, larguras)))


def main():
    parser = argparse.ArgumentParser(description='Importa as folhas de arte para assets/')
    parser.add_argument('--previa', help='gera uma prévia (PNG) com tudo que foi importado')
    args = parser.parse_args()
    SAIDA_SKINS.mkdir(parents=True, exist_ok=True)
    SAIDA_CENARIOS.mkdir(parents=True, exist_ok=True)
    cab_skin = ('nome', 'arquivo', 'tamanho', 'cores', 'opaco', 'validação')
    skins = importar_personagens('skins.png', NOMES_SKINS)
    times = importar_personagens('times.png', NOMES_TIMES, 'time_')
    cenarios = importar_cenarios()
    imprimir(f'SKINS ({len(skins)})', cab_skin, skins)
    imprimir(f'TIMES ({len(times)})', cab_skin, times)
    imprimir(f'CENÁRIOS ({len(cenarios)})', ('nome', 'arquivo', 'tamanho', 'peso', 'brilho -> período', 'validação'),
             cenarios)
    problemas = [l for l in skins + times + cenarios if l[-1] != 'ok']
    print(f'\n{len(skins) + len(times)} skins e {len(cenarios)} cenários importados; '
          f'{len(problemas)} com aviso.')
    if args.previa:
        from previa_artes import gerar_previa
        gerar_previa(Path(args.previa), skins, times, cenarios)
        print('prévia gravada em', args.previa)


if __name__ == '__main__':
    main()
