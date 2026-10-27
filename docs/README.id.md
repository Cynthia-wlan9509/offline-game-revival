<div align="center">

# 🎮 Offline Game Revival

### Skill agen AI yang menghidupkan kembali game mobile yang servernya sudah ditutup — sepenuhnya offline, di ponsel sungguhan.

**Server boleh mati, tapi game jangan ikut mati.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)
[![GitHub stars](https://img.shields.io/github/stars/Cynthia-wlan9509/offline-game-revival?style=flat&logo=github&label=stars&color=f5c518)](https://github.com/Cynthia-wlan9509/offline-game-revival/stargazers)

</div>

---

Setiap tahun, ratusan game mobile ditutup. APK-nya masih ada di ponsel para pemain, tetapi tanpa server ia tidak bisa login, tidak bisa memuat save, tidak bisa apa-apa. Bertahun-tahun cerita, karakter, dan kenangan pun tak lagi terjangkau.

**Offline Game Revival** adalah panduan yang sudah teruji di lapangan, dikemas sebagai [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills). Arahkan agen coding Anda (Claude Code dan agen lain yang membaca `SKILL.md`) ke APK sebuah game yang sudah mati, dan ia tahu cara mengubahnya menjadi **edisi kenangan yang berdiri sendiri**: pasang APK, mainkan seluruh game — tanpa jaringan, tanpa root, tanpa PC, tanpa injeksi saat runtime.

## ✨ Isinya

| | |
|---|---|
| 🔍 **Recon** | Membongkar APK, menemukan lapisan logika yang sebenarnya (Lua / JS / C# hasil transpile), serta mengidentifikasi enkripsi dan pemeriksaan integritas resource. |
| 🧩 **Patching dengan anchor yang diverifikasi** | Satu titik masuk build. Setiap penggantian kode memverifikasi anchor-nya — jika paket aslinya berubah, build akan *gagal dengan keras* alih-alih diam-diam merilis patch yang rusak. |
| 🖥️ **Server palsu lokal** | Mencegat lapisan HTTP/JSON dan menjawab ratusan endpoint dari save lokal. Dilengkapi metodologi untuk memetakan siapa pemanggil tiap endpoint dan apa yang dibacanya, lalu menghasilkan nilai default yang aman. |
| 📦 **Repack & tanda tangan ulang** | Menghitung ulang checksum cache engine, membangun ulang tabel resource, zipalign, lalu menandatangani. Termasuk algoritma checksum cache hasil reverse engineering dan patch loader untuk LayaAir native. |
| ✅ **Akseptansi di perangkat** | "Layar bisa terbuka" ≠ "berfungsi". State harus benar-benar berubah dan bertahan setelah cold restart. Pengujian berbasis tutorial: ikuti langkah panduan bawaan game dengan ketukan sungguhan. |
| 🎞️ **Penyelamatan data dari screenshot & rekaman layar** *(baru)* | Angka di sisi server (harga toko, rate gacha, hadiah, stat kartu) ikut hilang bersama server. `scripts/harvest.py` mengubah **puluhan GB screenshot dan rekaman layar pemain** menjadi beberapa ratus KB teks yang sudah dikategorikan — keyframe → penghapusan gambar yang nyaris kembar → OCR lokal → pengelompokan per layar — **sepenuhnya offline, nol token** — lalu `scripts/llm_structure.py` memprosesnya secara batch lewat DeepSeek / OpenAI / Qwen / Kimi / Ollama lokal dan menggabungkannya menjadi JSON + CSV. |
| ⏩ **Uji perjalanan waktu** *(baru)* | `scripts/timewarp` menjalankan server palsu Anda di sandbox dengan jam virtual: percepat beberapa hari, restart aplikasi, dan **audit setiap hadiah** — jika respons bilang "+50 gem" tetapi save tidak berubah, tes gagal. Simulasikan 30 hari bermain dalam satu detik dan lihat di hari ke berapa tiap gerbang bisa dilewati. Nol dependensi. |
| 🤝 **Agen apa pun, model apa pun** *(baru)* | Bekerja dengan Claude Code, Codex, Cursor, Copilot, OpenCode, Gemini CLI… lewat `SKILL.md` + `AGENTS.md`. Dilengkapi peran sub-agen (scout / worker / verifier) agar model mahal yang mengambil keputusan dan model murah yang mengerjakan pekerjaan kasarnya. Tidak punya agen sama sekali? Tempel `prompts/chat-playbook.md` ke DeepSeek / ChatGPT lalu jalankan perintah yang diberikannya. |
| 📚 **Catatan kegagalan** | 100 KB jebakan nyata: gejala → akar masalah → solusi. Crash akibat race saat startup, UI yang diam-diam bergeser ke luar layar, objek XHR dari pool yang "teracuni" respons palsu, save yang tidak pernah tertulis ke disk… |

## 🏆 Terbukti pada game sungguhan

Panduan ini disarikan dari proses menghidupkan kembali dua game mobile komersial yang servernya ditutup:

- **Kasus A — Unity + Lua**: build kenangan single-player yang lengkap, diverifikasi di ponsel Android 14 fisik.
- **Kasus B — LayaAir native + JavaScript**: 315 endpoint server diimplementasikan ulang secara lokal, 700+ assertion regresi, dan semua sistem utama (bab cerita, pertarungan, gacha, pet, dating, tower, event) dicoba satu per satu langsung di perangkat.

Kedua studi kasus (sudah dianonimkan) ada di [`references/`](../skills/offline-game-revival/references).

## 🚀 Instalasi

**Claude Code (plugin marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Agen apa pun yang mendukung Agent Skills** (Claude Code, OpenAI Codex, Cursor, GitHub Copilot, OpenCode, Goose…) — salin foldernya ke direktori skills agen tersebut:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/   # Claude Code
cp -r offline-game-revival/skills/offline-game-revival ~/.codex/skills/    # Codex
```

Agen lain membaca [`AGENTS.md`](../AGENTS.md), yang mengarahkan mereka ke skill ini. Peran sub-agen ada di [`agents/`](../agents).

**Hanya chat (DeepSeek / ChatGPT / Kimi versi web)** — tempel [`prompts/chat-playbook.md`](../prompts/chat-playbook.md) sebagai pesan pertama. Modelnya menjadi lead engineer Anda; Anda menjalankan perintah yang diberikannya lalu menempelkan kembali outputnya.

Setelah itu tinggal minta: *"Server game ini sudah ditutup — buat agar bisa dimainkan offline"* atau *"Ekstrak harga toko dan rate gacha dari 15 GB rekaman layar ini."*

## 🎞️ Selamatkan data dari rekaman layar (mandiri)

Harvester ini berjalan tanpa agen apa pun:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
export DEEPSEEK_API_KEY=sk-...                                                               # atau OPENAI_API_KEY, DASHSCOPE_API_KEY… (PowerShell: $env:DEEPSEEK_API_KEY="sk-...")
python skills/offline-game-revival/scripts/llm_structure.py ./out --limit 2                  # strukturkan 2 potongan, cek kualitasnya
python skills/offline-game-revival/scripts/llm_structure.py ./out                            # semuanya → out/structured/merged.json
```

- **Keyframe yang benar-benar penting**: sebuah frame hanya disimpan jika layar *berubah lalu stabil* — animasi transisi dan motion blur dilewati; daftar panjang yang di-scroll tetap disampel.
- **Deduplikasi lintas sumber**: layar yang sama dari screenshot dan rekaman digabung (status bar diabaikan).
- **OCR lokal** (RapidOCR / ONNX, hanya CPU, CJK + Latin) lengkap dengan bounding box dan urutan baca.
- **Output**: potongan `for_llm/*.txt` plus prompt siap pakai dan skema JSON di [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md); `llm_structure.py` menggabungkan semua jawaban dan menandai angka yang saling bertentangan.

## ⏩ Uji perjalanan waktu (mandiri)

```bash
node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js            # 51 lolos
BUGGY=1 node skills/offline-game-revival/scripts/timewarp/examples/mini.test.js    # menangkap 3 bug yang sengaja ditanam
```

Arahkan `timewarp.create({ files, entry, inventory, granted })` ke server palsu Anda sendiri. Daftar periksa bug waktu yang layak diuji (jam reset, loop login harian, batas regenerasi, timer, persistensi setelah restart) ada di [`timewarp.md`](../skills/offline-game-revival/references/timewarp.md).

## 🧭 Filosofi

1. **Patch saat build, bukan saat runtime.** Skrip Frida yang "berfungsi" tetap harus diinjeksikan selamanya. Perubahan yang sudah dipanggang ke dalam paket tinggal dipasang dan langsung jalan.
2. **Satu titik masuk + assertion anchor.** Penggantian yang dilewati diam-diam menghasilkan build rusak.
3. **Artefak bukan source code.** Perbaiki skrip patch-nya, jangan pernah mengedit output secara manual.
4. **"Bisa dibuka" bukan berarti "berfungsi".** Verifikasi perubahan state, pastikan bertahan setelah restart, dan catat mana yang sudah diverifikasi dan mana yang baru sekadar diimplementasikan.

## ⚖️ Penggunaan yang bertanggung jawab dan penafian

Repositori ini dibuat untuk **mempelajari cara kerja game** dan melestarikan game yang layanan resminya sudah berakhir. Isinya hanya metode dan alat buatan penulis sendiri.

- **Tidak ada unduhan di sini.** Repositori ini tidak berisi aset game, kode game, kunci dekripsi atau kunci tanda tangan, maupun paket instalasi apa pun, dan tidak menyediakan unduhan. Mohon jangan memintanya di sini.
- **Jangan biarkan paket instalasi tersebar.** Gunakan apa yang kamu buat hanya untuk keperluan pribadi dan non-komersial, pada salinan yang kamu peroleh secara sah. Mohon jangan memublikasikan atau menjual kembali paket instalasi yang dimodifikasi, aset game, atau kunci, dan jangan menjalankan server pribadi untuk mencari untung.
- **Hanya untuk game yang layanan resminya sudah berakhir.** Mohon jangan gunakan untuk game yang masih berjalan, untuk curang, untuk mengakali anti-cheat, atau dengan cara yang merugikan pemain lain atau pemegang hak.
- **Patuhi hukum di tempatmu; kamu bertanggung jawab atas penggunaanmu sendiri.** Di Indonesia, Undang-Undang Hak Cipta (UU No. 28 Tahun 2014) melindungi program komputer; menyebarkan versi modifikasi, menjalankan server pribadi, atau menjual cheat dapat dikenai sanksi perdata maupun pidana. Aturan di negara lain bisa berbeda. Tidak ada isi di sini yang merupakan nasihat hukum atau menyatakan bahwa suatu penggunaan tertentu sah. Jika ragu, konsultasikan dengan pengacara sebelum mulai.
- **Tidak berafiliasi.** Nama game dan merek dagang adalah milik pemiliknya masing-masing. Proyek ini tidak berafiliasi dengan dan tidak didukung oleh perusahaan game mana pun.
- **Tanpa jaminan, tanpa tanggung jawab.** Semua disediakan "sebagaimana adanya" di bawah lisensi MIT. Sejauh diizinkan oleh hukum, penulis tidak bertanggung jawab atas kerusakan, kehilangan data, sanksi akun, atau akibat hukum apa pun yang timbul dari penggunaannya.
- **Untuk pemegang hak:** jika kamu merasa ada isi di sini yang melanggar hakmu, buka issue; kami akan segera memeriksanya dan menghapusnya bila perlu. Jika sebuah game kembali secara resmi, dukunglah versi resminya.

Dengan menggunakan isi repositori ini, kamu menyetujui hal-hal di atas.

## 🤝 Berkontribusi

Sudah menghidupkan kembali sebuah game dengan skill ini? Menemukan jebakan baru? Issue dan PR berisi **studi kasus engine baru** (Cocos, Unreal, Godot, IL2CPP…) dan **entri baru untuk catatan kegagalan** sangat kami sambut.

Kalau proyek ini berhasil menyelamatkan game yang Anda cintai, sebuah ⭐ akan membantu pemain lain menemukannya.

Cara ikut berkontribusi (issue, pull request, menjadi maintainer): lihat [CONTRIBUTING.md](../CONTRIBUTING.md).

## ⭐ Riwayat bintang

[![Star History Chart](https://api.star-history.com/svg?repos=Cynthia-wlan9509/offline-game-revival&type=Date)](https://star-history.com/#Cynthia-wlan9509/offline-game-revival&Date)

## 📄 Lisensi

[MIT](../LICENSE)

<sub>Keywords: game preservation · time travel testing · multi-agent · DeepSeek · ChatGPT · Codex · shut down game · server shutdown · offline mode · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · uji perjalanan waktu · multi-agen · banyak agen AI · game server ditutup · game offline · game mobile mati · pelestarian game · main game tanpa server · game tutup server</sub>
