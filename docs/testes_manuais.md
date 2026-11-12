# Testes manuais e checklist de entrega

Complementa os testes automáticos (`python -m pytest`, 640 testes, e `python tools/verificar_jogo.py`). Marque cada item com ✅ (ok) ou ❌ (problema, com observação) antes da entrega. Os itens 1 a 3 vêm do checklist das Aulas 05.0/05.1 e da Sprint 05.

**Testado por:** ____________________ **Data:** ___/___/2026 **Commit:** ____________

## 1. Código-fonte

| # | Teste | Como | Resultado |
|---|---|---|---|
| 1.1 | O jogo abre pelo código | `python src/main.py` com o `.venv` ativo | |
| 1.2 | Verificação automática | `python tools/verificar_jogo.py` termina com PRONTO PARA O COMMIT | |
| 1.3 | Clone limpo | clonar o repositório numa pasta nova, criar o `.venv`, `pip install -r requirements.txt`, rodar | |
| 1.4 | Repositório limpo | no GitHub não aparecem `.venv/`, `data/`, `build/`, `dist/` | |

## 2. Executável

| # | Teste | Como | Resultado |
|---|---|---|---|
| 2.1 | Gera o executável | comando do PyInstaller do README; aparece `dist\FlappyBird.exe` | |
| 2.2 | Abre fora do projeto | copiar o `.exe` para outra pasta (ex.: Área de Trabalho) e abrir com dois cliques | |
| 2.3 | Imagens e sons | menu com música, sons ao pular e pontuar, skins e cenários aparecem | |
| 2.4 | Persistência | ganhar moedas e uma estrela, jogar o Clássico até o ranking, fechar, reabrir: moedas, estrela e ranking continuam (ficam em `%LOCALAPPDATA%\FlappyBird`) | |

## 3. Jogo completo (Clássico)

| # | Teste | Resultado |
|---|---|---|
| 3.1 | Menu → cadastro do nome → partida | |
| 3.2 | ESPAÇO e clique fazem o pássaro bater asas; colisão com cano e chão tira vida | |
| 3.3 | Pontuação sobe ao passar os canos; fases Galaga e Donkey Kong aparecem | |
| 3.4 | P pausa e retoma; S liga e desliga o som | |
| 3.5 | GAME OVER com pontuação, recorde e medalha; reiniciar começa nova partida | |

## 4. Modos novos

| # | Teste | Resultado |
|---|---|---|
| 4.1 | Mapa do Donkey Kong: casa 1 vencida dá estrelas e moedas e abre a casa 2 | |
| 4.2 | Galaga e Flappy: uma casa comum e uma de chefão (Modo Apresentação) | |
| 4.3 | Estilingue: arrastar e soltar lança pela mira; habilidade no ar; barril explode | |
| 4.4 | Combina 3: trocar por clique, por arraste e por teclado; peça especial; chefão ataca | |
| 4.5 | Arcade: casa 1 do capítulo 1 | |
| 4.6 | Modo Livre: cair não encerra; recorde de sequência salvo | |
| 4.7 | Loja: comprar uma skin e um cenário; Equipamentos: modo fixo e aleatório | |
| 4.8 | Configurações: música, efeitos sonoros e efeitos visuais ligam e desligam | |
| 4.9 | Dica de tutorial aparece uma vez em cada modo novo | |
| 4.10 | Ctrl + Shift + A no menu: tudo liberado; de novo: volta ao jogo normal intacto | |
| 4.11 | Janela redimensionada: o jogo mantém a proporção (faixas nas bordas) | |

## 5. Entrega

| # | Item | Resultado |
|---|---|---|
| 5.1 | Pasta e arquivos com o nome **PPEM Python – Pedro-Ruan-Guilherme – Projeto 2 – 26.2** (`python tools/montar_entrega.py` termina com ENTREGA PRONTA) | |
| 5.2 | Relatório PDF abre e está completo | |
| 5.3 | Apresentação PowerPoint abre | |
| 5.4 | README com imagens e instruções; link do GitHub funcionando | |
| 5.5 | Créditos e bibliografia (`CREDITOS.md`, relatório e último slide) | |

## Limitações conhecidas

- **Física por quadro:** como no jogo original das aulas, gravidade e salto são somados a cada quadro, calibrados para 30 quadros por segundo. Num computador que não mantém 30 FPS, o jogo fica mais lento em vez de pular quadros. Nas partidas medidas, 99% dos quadros ficam abaixo de 13 ms (o limite é 33 ms); os picos isolados aparecem ao abrir telas, como as prévias da loja.
- **Dificuldade medida por robôs:** o robô da Galaga morre mais que uma pessoa nos mergulhos (só a forma da curva é confiável), o Donkey Kong não tem robô e o robô "bom" do Combina 3 enxerga as peças que vão cair. As curvas foram conferidas também jogando; ajustes finos estão documentados em `docs/balanceamento.md`.
- **Executável sem assinatura digital:** o Windows pode mostrar o aviso do Microsoft Defender SmartScreen. Não desative as proteções; o código-fonte está no repositório para quem preferir rodar pelo Python.
- **Executável testado no Windows;** pelo código-fonte o jogo também roda em Linux (é onde os testes automáticos rodam).
- **Ranking e progresso são locais:** ficam no computador (`data/` pelo código-fonte, `%LOCALAPPDATA%\FlappyBird` no executável); não há ranking online.
- **Recursos de terceiros:** sprites e sons do repositório do curso e as skins de times (inspiradas em clubes) são para uso acadêmico; para distribuir o executável publicamente seria preciso verificar a permissão de cada recurso (veja `CREDITOS.md`).
