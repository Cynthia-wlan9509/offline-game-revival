<div align="center">

# 🎮 Offline Game Revival

### Uma skill de agente de IA que traz de volta à vida jogos mobile desativados — totalmente offline, em um celular de verdade.

**Quando os servidores morrem, o jogo não precisa morrer.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

Todo ano, centenas de jogos mobile são desativados. O APK continua no celular dos jogadores, mas sem o servidor ele não consegue fazer login, carregar um save, nada. Anos de histórias, personagens e memórias ficam fora de alcance.

**Offline Game Revival** é um manual testado em campo, empacotado como uma [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Aponte seu agente de programação (Claude Code e outros agentes que leem `SKILL.md`) para o APK de um jogo morto e ele sabe como transformá-lo em uma **edição memorial independente**: instale o APK e jogue o jogo inteiro, sem rede, sem root, sem PC, sem injeção em tempo de execução.

## ✨ O que tem aqui

| | |
|---|---|
| 🔍 **Reconhecimento** | Desempacota o APK, encontra a camada de lógica de verdade (Lua / JS / C# transpilado) e identifica criptografia e verificações de integridade de recursos. |
| 🧩 **Patch com âncoras verificadas** | Um único ponto de entrada de build. Cada substituição de código verifica sua âncora — se o pacote original mudar, o build *falha com estardalhaço* em vez de entregar um patch quebrado em silêncio. |
| 🖥️ **Servidor falso local** | Intercepta a camada HTTP/JSON e responde centenas de endpoints a partir de um save local. Inclui uma metodologia para mapear quem chama cada endpoint e o que ele lê, e então gerar valores padrão seguros. |
| 📦 **Reempacotamento e assinatura** | Recalcula os checksums do cache da engine, reconstrói as tabelas de recursos, faz zipalign e assina. Inclui um algoritmo de checksum de cache obtido por engenharia reversa e patches de loader para LayaAir native. |
| ✅ **Aceitação no aparelho** | "A tela abre" ≠ "funciona". O estado precisa mudar de verdade e sobreviver a uma reinicialização a frio. Teste guiado pelo tutorial: siga os passos do próprio guia do jogo com toques reais. |
| 🎞️ **Resgate de dados de screenshots e gravações** *(novo)* | Os números do lado do servidor (preços da loja, taxas de gacha, recompensas, status de cartas) morrem junto com o servidor. O `scripts/harvest.py` transforma **dezenas de GB de screenshots e gravações de tela de jogadores** em algumas centenas de KB de texto categorizado — quadros-chave → remoção de quase duplicatas → OCR local → agrupamento por tela — **totalmente offline, zero tokens** — e então o `scripts/llm_structure.py` processa tudo em lotes com DeepSeek / OpenAI / Qwen / Kimi / Ollama local e gera JSON + CSV consolidados. |
| ⏩ **Testes de viagem no tempo** *(novo)* | O `scripts/timewarp` roda seu servidor falso em um sandbox com relógio virtual: avance dias, reinicie o app e **audite cada recompensa** — se a resposta diz "+50 gemas" mas o save não mudou, o teste falha. Simule 30 dias de jogo em um segundo e veja em que dia cada barreira se torna alcançável. Zero dependências. |
| 🤝 **Qualquer agente, qualquer modelo** *(novo)* | Funciona com Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… via `SKILL.md` + `AGENTS.md`. Traz papéis de subagente (scout / worker / verifier) para que um modelo caro tome as decisões e os baratos façam o trabalho braçal. Sem agente nenhum? Cole o `prompts/chat-playbook.md` no DeepSeek / ChatGPT e execute os comandos que ele passar. |
| 📚 **Registro de falhas** | 100 KB de armadilhas reais: sintoma → causa raiz → correção. Crashes por condição de corrida na inicialização, UI que saiu da tela sem avisar, objetos XHR de pool "envenenados" por respostas falsas, saves que nunca chegavam ao disco… |

## 🏆 Provado em jogos reais

O manual foi destilado da ressurreição de dois jogos mobile comerciais cujos servidores foram desligados:

- **Caso A — Unity + Lua**: build memorial single-player completo, verificado em um celular Android 14 físico.
- **Caso B — LayaAir native + JavaScript**: 315 endpoints de servidor reimplementados localmente, mais de 700 asserções de regressão e todos os sistemas principais (capítulos da história, batalhas, gacha, pets, namoro, torre, eventos) testados na mão em um aparelho, além de códigos de licença offline (Ed25519, sem BigInt) e marcas d'água por cópia para compartilhamento privado.

Os dois estudos de caso (anonimizados) estão incluídos em [`references/`](../skills/offline-game-revival/references).

## 🚀 Instalação

**Claude Code (marketplace de plugins)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Qualquer agente que suporte Agent Skills** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose…) — copie a pasta para o diretório de skills desse agente:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Os demais agentes leem o [`AGENTS.md`](../AGENTS.md), que os direciona para a skill. Os papéis de subagente estão em [`agents/`](../agents).

**Só chat (DeepSeek / ChatGPT / Kimi web)** — cole o [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) como primeira mensagem. O modelo vira seu engenheiro-chefe; você executa os comandos que ele passar e cola a saída de volta.

Depois é só pedir: *"Os servidores desse jogo foram desligados — deixe ele jogável offline"* ou *"Extraia os preços da loja e as taxas de gacha desses 15 GB de gravações de tela."*

## 🎞️ Resgate dados de gravações de tela (independente)

O extrator funciona sem nenhum agente:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # ou OPENAI_API_KEY, DASHSCOPE_API_KEY… (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # estrutura 2 blocos para checar a qualidade
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # tudo → out/structured/merged.json
```

- **Quadros-chave que importam**: só guarda um quadro quando a tela *mudou e se estabilizou* — pula animações de transição e motion blur; listas longas com rolagem continuam sendo amostradas.
- **Deduplicação entre fontes**: a mesma tela vinda de um screenshot e de uma gravação é unificada (a barra de status é ignorada).
- **OCR local** (RapidOCR / ONNX, só CPU, CJK + latino) com caixas delimitadoras e ordem de leitura.
- **Saída**: blocos `for_llm/*.txt` mais um prompt pronto e um schema JSON em [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md); o `llm_structure.py` consolida todas as respostas e sinaliza números conflitantes.

## ⏩ Testes de viagem no tempo (independente)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 passaram
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # pega 3 bugs plantados
```

Aponte `timewarp.create({ files, entry, inventory, granted })` para o seu próprio servidor falso. A lista de bugs de tempo que valem ser testados (horário de reset, loops de login diário, limites de regeneração, timers, persistência após reiniciar) está em [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Filosofia

1. **Aplique o patch em tempo de build, não em tempo de execução.** Um script Frida que "funciona" precisa ser injetado para sempre. Mudanças embutidas no pacote são instaladas e simplesmente funcionam.
2. **Ponto de entrada único + asserções de âncora.** Substituições ignoradas em silêncio geram builds quebrados.
3. **Artefatos não são código-fonte.** Corrija o script de patch; nunca edite a saída na mão.
4. **"Abre" não é "funciona".** Verifique as mudanças de estado, que elas sobrevivam a reinicializações, e registre o que foi verificado e o que foi apenas implementado.

## ⚖️ Uso responsável

Este projeto trata de **preservação de jogos**: manter os jogos jogáveis **depois que o serviço oficial acabou**.

- Use apenas em jogos cujos servidores oficiais foram **desligados de forma permanente**. Nunca em jogos ativos, nunca para trapacear, burlar anti-cheat ou afetar outros jogadores.
- O repositório **não contém assets do jogo, código do jogo nem chaves** — apenas métodos e as ferramentas do próprio autor.
- Respeite os direitos autorais: mantenha as edições memoriais privadas e sem fins comerciais, e siga as leis da sua jurisdição. Se a detentora dos direitos relançar o jogo, apoie a versão oficial.

## 🤝 Contribuindo

Reviveu um jogo com esta skill? Caiu em uma armadilha nova? Issues e PRs com **novos estudos de caso de engines** (Cocos, Unreal, Godot, IL2CPP…) e **novas entradas para o registro de falhas** são muito bem-vindos.

Se isto salvou um jogo que você amava, uma ⭐ ajuda outros jogadores a encontrá-lo.

## 📄 Licença

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · testes de viagem no tempo · multiagente · múltiplos agentes de IA · jogo desativado · servidor encerrado · jogar offline · preservação de jogos · jogo mobile sem servidor · fim dos servidores</sub>
