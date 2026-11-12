"""Monta a pasta de entrega do Projeto 2 com os nomes no padrão da rubrica.

    python tools/montar_entrega.py
    python tools/montar_entrega.py --relatorio "C:\\Users\\voce\\Downloads\\relatorio.pdf" --apresentacao apres.pptx --exe

Cria entrega/<NOME>/ (a pasta entrega/ fica fora do Git) com:
  <NOME> – Código.zip         o que está COMMITADO (git archive): nunca leva .venv, data/ ou dist/
  <NOME> – Relatório.pdf      cópia do PDF indicado (ou o mais novo da pasta Downloads)
  <NOME> – Apresentação.pptx  cópia da apresentação indicada (ou a mais nova da pasta Downloads)
  Link do GitHub.txt
  FlappyBird.exe              só com --exe (gerado antes pelo PyInstaller)

Depois confere se cada arquivo abre (PDF íntegro, PPTX e ZIP válidos, código com
README e src/main.py) e termina com ENTREGA PRONTA ou com a lista do que falta.
Cada arquivo que não abre custa 0,5 ponto na rubrica: rode isto antes de enviar.
"""
import argparse
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

NOME = 'PPEM Python – Pedro-Ruan-Guilherme – Projeto 2 – 26.2'
LINK_GITHUB = 'https://github.com/peu-as/FLAPPY_BIRD_ARCADE'
RAIZ = Path(__file__).resolve().parents[1]
OBRIGATORIOS_NO_CODIGO = ('README.md', 'LICENSE', 'CREDITOS.md', 'requirements.txt', 'src/main.py')
PROIBIDOS_NO_CODIGO = ('.venv/', 'venv/', 'data/', 'build/', 'dist/', '__pycache__/')


def git(*args, raiz=RAIZ):
    return subprocess.run(['git', *args], cwd=raiz, capture_output=True, check=True).stdout


def zip_do_codigo(destino, raiz=RAIZ):
    """O que está no último commit, numa pasta flappybird/ dentro do zip."""
    dados = git('archive', '--format=zip', '--prefix=flappybird/', 'HEAD', raiz=raiz)
    destino.write_bytes(dados)


def mudancas_nao_commitadas(raiz=RAIZ):
    """Arquivos modificados ou novos que o zip (feito do commit) NÃO vai levar."""
    saida = git('status', '--porcelain', raiz=raiz).decode('utf-8', 'replace')
    return [linha[3:] for linha in saida.splitlines() if linha.strip()]


def mais_novo(pasta, extensao, contem=''):
    if not pasta.is_dir():
        return None
    candidatos = [p for p in pasta.glob(f'*{extensao}') if contem.lower() in p.name.lower()]
    return max(candidatos, key=lambda p: p.stat().st_mtime, default=None)


# ---------------------------------------------------------------- conferências
def conferir_pdf(caminho):
    dados = caminho.read_bytes()
    if not dados.startswith(b'%PDF'):
        return 'não começa com %PDF (não é um PDF)'
    if b'%%EOF' not in dados[-2048:]:
        return 'PDF incompleto (sem %%EOF no fim): baixe de novo'
    return None


def conferir_pptx(caminho):
    try:
        with zipfile.ZipFile(caminho) as z:
            if z.testzip() is not None:
                return 'arquivo corrompido'
            if 'ppt/presentation.xml' not in z.namelist():
                return 'não é uma apresentação do PowerPoint'
    except zipfile.BadZipFile:
        return 'não é um .pptx válido'
    return None


def conferir_codigo(caminho):
    try:
        with zipfile.ZipFile(caminho) as z:
            if z.testzip() is not None:
                return 'zip corrompido'
            nomes = [n.split('/', 1)[1] for n in z.namelist() if '/' in n]
    except zipfile.BadZipFile:
        return 'não é um .zip válido'
    faltam = [n for n in OBRIGATORIOS_NO_CODIGO if n not in nomes]
    if faltam:
        return 'faltam no zip: ' + ', '.join(faltam)
    sobram = sorted({p for n in nomes for p in PROIBIDOS_NO_CODIGO if n.startswith(p) or f'/{p}' in n})
    if sobram:
        return 'o zip leva pastas que não devem ir: ' + ', '.join(sobram)
    return None


def conferir_exe(caminho):
    return None if caminho.read_bytes()[:2] == b'MZ' else 'não é um executável do Windows'


# ---------------------------------------------------------------- montagem
def montar(relatorio=None, apresentacao=None, exe=None, raiz=RAIZ, saida=None):
    """Monta a pasta e devolve (pasta, problemas, avisos)."""
    pasta = (saida or raiz / 'entrega') / NOME
    if pasta.exists():
        shutil.rmtree(pasta)
    pasta.mkdir(parents=True)
    problemas, avisos = [], []

    pendentes = mudancas_nao_commitadas(raiz)
    if pendentes:
        avisos.append(f'{len(pendentes)} arquivo(s) com mudanças não commitadas ficam FORA do zip '
                      f'(ex.: {pendentes[0]}). Faça o commit e rode de novo.')
    codigo = pasta / f'{NOME} – Código.zip'
    zip_do_codigo(codigo, raiz)

    copias = []
    for rotulo, origem, extensao, conferir in (('Relatório', relatorio, '.pdf', conferir_pdf),
                                               ('Apresentação', apresentacao, '.pptx', conferir_pptx)):
        if origem is None or not Path(origem).is_file():
            problemas.append(f'{rotulo}: arquivo {extensao} não encontrado'
                             + (f' ({origem})' if origem else ' (use --' + ('relatorio' if extensao == '.pdf' else 'apresentacao') + ')'))
            continue
        destino = pasta / f'{NOME} – {rotulo}{extensao}'
        shutil.copy2(origem, destino)
        copias.append((destino, conferir))
    copias.append((codigo, conferir_codigo))

    (pasta / 'Link do GitHub.txt').write_text(f'Repositório do projeto:\n{LINK_GITHUB}\n', encoding='utf-8')

    if exe is not None:
        if Path(exe).is_file():
            destino = pasta / 'FlappyBird.exe'
            shutil.copy2(exe, destino)
            copias.append((destino, conferir_exe))
        else:
            problemas.append(f'Executável não encontrado ({exe}): gere com o PyInstaller (veja o README)')

    for arquivo, conferir in copias:
        erro = conferir(arquivo)
        if erro:
            problemas.append(f'{arquivo.name}: {erro}')
    return pasta, problemas, avisos


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--relatorio', help='PDF do relatório (padrão: o .pdf mais novo da pasta Downloads)')
    parser.add_argument('--apresentacao', help='.pptx da apresentação (padrão: o .pptx mais novo da pasta Downloads)')
    parser.add_argument('--exe', action='store_true', help='incluir dist/FlappyBird.exe')
    args = parser.parse_args()

    downloads = Path.home() / 'Downloads'
    relatorio = Path(args.relatorio) if args.relatorio else mais_novo(downloads, '.pdf', 'relat')
    apresentacao = Path(args.apresentacao) if args.apresentacao else mais_novo(downloads, '.pptx', 'apresenta')
    exe = RAIZ / 'dist' / 'FlappyBird.exe' if args.exe else None

    try:
        pasta, problemas, avisos = montar(relatorio, apresentacao, exe)
    except subprocess.CalledProcessError as erro:
        print('Erro do Git:', erro.stderr.decode('utf-8', 'replace').strip())
        print('Rode este comando dentro da pasta do projeto (C:\\projetos\\flappybird).')
        sys.exit(1)

    print(f'\nPasta: {pasta}\n')
    for arquivo in sorted(pasta.iterdir()):
        print(f'  {arquivo.name}  ({arquivo.stat().st_size / 1e6:.1f} MB)')
    for aviso in avisos:
        print(f'\nAVISO: {aviso}')
    if problemas:
        print('\nFALTA RESOLVER:')
        for problema in problemas:
            print(f'  - {problema}')
        sys.exit(1)
    print('\nENTREGA PRONTA: abra cada arquivo uma vez antes de enviar.')


if __name__ == '__main__':
    main()
