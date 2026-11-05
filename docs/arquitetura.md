# Arquitetura — Flappy Arcade

Como rodar: `python src/main.py` (tela de modos) · `--livre` ou `--classico` abrem direto · testes: `python -m pytest` · atalhos de teste: `$env:FLAPPY_DEBUG=1; python src/main.py`

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
      difficulty_profiles.py curva de 25 níveis: Rampa/Degraus por parâmetro
      levels.py              mapas de 25 casas + jornada Arcade (capítulos e etapas)
      debug.py               atalhos de teste (FLAPPY_DEBUG=1)
    systems/                 serviços persistentes
      save_manager.py        save.json versionado, atômico, com backup
      settings_store.py      música / SFX / efeitos visuais
      audio_manager.py       SFX e música em canais separados
      ranking.py             Top 10 (ranking.json)
      progress.py            estrelas por casa; casas liberadas em sequência
    gameplay/                o jogo original, reorganizado
      classic_session.py     estados, ciclo de níveis, entrada e telas
      free_mode.py           Modo Livre: sem vidas, dificuldade pelo tempo
      level_session.py       casas dos mapas: 3 vidas, estrelas; criar_sessao(mapa, casa)
      flappy.py              Passaro, Obstaculo, Chao
      galaga.py              fase Galaga e Boss Galaga
      donkey.py              fase Donkey Kong e Kong Furioso
      powerups.py, effects.py, hud.py
      difficulty.py          tabelas originais (10 níveis) + justiça das passagens
      difficulty_curve.py    motor da curva de 25 níveis (lê os perfis)
      geometry.py, procedural.py, resources.py
    scenes/
      mode_select.py         escolha de modo (provisória até o menu da Fase 6)
      map_scene.py           mapa de 25 casas com rolagem
      level_scene.py         casa: abertura -> jogo -> resultado com estrelas
      game_scene.py          conduz a sessão (clássico ou livre)
    ui/
      theme.py               paleta (tirada dos sprites), medidas, animação, fontes
      widgets.py             texto com contorno, painel, estrela, botões com hover e teclado
tests/
  golden/                    gravação do jogo original e cenários
  test_golden_master.py      regra de ouro: clássico idêntico ao original
  test_difficulty_curve.py   curva: nível 1 = original, monotonia, passagens justas
  test_free_mode.py          regras e HUD do Modo Livre
  test_levels.py             regras das casas e do progresso
  test_menus.py              telas de modo, mapa e casa (fluxo completo)
  test_arcade.py             jornada Arcade: tabela, sessões por casa, mapa
  test_*.py                  save, configurações, áudio, cenas, janela, App
```

## Regras da casa

1. **Dependências só descem:** `scenes` → `gameplay` / `systems` → `config`. A jogabilidade não importa nada de `scenes` nem de `core.app`.
2. **Serviços chegam por injeção:** cenas recebem um `AppContext` (janela, recursos, save, settings, áudio, bus, relógio, pilha de cenas). Nada de variáveis globais.
3. **Tempo só pelo relógio injetado:** nada de `time.monotonic()` ou `pygame.time.get_ticks()` direto na jogabilidade.
4. **Cores só pelo tema:** `Palette.<NOME>`, nunca RGB solto em telas novas.
5. **Dificuldade só pelo provedor:** as fases leem `cfg` e a sessão pede `self.dificuldade.flappy/galaga/donkey(nivel)`. Nada de contas com o número do nível espalhadas pelo código.
6. **O clássico não muda sem o golden master acusar.** Depois de mudar algo de propósito no clássico, ou quando a regra do retrato (`tests/golden/snapshot.py`) mudar, regrave a referência com `python tests/golden/record_legacy.py` e explique no commit.

## Loop (mesma ordem do jogo original)

```
tick(fps da cena do topo) → eventos → update(dt) → draw(tela lógica 575x860) → janela (letterbox)
```

A física é por quadro e calibrada a 30 FPS, por isso a `GameScene` roda a 30 FPS. Telas de menu podem rodar a 60 FPS para animações mais suaves.

## Dificuldade

| Provedor | Onde | Níveis | Usado por |
|---|---|---|---|
| `DificuldadeOriginal` | `gameplay/difficulty.py` | 1 a 10 | jogo clássico (idêntico ao original) |
| `CurvaDificuldade` | `gameplay/difficulty_curve.py` + `config/difficulty_profiles.py` | 1 a 25 | Modo Livre e mapas (casa N = nível N) |

Na curva, o nível 1 é sempre o nível 1 original. Galaga e Donkey terminam no nível 10 original (o teto já testado); o Flappy vai um pouco além (gravidade 1,70, abertura 175 px, velocidade 6,2). Para balancear, edite só `config/difficulty_profiles.py` e rode `python -m pytest tests/test_difficulty_curve.py`.

## Modo Livre

Sem cadastro, ranking ou game over. Bater conta uma queda e o pássaro volta com 1,2 s de invulnerabilidade. A dificuldade sobe um nível da curva a cada `LIVRE_SEGUNDOS_POR_NIVEL` (40 s) de jogo, sem contar pausas e alertas, até o 25. Os ciclos continuam depois do 10. Recorde: maior sequência de pontos sem cair (`records.free_best_streak` no save).

## Mapas

Cada casa é um desafio fechado com 3 vidas, na dificuldade do nível N da curva. As casas são sessões que herdam da `ClassicSession`, então a física e as fases são as do original. Chefão nas casas 5, 10, 15, 20 e 25 (no Flappy, a fase dos pássaros), ligado por `cfg['chefe']`. Estrelas: 3 sem perder vida, 2 perdendo uma, 1 perdendo duas. Tempo esgotado na Galaga ou no Donkey é derrota. A casa N + 1 abre quando a N tem estrela.

## Jornada Arcade

`JORNADA` em `config/levels.py` é uma tabela de 5 capítulos (Céus, Selva, Entardecer, Noite, Espaço) com 5 casas cada; `'*'` marca o chefão, sempre na 5ª casa. Estilos: `flappy`, `passaros`, `donkey`, `galaga`. A casa N usa o nível N da curva, seja qual for o estilo. No mapa, o cenário de fundo acompanha o capítulo, cada casa tem um selo com o ícone do estilo e placas marcam os capítulos. Para mudar a jornada, edite a tabela: os testes conferem chefões no lugar certo, estilos misturados e nada repetido três vezes seguidas.

## Cuidados com o pygame

Fontes (`ui/theme.py: Fonts`) e textos prontos (`ui/widgets.py`) ficam em cache e são esvaziados sozinhos no `pygame.quit()` (`pygame.register_quit`). Nunca guarde uma `Font` em variável global fora desse cache.

## Save (`data/save.json`)

```json
{ "version": 1,
  "settings": {"music": true, "sfx": true, "visual_fx": true},
  "wallet":   {"coins": 0},
  "skins":    {"owned": ["classico"], "equipped": "classico"},
  "progress": {"flappy": {"estrelas": [3, 2, 0, ...]}},
  "records":  {"free_best_streak": 0} }
```

Mudou o formato? Aumente `VERSAO_ATUAL` e registre a migração em `MIGRACOES` (`save_manager.py`). Seções novas com valor padrão (como `records`) não precisam de migração: o save as completa sozinho.
