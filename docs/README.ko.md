<div align="center">

# 🎮 Offline Game Revival

### 서비스가 종료된 모바일 게임을 실제 스마트폰에서 완전한 오프라인으로 되살리는 AI 에이전트 스킬.

**서버는 사라져도, 게임은 사라지지 않는다.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

</div>

---

매년 수백 개의 모바일 게임이 서비스를 종료합니다. APK는 여전히 플레이어의 폰에 남아 있지만, 서버가 없으면 로그인도, 세이브 불러오기도, 아무것도 할 수 없습니다. 수년간 쌓인 이야기와 캐릭터, 추억에 더는 닿을 수 없게 됩니다.

**Offline Game Revival**은 실전에서 검증된 노하우를 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills)로 묶은 플레이북입니다. 코딩 에이전트(Claude Code 및 `SKILL.md`를 읽는 다른 에이전트)에게 서비스가 종료된 게임의 APK를 건네기만 하면, 에이전트가 이를 **독립 실행형 추억 에디션**으로 바꾸는 방법을 알고 있습니다. APK를 설치하면 게임을 끝까지 즐길 수 있습니다. 네트워크도, 루팅도, PC도, 런타임 인젝션도 필요 없습니다.

## ✨ 구성

| | |
|---|---|
| 🔍 **정찰(Recon)** | APK를 풀고 진짜 로직 계층(Lua / JS / 트랜스파일된 C#)을 찾아내며, 암호화와 리소스 무결성 검사를 파악합니다. |
| 🧩 **앵커 검증 패치** | 빌드 진입점은 단 하나. 모든 코드 치환이 자신의 앵커를 검증하므로, 원본 패키지가 바뀌면 조용히 깨진 패치를 내보내는 대신 빌드가 *요란하게 실패*합니다. |
| 🖥️ **로컬 가짜 서버** | HTTP/JSON 계층을 가로채 수백 개의 엔드포인트에 로컬 세이브 데이터로 응답합니다. 모든 엔드포인트의 호출처와 읽는 값을 파악해 안전한 기본값을 생성하는 방법론을 담았습니다. |
| 📦 **리패키징 & 재서명** | 엔진 캐시 체크섬 재계산, 리소스 테이블 재구성, zipalign, 서명까지. 리버스 엔지니어링으로 밝혀낸 캐시 체크섬 알고리즘과 LayaAir native용 로더 패치도 포함되어 있습니다. |
| ✅ **실기기 검수** | "화면이 열린다"와 "동작한다"는 다릅니다. 상태가 실제로 바뀌고 콜드 리스타트 후에도 유지되어야 합니다. 튜토리얼 기반 테스트로, 게임 자체의 가이드 단계를 실제 탭으로 그대로 따라갑니다. |
| 🎞️ **스크린샷·녹화 영상에서 데이터 구출** *(신규)* | 상점 가격, 가챠 확률, 보상, 카드 능력치 같은 서버 측 수치는 서버와 함께 사라집니다. `scripts/harvest.py`는 **수십 GB의 플레이어 스크린샷과 화면 녹화**를 분류된 수백 KB의 텍스트로 바꿔 줍니다. 키프레임 추출 → 유사 중복 제거 → 로컬 OCR → 화면별 그룹화 순으로 진행되며, **완전 오프라인에 토큰 소모 0**입니다. 이후 저렴한 텍스트 LLM에 구조화만 맡기면 됩니다. |
| 📚 **실패 대장** | 실제로 겪은 함정 80 KB 분량: 증상 → 근본 원인 → 해결 순서로 정리했습니다. 시작 시점 레이스로 인한 크래시, 조용히 화면 밖으로 밀려난 UI, 가짜 응답에 "오염"된 풀링 XHR 객체, 디스크에 쓰이지 않던 세이브…… |

## 🏆 실제 게임으로 검증

이 플레이북은 서버가 종료된 상용 모바일 게임 두 편을 되살리며 정리한 것입니다.

- **사례 A — Unity + Lua**: 완전한 싱글플레이 추억 빌드. 실제 Android 14 기기에서 검증.
- **사례 B — LayaAir native + JavaScript**: 서버 엔드포인트 315개를 로컬에서 재구현하고, 700개 이상의 회귀 어설션을 작성했습니다. 주요 시스템(스토리 챕터, 전투, 가챠, 펫, 데이트, 타워, 이벤트)을 모두 기기에서 직접 눌러 확인했고, 오프라인 라이선스 코드(Ed25519, BigInt 미사용)와 비공개 공유용 사본별 워터마크도 갖췄습니다.

두 사례 연구(익명화됨)는 [`references/`](../skills/offline-game-revival/references)에 들어 있습니다.

## 🚀 설치

**Claude Code (플러그인 마켓플레이스)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**`SKILL.md`를 읽는 모든 에이전트** — 폴더를 에이전트의 skills 디렉터리로 복사하세요. Claude Code의 경우:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

그다음엔 그냥 말하면 됩니다. *"이 게임 서버가 종료됐어. 오프라인으로 플레이할 수 있게 만들어 줘"* 또는 *"15 GB짜리 화면 녹화에서 상점 가격이랑 가챠 확률을 뽑아 줘."*

## 🎞️ 화면 녹화에서 데이터 구출하기 (단독 실행)

이 수집기는 에이전트 없이도 동작합니다.

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **의미 있는 키프레임만**: 화면이 *바뀐 뒤 안정되었을 때*만 프레임을 남기고, 전환 애니메이션과 모션 블러는 건너뜁니다. 길게 스크롤되는 목록도 빠짐없이 샘플링합니다.
- **소스 간 중복 제거**: 스크린샷과 녹화 영상에 같은 화면이 있으면 하나로 합칩니다(상태 표시줄은 무시).
- **로컬 OCR**(RapidOCR / ONNX, CPU 전용, CJK + 라틴 문자 지원): 바운딩 박스와 읽기 순서를 함께 제공합니다.
- **출력**: `for_llm/*.txt` 청크와, 바로 쓸 수 있는 프롬프트 및 JSON 스키마([`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md) 참고).

## 🧭 철학

1. **런타임이 아니라 빌드 시점에 패치한다.** "동작하는" Frida 스크립트도 영원히 주입해야 합니다. 패키지에 구워 넣은 변경은 설치만 하면 그냥 동작합니다.
2. **단일 진입점 + 앵커 검증.** 조용히 건너뛴 치환은 깨진 빌드를 배포하게 만듭니다.
3. **산출물은 소스가 아니다.** 고쳐야 할 것은 패치 스크립트이지, 출력물을 손으로 편집해서는 안 됩니다.
4. **"열린다"는 "동작한다"가 아니다.** 상태 변화와 재시작 후 유지 여부를 검증하고, 검증된 것과 구현만 된 것을 구분해 기록하세요.

## ⚖️ 책임 있는 사용

이 프로젝트는 **게임 보존**을 위한 것입니다. **공식 서비스가 종료된 이후에도** 게임을 플레이할 수 있도록 지키는 것이 목적입니다.

- 공식 서버가 **영구적으로 종료된** 게임에만 사용하세요. 운영 중인 게임에는 절대 사용하지 마세요. 치팅, 안티치트 우회, 다른 플레이어에게 영향을 주는 용도로도 사용해서는 안 됩니다.
- 이 저장소에는 **게임 에셋도, 게임 코드도, 키도 없습니다.** 방법론과 작성자가 직접 만든 도구뿐입니다.
- 저작권을 존중하세요. 추억 빌드는 비공개·비상업적으로만 사용하고, 거주 지역의 법률을 따르세요. 권리자가 게임을 재출시한다면 공식 버전을 응원해 주세요.

## 🤝 기여하기

이 스킬로 게임을 되살렸나요? 새로운 함정에 빠졌나요? **새로운 엔진 사례 연구**(Cocos, Unreal, Godot, IL2CPP 등)와 **실패 대장의 새 항목**을 담은 Issue와 PR을 언제든 환영합니다.

아끼던 게임을 이 프로젝트로 지켜냈다면 ⭐ 하나가 다른 플레이어들이 이곳을 찾는 데 큰 도움이 됩니다.

## 📄 라이선스

[MIT](../LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · 서비스 종료 · 서비스 종료 게임 · 오프라인화 · 게임 보존 · 모바일 게임 복구 · 화면 녹화 OCR</sub>
