<div align="center">

# 🎮 Offline Game Revival

### Skill agen AI yang menghidupkan kembali game mobile yang servernya sudah ditutup — sepenuhnya offline, di ponsel sungguhan.

**Server boleh mati, tapi game jangan ikut mati.**

[English](../README.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [Bahasa Indonesia](README.id.md)

![Agent Skill](https://img.shields.io/badge/Agent%20Skill-SKILL.md-8A2BE2)
![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757)
![Engines](https://img.shields.io/badge/engines-Unity%20%2B%20Lua%20%7C%20LayaAir%20%2B%20JS-2ea44f)
![License](https://img.shields.io/badge/license-MIT-blue)

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
| 🎞️ **Penyelamatan data dari screenshot & rekaman layar** *(baru)* | Angka di sisi server (harga toko, rate gacha, hadiah, stat kartu) ikut hilang bersama server. `scripts/harvest.py` mengubah **puluhan GB screenshot dan rekaman layar pemain** menjadi beberapa ratus KB teks yang sudah dikategorikan — keyframe → penghapusan gambar yang nyaris kembar → OCR lokal → pengelompokan per layar — **sepenuhnya offline, nol token**, siap distrukturkan oleh LLM teks murah mana pun. |
| 📚 **Catatan kegagalan** | 80 KB jebakan nyata: gejala → akar masalah → solusi. Crash akibat race saat startup, UI yang diam-diam bergeser ke luar layar, objek XHR dari pool yang "teracuni" respons palsu, save yang tidak pernah tertulis ke disk… |

## 🏆 Terbukti pada game sungguhan

Panduan ini disarikan dari proses menghidupkan kembali dua game mobile komersial yang servernya ditutup:

- **Kasus A — Unity + Lua**: build kenangan single-player yang lengkap, diverifikasi di ponsel Android 14 fisik.
- **Kasus B — LayaAir native + JavaScript**: 315 endpoint server diimplementasikan ulang secara lokal, 700+ assertion regresi, dan semua sistem utama (bab cerita, pertarungan, gacha, pet, dating, tower, event) dicoba satu per satu langsung di perangkat, plus kode lisensi offline (Ed25519, tanpa BigInt) dan watermark per salinan untuk berbagi secara privat.

Kedua studi kasus (sudah dianonimkan) ada di [`references/`](../skills/offline-game-revival/references).

## 🚀 Instalasi

**Claude Code (plugin marketplace)**

```bash
/plugin marketplace add Cynthia-wlan9509/offline-game-revival
/plugin install offline-game-revival@offline-game-revival
```

**Agen apa pun yang membaca `SKILL.md`** — salin foldernya ke direktori skills agen Anda, misalnya untuk Claude Code:

```bash
git clone https://github.com/Cynthia-wlan9509/offline-game-revival
cp -r offline-game-revival/skills/offline-game-revival ~/.claude/skills/
```

Setelah itu tinggal minta: *"Server game ini sudah ditutup — buat agar bisa dimainkan offline"* atau *"Ekstrak harga toko dan rate gacha dari 15 GB rekaman layar ini."*

## 🎞️ Selamatkan data dari rekaman layar (mandiri)

Harvester ini berjalan tanpa agen apa pun:

```bash
pip install -r skills/offline-game-revival/scripts/requirements.txt
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out --limit 50   # trial run
python skills/offline-game-revival/scripts/harvest.py ./player_recordings ./out              # full run, resumable
```

- **Keyframe yang benar-benar penting**: sebuah frame hanya disimpan jika layar *berubah lalu stabil* — animasi transisi dan motion blur dilewati; daftar panjang yang di-scroll tetap disampel.
- **Deduplikasi lintas sumber**: layar yang sama dari screenshot dan rekaman digabung (status bar diabaikan).
- **OCR lokal** (RapidOCR / ONNX, hanya CPU, CJK + Latin) lengkap dengan bounding box dan urutan baca.
- **Output**: potongan `for_llm/*.txt` plus prompt siap pakai dan skema JSON di [`media-harvest.md`](../skills/offline-game-revival/references/media-harvest.md).

## 🧭 Filosofi

1. **Patch saat build, bukan saat runtime.** Skrip Frida yang "berfungsi" tetap harus diinjeksikan selamanya. Perubahan yang sudah dipanggang ke dalam paket tinggal dipasang dan langsung jalan.
2. **Satu titik masuk + assertion anchor.** Penggantian yang dilewati diam-diam menghasilkan build rusak.
3. **Artefak bukan source code.** Perbaiki skrip patch-nya, jangan pernah mengedit output secara manual.
4. **"Bisa dibuka" bukan berarti "berfungsi".** Verifikasi perubahan state, pastikan bertahan setelah restart, dan catat mana yang sudah diverifikasi dan mana yang baru sekadar diimplementasikan.

## ⚖️ Penggunaan yang bertanggung jawab

Proyek ini bertujuan untuk **pelestarian game**: menjaga game tetap bisa dimainkan **setelah layanan resminya berakhir**.

- Gunakan hanya pada game yang server resminya **ditutup secara permanen**. Jangan pernah pada game yang masih berjalan, jangan untuk curang, melewati anti-cheat, atau memengaruhi pemain lain.
- Repositori ini **tidak berisi aset game, kode game, maupun kunci** — hanya metode dan perkakas buatan penulisnya sendiri.
- Hormati hak cipta: simpan build kenangan secara privat dan nonkomersial, serta patuhi hukum di wilayah Anda. Jika pemegang hak merilis ulang game tersebut, dukunglah versi resminya.

## 🤝 Berkontribusi

Sudah menghidupkan kembali sebuah game dengan skill ini? Menemukan jebakan baru? Issue dan PR berisi **studi kasus engine baru** (Cocos, Unreal, Godot, IL2CPP…) dan **entri baru untuk catatan kegagalan** sangat kami sambut.

Kalau proyek ini berhasil menyelamatkan game yang Anda cintai, sebuah ⭐ akan membantu pemain lain menemukannya.

## 📄 Lisensi

[MIT](../LICENSE)

<sub>Keywords: game preservation · shut down game · server shutdown · offline mode · private server alternative · APK repack · Lua · LayaAir · Unity · reverse engineering for preservation · screen recording OCR · keyframe extraction · Claude Code skill · agent skills · game server ditutup · game offline · game mobile mati · pelestarian game · main game tanpa server · game tutup server</sub>
