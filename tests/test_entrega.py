"""Fase 21: tools/montar_entrega.py monta a pasta da entrega com os nomes da rubrica."""
import importlib.util
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest

FERRAMENTA = Path(__file__).resolve().parents[1] / 'tools' / 'montar_entrega.py'
pytestmark = pytest.mark.skipif(shutil.which('git') is None, reason='precisa do git')


def _ferramenta():
    spec = importlib.util.spec_from_file_location('montar_entrega', FERRAMENTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _git(raiz, *args):
    subprocess.run(['git', '-c', 'user.name=Teste', '-c', 'user.email=teste@exemplo.com', *args],
                   cwd=raiz, check=True, capture_output=True)


@pytest.fixture
def projeto(tmp_path):
    raiz = tmp_path / 'flappybird'
    for nome, conteudo in {'README.md': '# Flappy', 'LICENSE': 'MIT', 'CREDITOS.md': 'créditos',
                           'requirements.txt': 'pygame', 'src/main.py': 'print(1)',
                           '.gitignore': '.venv/\n/data/\n/entrega/\n'}.items():
        arquivo = raiz / nome
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(conteudo, encoding='utf-8')
    _git(raiz, 'init', '-q')
    _git(raiz, 'add', '-A')
    _git(raiz, 'commit', '-q', '-m', 'inicio')
    (raiz / 'data').mkdir()
    (raiz / 'data' / 'save.json').write_text('{"wallet": 999}', encoding='utf-8')     # o save do jogador
    (raiz / '.venv').mkdir()
    (raiz / '.venv' / 'lib.py').write_text('x', encoding='utf-8')
    return raiz


@pytest.fixture
def arquivos(tmp_path):
    pdf = tmp_path / 'relatorio.pdf'
    pdf.write_bytes(b'%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n')
    pptx = tmp_path / 'apresentacao.pptx'
    with zipfile.ZipFile(pptx, 'w') as z:
        z.writestr('ppt/presentation.xml', '<p:presentation/>')
    return pdf, pptx


def test_monta_a_pasta_com_os_nomes_da_rubrica(projeto, arquivos, tmp_path):
    m = _ferramenta()
    pasta, problemas, avisos = m.montar(*arquivos, raiz=projeto, saida=tmp_path / 'saida')
    assert problemas == [] and avisos == []
    assert pasta.name == 'PPEM Python – Pedro-Ruan-Guilherme – Projeto 2 – 26.2'
    nomes = sorted(p.name for p in pasta.iterdir())
    assert nomes == sorted([f'{m.NOME} – Código.zip', f'{m.NOME} – Relatório.pdf',
                            f'{m.NOME} – Apresentação.pptx', 'Link do GitHub.txt'])
    assert m.LINK_GITHUB in (pasta / 'Link do GitHub.txt').read_text(encoding='utf-8')


def test_zip_do_codigo_leva_so_o_commitado(projeto, arquivos, tmp_path):
    m = _ferramenta()
    pasta, _, _ = m.montar(*arquivos, raiz=projeto, saida=tmp_path / 'saida')
    with zipfile.ZipFile(pasta / f'{m.NOME} – Código.zip') as z:
        nomes = z.namelist()
    assert 'flappybird/README.md' in nomes and 'flappybird/src/main.py' in nomes
    assert not any('data/' in n or '.venv' in n for n in nomes)       # nunca o save nem o ambiente


def test_avisa_mudancas_nao_commitadas(projeto, arquivos, tmp_path):
    m = _ferramenta()
    (projeto / 'README.md').write_text('# mudado', encoding='utf-8')
    _, problemas, avisos = m.montar(*arquivos, raiz=projeto, saida=tmp_path / 'saida')
    assert problemas == [] and len(avisos) == 1 and 'README.md' in avisos[0]


def test_acusa_arquivo_que_nao_abriria(projeto, arquivos, tmp_path):
    m = _ferramenta()
    pdf, pptx = arquivos
    pdf.write_bytes(b'%PDF-1.7\nmetade do arquivo')                      # download interrompido
    _, problemas, _ = m.montar(pdf, None, raiz=projeto, saida=tmp_path / 'saida')
    assert any('Relatório.pdf' in p and 'incompleto' in p for p in problemas)
    assert any(p.startswith('Apresentação') for p in problemas)


def test_confere_o_conteudo_do_codigo(tmp_path):
    m = _ferramenta()
    ruim = tmp_path / 'ruim.zip'
    with zipfile.ZipFile(ruim, 'w') as z:
        z.writestr('flappybird/src/main.py', '')
        z.writestr('flappybird/.venv/lib.py', '')
    erro = m.conferir_codigo(ruim)
    assert 'README.md' in erro
    assert m.conferir_pptx(tmp_path / 'ruim.zip') == 'não é uma apresentação do PowerPoint'
