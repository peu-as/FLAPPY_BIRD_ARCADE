import json

from flappy_arcade.systems.save_manager import PADRAO, VERSAO_ATUAL, SaveManager


def test_sem_arquivo_usa_padrao(tmp_path):
    save = SaveManager(tmp_path / 'save.json')
    assert save.load() == PADRAO


def test_grava_e_le_de_volta(tmp_path):
    save = SaveManager(tmp_path / 'save.json')
    save.load()
    save.section('wallet')['coins'] = 125
    save.section('skins')['owned'].append('azul')
    assert save.save()
    outro = SaveManager(tmp_path / 'save.json').load()
    assert outro['wallet']['coins'] == 125
    assert outro['skins']['owned'] == ['classico', 'azul']
    assert not (tmp_path / 'save.json.tmp').exists()


def test_corrompido_e_isolado_e_backup_assume(tmp_path):
    caminho = tmp_path / 'save.json'
    save = SaveManager(caminho)
    save.load()
    save.section('wallet')['coins'] = 10
    save.save()
    save.section('wallet')['coins'] = 20
    save.save()                               # .bak guarda o save com 10 moedas
    caminho.write_text('{ isto não é json', encoding='utf-8')
    dados = SaveManager(caminho).load()
    assert dados['wallet']['coins'] == 10
    assert list(tmp_path.glob('save.corrupt-*.json')), 'o arquivo ruim deve ser guardado'


def test_corrompido_sem_backup_volta_ao_padrao(tmp_path):
    caminho = tmp_path / 'save.json'
    caminho.write_text('[1, 2, 3]', encoding='utf-8')
    assert SaveManager(caminho).load() == PADRAO


def test_campos_faltando_ou_tipo_errado_sao_corrigidos(tmp_path):
    caminho = tmp_path / 'save.json'
    caminho.write_text(json.dumps({
        'version': 1, 'wallet': {'coins': 'muitas'},
        'settings': {'music': False}, 'extra_futuro': 42}), encoding='utf-8')
    dados = SaveManager(caminho).load()
    assert dados['wallet']['coins'] == 0            # tipo errado -> padrão
    assert dados['settings']['music'] is False      # valor válido preservado
    assert dados['settings']['sfx'] is True         # ausente -> padrão
    assert dados['extra_futuro'] == 42              # chave desconhecida preservada


def test_migracao_de_versao_antiga(tmp_path):
    caminho = tmp_path / 'save.json'
    caminho.write_text(json.dumps({'wallet': {'coins': 7}}), encoding='utf-8')   # sem versão = v0
    dados = SaveManager(caminho).load()
    assert dados['version'] == VERSAO_ATUAL
    assert dados['wallet']['coins'] == 7


def test_reset_mantem_configuracoes(tmp_path):
    save = SaveManager(tmp_path / 'save.json')
    save.load()
    save.section('settings')['music'] = False
    save.section('wallet')['coins'] = 999
    save.section('progress')['flappy'] = {'liberadas': 7}
    save.reset_progress()
    dados = SaveManager(tmp_path / 'save.json').load()
    assert dados['wallet']['coins'] == 0
    assert dados['progress'] == {}
    assert dados['settings']['music'] is False


def test_pasta_sem_permissao_nao_trava_o_jogo(tmp_path):
    bloqueio = tmp_path / 'arquivo'
    bloqueio.write_text('x')                  # um arquivo no lugar da pasta
    save = SaveManager(bloqueio / 'data' / 'save.json')
    save.load()
    assert save.save() is False
    assert save.gravavel is False


def test_dois_saves_corrompidos_no_mesmo_segundo_nao_se_sobrescrevem(tmp_path, monkeypatch):
    import time as modulo_time
    monkeypatch.setattr(modulo_time, 'strftime', lambda formato: '20261111-120000')
    caminho = tmp_path / 'save.json'
    for conteudo in ('{quebrado 1', '{quebrado 2'):
        caminho.write_text(conteudo, encoding='utf-8')
        SaveManager(caminho).load()
    isolados = sorted(x.read_text(encoding='utf-8') for x in tmp_path.glob('save.corrupt-*.json'))
    assert isolados == ['{quebrado 1', '{quebrado 2']
