<div align="center">

# 🎮 Offline Game Revival

### Một agent skill AI giúp hồi sinh các game mobile đã ngừng vận hành — hoàn toàn offline, chạy trên điện thoại thật.

**Máy chủ có thể tắt, nhưng game thì không nên chết theo.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Mỗi năm có hàng trăm game mobile đóng cửa. File APK vẫn nằm trong điện thoại của người chơi, nhưng không có máy chủ thì không thể đăng nhập, không tải được dữ liệu lưu, không làm được gì cả. Bao nhiêu năm cốt truyện, nhân vật và kỷ niệm bỗng nằm ngoài tầm với.

**Offline Game Revival** là một cẩm nang đã được thử lửa thực tế, đóng gói thành [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Chỉ cần trỏ agent lập trình của bạn (Claude Code và các agent khác đọc được `SKILL.md`) vào file APK của một game đã chết, nó sẽ biết cách biến game đó thành một **bản tưởng niệm chạy độc lập**: cài APK là chơi trọn game — không cần mạng, không cần root, không cần PC, không cần chèn mã lúc chạy.

## ✨ Bên trong có gì

| | |
|---|---|
| 🔍 **Trinh sát (Recon)** | Giải nén APK, tìm ra tầng logic thật sự (Lua / JS / C# đã transpile), nhận diện mã hóa và các bước kiểm tra tính toàn vẹn tài nguyên. |
| 🧩 **Vá lỗi có kiểm tra điểm neo** | Chỉ một điểm vào cho quá trình build. Mỗi lần thay thế mã đều kiểm tra điểm neo của nó — nếu gói gốc thay đổi, bản build sẽ *báo lỗi ầm ĩ* thay vì âm thầm tung ra một bản vá hỏng. |
| 🖥️ **Máy chủ giả cục bộ** | Chặn tầng HTTP/JSON và trả lời hàng trăm endpoint từ dữ liệu lưu cục bộ. Kèm phương pháp lập bản đồ xem ai gọi từng endpoint và nó đọc gì, rồi sinh ra các giá trị mặc định an toàn. |
| 📦 **Đóng gói lại & ký lại** | Tính lại checksum cache của engine, dựng lại bảng tài nguyên, zipalign, ký. Gồm thuật toán checksum cache được dịch ngược và các bản vá loader cho LayaAir native. |
| ✅ **Nghiệm thu trên thiết bị** | "Màn hình mở được" ≠ "chạy được". Trạng thái phải thực sự thay đổi và còn nguyên sau khi khởi động lại hoàn toàn. Kiểm thử theo hướng dẫn: làm theo từng bước hướng dẫn của chính game bằng những cú chạm thật. |
| 🎞️ **Cứu dữ liệu từ ảnh chụp & video quay màn hình** *(mới)* | Các con số phía máy chủ (giá cửa hàng, tỉ lệ gacha, phần thưởng, chỉ số thẻ) sẽ mất cùng máy chủ. `scripts/harvest.py` biến **hàng chục GB ảnh chụp và video quay màn hình của người chơi** thành vài trăm KB văn bản đã phân loại — khung hình chính → loại bỏ ảnh gần trùng → OCR cục bộ → gom nhóm theo từng màn hình — **hoàn toàn offline, không tốn token**, sau đó `scripts/llm_structure.py` xử lý hàng loạt qua DeepSeek / OpenAI / Qwen / Kimi / Ollama cục bộ và gộp thành JSON + CSV. |
| ⏩ **Kiểm thử du hành thời gian** *(mới)* | `scripts/timewarp` chạy server giả của bạn trong sandbox có đồng hồ ảo: tua nhanh nhiều ngày, khởi động lại app và **kiểm toán mọi phần thưởng** — nếu phản hồi ghi "+50 gem" mà file save không đổi thì test thất bại. Mô phỏng 30 ngày chơi trong một giây và xem mỗi cột mốc mở được vào ngày thứ mấy. Không phụ thuộc thư viện nào. |
| 🤝 **Agent nào, model nào cũng được** *(mới)* | Chạy được với Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… qua `SKILL.md` + `AGENTS.md`. Có sẵn các vai trò sub-agent (scout / worker / verifier) để model đắt tiền ra quyết định, còn model rẻ làm phần việc chân tay. Không có agent nào cả? Dán `prompts/chat-playbook.md` vào DeepSeek / ChatGPT rồi chạy các lệnh nó đưa ra. |
| 📚 **Sổ ghi lỗi** | 100 KB những cái bẫy có thật: triệu chứng → nguyên nhân gốc → cách sửa. Crash do race condition lúc khởi động, UI âm thầm trôi ra ngoài màn hình, đối tượng XHR trong pool bị phản hồi giả "đầu độc", dữ liệu lưu không bao giờ được ghi xuống đĩa… |

## 🏆 Đã kiểm chứng trên game thật

Cẩm nang này được đúc kết từ việc hồi sinh hai game mobile thương mại đã bị tắt máy chủ:

- **Trường hợp A — Unity + Lua**: bản tưởng niệm chơi đơn đầy đủ, đã kiểm chứng trên một điện thoại Android 14 thật.
- **Trường hợp B — LayaAir native + JavaScript**: 315 endpoint của máy chủ được cài đặt lại cục bộ, hơn 700 assertion hồi quy, và tất cả hệ thống chính (chương cốt truyện, chiến đấu, gacha, thú cưng, hẹn hò, tháp, sự kiện) đều được bấm thử trực tiếp trên thiết bị — cùng với mã giấy phép offline (Ed25519, không dùng BigInt) và watermark riêng cho từng bản sao để chia sẻ riêng tư.

Cả hai case study (đã ẩn danh) đều có trong [`references/`](../skills/offline-game-revival/references).

## 🚀 Cài đặt

**Claude Code (plugin marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Bất kỳ agent nào hỗ trợ Agent Skills** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose…) — chép thư mục vào thư mục skills của agent đó:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Các agent khác sẽ đọc [`AGENTS.md`](../AGENTS.md), file này chỉ dẫn chúng tới skill. Các vai trò sub-agent nằm trong [`agents/`](../agents).

**Chỉ có chat (DeepSeek / ChatGPT / Kimi bản web)** — dán [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) làm tin nhắn đầu tiên. Model sẽ trở thành kỹ sư trưởng của bạn; bạn chạy các lệnh nó đưa ra rồi dán kết quả trả lại.

Sau đó chỉ cần nhờ: *"Máy chủ của game này đã đóng — hãy làm cho nó chơi được offline"* hoặc *"Trích giá cửa hàng và tỉ lệ gacha từ 15 GB video quay màn hình này."*

## 🎞️ Cứu dữ liệu từ video quay màn hình (chạy độc lập)

Công cụ thu thập này chạy được mà không cần agent:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # hoặc OPENAI_API_KEY, DASHSCOPE_API_KEY… (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # cấu trúc hóa 2 đoạn để kiểm tra chất lượng
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # toàn bộ → out/structured/merged.json
```

- **Chỉ giữ khung hình chính có ý nghĩa**: chỉ giữ một khung hình khi màn hình *đã thay đổi và đã ổn định* — bỏ qua hiệu ứng chuyển cảnh và nhòe chuyển động; các danh sách dài cuộn được vẫn được lấy mẫu.
- **Loại trùng giữa các nguồn**: cùng một màn hình từ ảnh chụp và từ video sẽ được gộp lại (bỏ qua thanh trạng thái).
- **OCR cục bộ** (RapidOCR / ONNX, chỉ cần CPU, hỗ trợ CJK + Latin) kèm khung bao và thứ tự đọc.
- **Đầu ra**: các đoạn `for_llm/*.txt` cùng một prompt dựng sẵn và JSON schema trong [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md); `llm_structure.py` gộp mọi câu trả lời và đánh dấu các con số mâu thuẫn nhau.

## ⏩ Kiểm thử du hành thời gian (chạy độc lập)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 test đạt
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # bắt được 3 bug cài sẵn
```

Trỏ `timewarp.create({ files, entry, inventory, granted })` vào server giả của riêng bạn. Danh sách các lỗi liên quan đến thời gian đáng kiểm thử (giờ reset, vòng lặp điểm danh, giới hạn hồi phục, bộ đếm giờ, lưu bền sau khi khởi động lại) nằm ở [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Triết lý

1. **Vá lúc build, không vá lúc chạy.** Một script Frida "chạy được" thì phải chèn vào mãi mãi. Thay đổi đã được nướng sẵn vào gói thì cài là chạy.
2. **Một điểm vào duy nhất + kiểm tra điểm neo.** Bỏ qua âm thầm sẽ tung ra bản build hỏng.
3. **Sản phẩm đầu ra không phải mã nguồn.** Hãy sửa script vá, đừng bao giờ chỉnh tay bản đầu ra.
4. **"Mở được" không có nghĩa là "chạy được".** Hãy xác minh trạng thái thay đổi, còn nguyên sau khi khởi động lại, và ghi rõ cái gì đã kiểm chứng, cái gì mới chỉ được cài đặt.

## ⚖️ Sử dụng có trách nhiệm

Dự án này nhằm **bảo tồn game**: giúp game vẫn chơi được **sau khi dịch vụ chính thức đã kết thúc**.

- Chỉ dùng cho những game mà máy chủ chính thức đã **đóng vĩnh viễn**. Tuyệt đối không dùng cho game đang vận hành, không dùng để gian lận, vượt qua hệ thống chống gian lận, hay ảnh hưởng đến người chơi khác.
- Kho mã này **không chứa tài nguyên game, mã nguồn game hay khóa nào** — chỉ có phương pháp và công cụ do chính tác giả viết.
- Tôn trọng bản quyền: hãy giữ các bản tưởng niệm ở mức riêng tư, phi thương mại và tuân thủ luật pháp nơi bạn sinh sống. Nếu chủ sở hữu bản quyền phát hành lại game, hãy ủng hộ phiên bản chính thức.

## 🤝 Đóng góp

Bạn đã hồi sinh một game bằng skill này? Gặp phải một cái bẫy mới? Rất hoan nghênh các issue và PR với **case study cho engine mới** (Cocos, Unreal, Godot, IL2CPP…) và **mục mới cho sổ ghi lỗi**.

Nếu dự án này đã cứu một tựa game bạn yêu thích, một ⭐ sẽ giúp những người chơi khác tìm thấy nó.

Cách tham gia (issue, pull request, trở thành người cùng duy trì): xem [CONTRIBUTING.md](../CONTRIBUTING.md).

## ⭐ Lịch sử sao

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 Giấy phép

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · kiểm thử du hành thời gian · đa agent · nhiều AI agent · game ngừng hoạt động · đóng máy chủ · chơi offline · bảo tồn game · game mobile không cần server · hồi sinh game</sub>
