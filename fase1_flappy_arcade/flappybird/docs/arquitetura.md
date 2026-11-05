# Arquitetura — Flappy Arcade

Como rodar: `python src/main.py` · testes: `python -m pytest` · atalhos de teste: `$env:FLAPPY_DEBUG=1; python src/main.py`

## Pastas

```
src/
  main.py                    ponto de entrada (também o do PyInstaller)
  flappy_arcade/
    core/                    infraestrutura, sem regras de jogo
      app.py                 cria os serviços e roda o loop principal
      scene.py               Scene (base das telas) e SceneManager (pilha)
      display.py             janela redimensionável com letterbox
      event_bus.py           eventos entre módulos (ex.: settings_changed)
      clock.py               relógio do jogo (substituível nos testes)
      paths.py               onde ficam assets e dados do jogador
    config/
      constants.py           física, dificuldade, fases (valores originais)
      debug.py               atalhos de teste (FLAPPY_DEBUG=1)
    systems/                 serviços persistentes
      save_manager.py        save.json versionado, atômico, com backup
      settings_store.py      música / SFX / efeitos visuais
      audio_manager.py       SFX e música em canais separados
      ranking.py             Top 10 (ranking.json)
    gameplay/                o jogo original, só reorganizado
      classic_session.py     estados, ciclo de níveis, entrada e telas
      flappy.py              Passaro, Obstaculo, Chao
      galaga.py              fase Galaga e Boss Galaga
      donkey.py              fase Donkey Kong e Kong Furioso
      powerups.py, effects.py, hud.py
      difficulty.py          parâmetros por nível + justiça das passagens
      geometry.py, procedural.py, resources.py
    scenes/
      game_scene.py          conduz a ClassicSession
    ui/
      theme.py               paleta (tirada dos sprites), medidas, animação, fontes
tests/
  golden/                    gravação do jogo original e cenários
  test_golden_master.py      regra de ouro: comportamento idêntico ao original
  test_*.py                  save, configurações, áudio, cenas, janela, App
```

## Regras da casa

1. **Dependências só descem:** `scenes` → `gameplay` / `systems` → `config`. A jogabilidade não importa nada de `scenes` nem de `core.app`.
2. **Serviços chegam por injeção:** cenas recebem um `AppContext` (janela, recursos, save, settings, áudio, bus, relógio, pilha de cenas). Nada de variáveis globais.
3. **Tempo só pelo relógio injetado:** nada de `time.monotonic()` ou `pygame.time.get_ticks()` direto na jogabilidade.
4. **Cores só pelo tema:** `Palette.<NOME>`, nunca RGB solto em telas novas.
5. **A física não muda sem o golden master acusar.** Se uma mudança de jogabilidade for intencional (Fase 2 em diante), regrave a referência com `tests/golden/record_legacy.py` e explique no commit.

## Loop (mesma ordem do jogo original)

```
tick(fps da cena do topo) → eventos → update(dt) → draw(tela lógica 575x860) → janela (letterbox)
```

A física é por quadro e calibrada a 30 FPS, por isso a `GameScene` roda a 30 FPS. Telas de menu podem rodar a 60 FPS para animações mais suaves.

## Save (`data/save.json`)

```json
{ "version": 1,
  "settings": {"music": true, "sfx": true, "visual_fx": true},
  "wallet":   {"coins": 0},
  "skins":    {"owned": ["classico"], "equipped": "classico"},
  "progress": {} }
```

Mudou o formato? Aumente `VERSAO_ATUAL` e registre a migração em `MIGRACOES` (`save_manager.py`).
