"""Gera o ícone do jogo a partir da capa (artes/capa.png).

    python tools/gerar_icone.py                 gera os arquivos e mostra o relatório
    python tools/gerar_icone.py --previa X.png  também salva uma prévia com todos os tamanhos

Saída (assets/icone/):
  flappy_arcade.ico   ícone do executável (PyInstaller --icon), com 7 tamanhos dentro
  flappy_arcade.png   o mesmo desenho em 256 x 256 (README, atalhos)
  icone_janela.png    ícone da janela e da barra de tarefas (pygame.display.set_icon)

A capa é vertical (1024 x 1536) e cheia de detalhes: reduzida inteira para
16 px, vira um borrão. Por isso o .ico tem DOIS desenhos:
  48 a 256 px  pássaro + coroa + logotipo FLAPPY ARCADE (recorte quadrado da capa)
  16 a 32 px   só o pássaro, de perto (é o que dá para reconhecer na barra de tarefas)
O Windows escolhe sozinho o tamanho certo para cada lugar (Explorer, atalho, barra).

Cada tamanho vai dentro do .ico como PNG (aceito pelo Windows desde o Vista);
o arquivo é escrito aqui mesmo, sem depender da versão do Pillow.
Requer Pillow (requirements-dev.txt).
"""
import argparse
import io
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[1]
CAPA = RAIZ / 'artes' / 'capa.png'
SAIDA = RAIZ / 'assets' / 'icone'

# Recortes quadrados em pixels da capa de 1024 x 1536 (x0, y0, lado).
RECORTE_LOGO = (112, 214, 800)        # pássaro, coroa e o logotipo
RECORTE_PASSARO = (392, 248, 290)    # só o pássaro
TAMANHOS_GRANDES = (256, 128, 64, 48)
TAMANHOS_PEQUENOS = (32, 24, 16)
TAMANHO_JANELA = 64
RAIO_CANTO = 0.18                    # cantos arredondados (fração do lado)


def recortar(capa, recorte):
    x0, y0, lado = recorte
    escala_x, escala_y = capa.width / 1024, capa.height / 1536      # aceita a capa em outra resolução
    caixa = (round(x0 * escala_x), round(y0 * escala_y),
             round((x0 + lado) * escala_x), round(y0 * escala_y + lado * escala_x))
    return capa.crop(caixa)


def arredondar(imagem):
    """Cantos transparentes (com 4x de resolução na máscara para a borda sair lisa)."""
    lado = imagem.width
    grande = lado * 4
    mascara = Image.new('L', (grande, grande), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, grande - 1, grande - 1), round(grande * RAIO_CANTO), fill=255)
    saida = imagem.convert('RGBA')
    saida.putalpha(mascara.resize((lado, lado), Image.LANCZOS))
    return saida


def tamanho(imagem, lado):
    return arredondar(imagem.resize((lado, lado), Image.LANCZOS))


def escrever_ico(caminho, imagens):
    """ICO = cabeçalho (6 bytes) + uma entrada de 16 bytes por imagem + os PNGs."""
    dados = []
    for img in imagens:
        buffer = io.BytesIO()
        img.save(buffer, 'PNG', optimize=True)
        dados.append(buffer.getvalue())
    cabecalho = struct.pack('<HHH', 0, 1, len(imagens))           # reservado, tipo 1 = ícone, quantidade
    deslocamento = 6 + 16 * len(imagens)
    entradas = b''
    for img, png in zip(imagens, dados):
        lado = img.width if img.width < 256 else 0                 # 0 significa 256
        entradas += struct.pack('<BBBBHHII', lado, lado, 0, 0, 1, 32, len(png), deslocamento)
        deslocamento += len(png)
    caminho.write_bytes(cabecalho + entradas + b''.join(dados))


def ler_tamanhos_ico(caminho):
    """Tamanhos gravados num .ico (usado pelos testes e pelo relatório)."""
    bruto = caminho.read_bytes()
    reservado, tipo, quantidade = struct.unpack_from('<HHH', bruto, 0)
    if reservado != 0 or tipo != 1:
        raise ValueError('não é um arquivo .ico')
    lados = []
    for i in range(quantidade):
        lado = struct.unpack_from('<B', bruto, 6 + 16 * i)[0]
        lados.append(lado or 256)
    return lados


def gerar(previa=None):
    if not CAPA.exists():
        sys.exit(f'Capa não encontrada: {CAPA}')
    capa = Image.open(CAPA).convert('RGB')
    logo = recortar(capa, RECORTE_LOGO)
    passaro = recortar(capa, RECORTE_PASSARO)
    imagens = [tamanho(logo, lado) for lado in TAMANHOS_GRANDES]
    imagens += [tamanho(passaro, lado) for lado in TAMANHOS_PEQUENOS]
    SAIDA.mkdir(parents=True, exist_ok=True)
    escrever_ico(SAIDA / 'flappy_arcade.ico', imagens)
    imagens[0].save(SAIDA / 'flappy_arcade.png', optimize=True)
    tamanho(passaro, TAMANHO_JANELA).save(SAIDA / 'icone_janela.png', optimize=True)
    print('flappy_arcade.ico  tamanhos:', ', '.join(f'{lado}' for lado in ler_tamanhos_ico(SAIDA / 'flappy_arcade.ico')))
    print('flappy_arcade.png  256x256')
    print(f'icone_janela.png   {TAMANHO_JANELA}x{TAMANHO_JANELA}')
    if previa:
        largura = sum(i.width + 16 for i in imagens) + 16
        tela = Image.new('RGBA', (largura, 288), (40, 44, 52, 255))
        x = 16
        for img in imagens:
            tela.alpha_composite(img, (x, 272 - img.height))
            x += img.width + 16
        tela.save(previa)
        print(f'prévia: {previa}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--previa', help='salva uma prévia com todos os tamanhos')
    gerar(parser.parse_args().previa)


if __name__ == '__main__':
    main()
