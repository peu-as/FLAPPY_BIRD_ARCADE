# Avaliação e entrega — Projeto 2 (PPEM 2026.2)

Fonte: material do curso no repositório original (`aulas/aula-01.0-planejamento-ambiente.md`, seção 9; `aulas/aula-05.0` e `aula-05.1`; `docs/sprints/sprint-05-testes-documentacao-entrega.md`). Disciplina: Programação para Engenharia Mecânica — UFS/DMEC, prof. Wilson Luciano. Equipe: Pedro, Ruan e Guilherme. **Entrega e apresentação: terça-feira, 17/11/2026.**

## Rubrica (10,0 pontos)

| Nº | Critério | Pontos | Situação do projeto | O que falta |
|---|---|---:|---|---|
| 1 | Identificação de pasta e arquivos: **PPEM Python – Aluno1-Aluno2-Aluno3 – Projeto 2 – 26.2** | 0,5 | `tools/montar_entrega.py` monta a pasta com os nomes no padrão (Fase 21) | rodar com o PDF e o PPTX finais |
| 2 | Relatório técnico completo (PDF) | 1,0 | escrito (Fase 20): documento "PPEM Python – Pedro-Ruan-Guilherme – Projeto 2 – 26.2 – Relatório Técnico", 11 seções + créditos, com gráfico, diagrama e telas | revisar em grupo e exportar em PDF com o nome no padrão |
| 3 | Ambiente Python, dependências e estrutura | 0,5 | forte: `.venv`, `requirements.txt` (pygame, pymunk), estrutura modular | descrever no README e no relatório |
| 4 | Explicação dos parâmetros e funcionamento | 1,0 | parcial: `docs/arquitetura.md`, `docs/balanceamento.md` | tabela de parâmetros (gravidade, salto, velocidades, FPS, dificuldade) no relatório |
| 5 | Originalidade, complexidade e criatividade | 1,0 | forte: 5 mapas, Arcade, Modo Livre, Estilingue com física, Combina 3, loja | mostrar bem no relatório e na apresentação |
| 6 | Estrutura, legibilidade e qualidade do código | 1,0 | forte: cenas, injeção de dependências, regras da casa | citar a arquitetura e exemplos no relatório |
| 7 | Controles, obstáculos e colisões funcionais | 1,0 | forte | explicar colisão (retângulo + máscara) no relatório |
| 8 | Pontuação, vidas, encerramento e reinício | 1,0 | forte | demonstrar na apresentação |
| 9 | Compreensão da física e programação | 0,5 | implementado, falta explicar | seção de física: integração por quadro, gravidade e salto em px/quadro, Estilingue com pymunk |
| 10 | Testes, erros e limitações | 0,5 | forte: 640 testes, golden master, robôs; `docs/testes_manuais.md` com checklist e limitações (Fase 19) | grupo preencher o checklist; resumir no relatório |
| 11 | README e Git/GitHub | 0,5 | README do Flappy Arcade com imagens, instruções e histórico (Fase 19); repositório https://github.com/peu-as/FLAPPY_BIRD_ARCADE | enviar o histórico com as tags |
| 12 | Incrementos efetivamente implementados | 0,5 | forte (fases 8–18) | lista de incrementos no relatório |
| 13 | Apresentação em PowerPoint | 0,5 | feita (Fase 21): 16 slides com notas do orador + `docs/roteiro_apresentacao.md` | ensaiar; preparar o vídeo do plano B |
| 14 | Bibliografia e créditos | 0,5 | `CREDITOS.md` com código, IA (ChatGPT nas artes, Claude no código), recursos, bibliotecas e bibliografia (Fase 19) | repetir no relatório e no último slide |

**Entregas:** relatório PDF, código e recursos, apresentação PowerPoint, link do GitHub, README e referências. Um executável não substitui o código-fonte.

**Descontos:** −2,0 por não apresentar/ausência; −0,5 por arquivo enviado que não abre.

## Checklist da Sprint 05 / Aula 05 (entrega final)

- [ ] O jogo roda com `python src/main.py`
- [ ] `dist/FlappyBird.exe` gerado pelo PyInstaller, abre fora da pasta do projeto, com imagens e áudio
- [ ] Recorde e progresso continuam após fechar e reabrir o `.exe`
- [ ] `.gitignore` exclui `.venv/`, `data/`, `build/`, `dist/`
- [ ] `LICENSE` (MIT) para o código; nota separando código de recursos de terceiros
- [ ] README com imagem real do jogo, instruções para Windows e roadmap final
- [ ] Repositório sem `.venv`, dados pessoais ou gabarito privado
- [ ] Teste de download ZIP ou clone em ambiente limpo
- [ ] Executável distribuído só depois de verificar a permissão de redistribuir os recursos
- [ ] Créditos e recursos externos identificados

## Plano de lapidação

- **Fase 19 — Repositório:** README novo, créditos e bibliografia, `LICENSE` e `.gitignore` revisados, nomes no padrão, capturas de tela, teste do `.exe` e da persistência.
- **Fase 20 — Relatório técnico (PDF):** estrutura que cobre os critérios 2, 4, 9, 10, 12 e 14.
- **Fase 21 — Apresentação (PowerPoint):** slides, roteiro de demonstração (com o Modo Apresentação) e conferência final de que todos os arquivos abrem.
