# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code icin planlama otomasyonu, kalici bellek, akilli commit ve daha fazlasini ekleyen hook ve skill koleksiyonu. Ana dizininize kopyalayin, hemen calismaya baslasin.

## Icerik

### Hook'lar

| Hook                  | Olay               | Aciklama                                                                  |
|-----------------------|---------------------|---------------------------------------------------------------------------|
| `plan-mode.py`        | UserPromptSubmit    | Anahtar kelime veya karmasiklik puanlamasiyla planlama ihtiyacini tespit eder, 5 fazli is akisi enjekte eder |
| `save-plan.py`        | PostToolUse         | Tamamlanan planlari diske kaydeder, masaustu bildirimi gonderir           |
| `memory-load.py`      | SessionStart        | Projeye ozel bellegi (MEMORY.md + konu dosyalari) baglama yukler          |
| `memory-save.py`      | Stop                | Oturum bitmeden once ajanin ogrendiklerini kaydetmesini hatirlatir        |
| `compact-reinject.py` | SessionStart:compact| Baglam sikistirmasindan sonra AGENTS.md veya CLAUDE.md'yi yeniden enjekte eder |
| `notify.py`           | (yardimci modul)    | Platformlar arasi masaustu bildirimleri (macOS, Linux, Windows)           |

### Skill'ler

| Skill                                          | Komut                      | Aciklama                                                    |
|------------------------------------------------|----------------------------|-------------------------------------------------------------|
| `commit`                                       | `/commit`                  | Repo stilini taklit eden conventional commit'ler             |
| `task-plan`                                    | `/task-plan`               | PRD'yi ozelliklere ayirma ve otonom yurutme                  |
| `bug-report`                                   | `/bug-report`              | Sistematik hata analizi ve yapilandirilmis rapor olusturma   |
| `initialize`                                   | `/initialize`              | Kod tabanini tarayarak AGENTS.md olusturur                   |
| `init` (yalnizca Factory Droid)                | `/init`                    | Kod tabanini tarayarak CLAUDE.md olusturur                   |
| `implementation-planning` (yalnizca Factory Droid) | `/implementation-planning` | AskUser sorulariyla interaktif planlama                  |

## Dizin Yapisi

```
cli-tweaks/
  .factory/          <-- Factory Droid (Kiro)
    hooks/
    skills/
    settings.json
  .claude/           <-- Claude Code
    hooks/
    skills/
    settings.json
```

## Kurulum

### Hizli Kurulum (her seyi kopyala)

```bash
git clone https://github.com/KilimcininKorOglu/cli-tweaks.git
cd cli-tweaks

# Factory Droid
cp -r .factory/hooks/* ~/.factory/hooks/
cp -r .factory/skills/* ~/.factory/skills/

# Claude Code
cp -r .claude/hooks/* ~/.claude/hooks/
cp -r .claude/skills/* ~/.claude/skills/
```

### Hook Kaydi

Dosyalari kopyaladiktan sonra, repodaki `settings.json` icerisindeki hooks bolumunu kendi ayar dosyaniza birlestiriniz:

| Platform      | Kaynak                    | Hedef                      |
|---------------|---------------------------|----------------------------|
| Factory Droid | `.factory/settings.json`  | `~/.factory/settings.json` |
| Claude Code   | `.claude/settings.json`   | `~/.claude/settings.json`  |

Bu repodaki her `settings.json` dosyasi, birlestirmeye hazir tam hook yapilandirmasini icerir. Olay eslemeleri ve zaman asimlari icin dosyalari inceleyin.

### Secmeli Kurulum

Yalnizca ihtiyaciniz olanlari secin. Asagidaki ornekler `.factory/` kullanir; Claude Code icin `.claude/` ile degistirin.

```bash
# Yalnizca planlama hook'lari (notify.py, save-plan.py icin gereklidir)
cp .factory/hooks/plan-mode.py ~/.factory/hooks/
cp .factory/hooks/save-plan.py ~/.factory/hooks/
cp .factory/hooks/notify.py ~/.factory/hooks/

# Yalnizca bellek sistemi
cp .factory/hooks/memory-load.py ~/.factory/hooks/
cp .factory/hooks/memory-save.py ~/.factory/hooks/

# Yalnizca commit skill'i
cp -r .factory/skills/commit ~/.factory/skills/
```

> **Not:** `save-plan.py`, calisma zamaninda `notify.py`'yi import eder. Her zaman `notify.py`'yi de birlikte kopyalayin.

Ardindan ilgili hook kayitlarini `settings.json` dosyaniza ekleyin.

## Nasil Calisir

### Planlama Modu

"plan this feature" veya "planla" gibi bir sey yazdiginizda ya da karmasik bir istek gonderdiginizde (puanlama ile tespit edilir), hook 5 fazli bir is akisi enjekte eder:

1. **Kesfet** -- Kod tabani baglamini topla
2. **Soru Sor** -- Kullanicidan gereksinimleri netlestir (zorunlu)
3. **Tasarla** -- Uygulama planini hazirla
4. **Sun** -- Plani onaya sun
5. **Bekle** -- Onaylanana kadar kod yazma

Tamamlanan planlar masaustu bildirimleriyle birlikte `~/.factory/plans/<proje>/` (veya `~/.claude/plans/<proje>/`) dizinine kaydedilir.

### Otomatik Bellek

Bellek sistemi, ajana oturumlar arasi kalici ve projeye ozel bir bellek saglar:

- Oturum basinda `memory-load.py`, `~/.factory/memory/<proje>/MEMORY.md` dosyasini okur ve baglama enjekte eder
- Oturum sonunda `memory-save.py`, ajanin yeni ogrendiklerini kaydetmesini hatirlatir
- Bellek dosyalari proje bazinda ana indeks ve konu dosyalariyla duzenlenir

### Sikistirma Sonrasi Yeniden Enjeksiyon

Baglam penceresi sikistirildiginda AGENTS.md veya CLAUDE.md talimatlari kaybolur. `compact-reinject.py` hook'u sikistirma olaylarini tespit eder ve dosyayi proje dizininizden yeniden okuyarak talimatlarinizi canli tutar.

### Commit Skill'i

`/commit` skill'i, commit oncesi tam git baglamini toplar (status, diff, branch, son log), reponuzun mevcut commit stilini taklit eder, git guvenlik protokolunu uygular ve `--amend`, `--wip`, `--push`, `--all` gibi bayraklari destekler.

## Gereksinimler

- Python 3.8+
- Factory Droid veya Claude Code (veya her ikisi)

## Platform Farkliliklari

| Ozellik                    | Factory Droid       | Claude Code          |
|----------------------------|---------------------|----------------------|
| Plan modu cikis olayı      | `ExitSpecMode`      | `ExitPlanMode`       |
| Yeniden enjeksiyon hedefi  | `AGENTS.md`         | `CLAUDE.md`          |
| `/init` skill'i            | Evet (CLAUDE.md)    | Hayir (yerlesik)     |
| `/implementation-planning` | Evet                | Hayir                |
| Bellek yollari             | `~/.factory/memory/`| `~/.claude/memory/`  |
| Plan kayit yollari         | `~/.factory/plans/` | `~/.claude/plans/`   |

## Lisans

MIT
