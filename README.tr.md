# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code için planlama otomasyonu, kalıcı bellek, akıllı commit ve daha fazlasını ekleyen hook ve skill koleksiyonu. Ana dizininize kopyalayın, hemen çalışmaya başlasın.

## İçerik

### Hook'lar

| Hook                  | Olay                 | Açıklama                                                                                                     |
|-----------------------|----------------------|--------------------------------------------------------------------------------------------------------------|
| `plan-mode.py`        | UserPromptSubmit     | Anahtar kelime veya karmaşıklık puanlamasıyla planlama ihtiyacını tespit eder, 5 fazlı iş akışı enjekte eder |
| `save-plan.py`        | PostToolUse          | Tamamlanan planları diske kaydeder, masaüstü bildirimi gönderir                                              |
| `memory-load.py`      | SessionStart         | Projeye özel belleği (MEMORY.md + konu dosyaları) bağlama yükler                                             |
| `memory-save.py`      | Stop                 | Oturum bitmeden önce ajanın öğrendiklerini kaydetmesini hatırlatır                                           |
| `compact-reinject.py` | SessionStart:compact | Bağlam sıkıştırmasından sonra AGENTS.md veya CLAUDE.md'yi yeniden enjekte eder                               |
| `notify.py`           | (yardımcı modül)     | Platformlar arası masaüstü bildirimleri (macOS, Linux, Windows)                                              |

### Skill'ler

| Skill                                              | Komut                      | Açıklama                                                   |
|----------------------------------------------------|----------------------------|------------------------------------------------------------|
| `commit`                                           | `/commit`                  | Repo stilini taklit eden conventional commit'ler           |
| `task-plan`                                        | `/task-plan`               | PRD'yi özelliklere ayırma ve otonom yürütme                |
| `bug-report`                                       | `/bug-report`              | Sistematik hata analizi ve yapılandırılmış rapor oluşturma |
| `initialize`                                       | `/initialize`              | Kod tabanını tarayarak AGENTS.md oluşturur                 |
| `init` (yalnızca Factory Droid)                    | `/init`                    | Kod tabanını tarayarak CLAUDE.md oluşturur                 |
| `implement-plan`                                   | `/implement-plan`          | AskUser sorularıyla interaktif planlama                    |

## Dizin Yapısı

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

### Hızlı Kurulum (her şeyi kopyala)

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

### Hook Kaydı

Dosyaları kopyaladıktan sonra, repodaki `settings.json` içerisindeki hooks bölümünü kendi ayar dosyanıza birleştiriniz:

| Platform      | Kaynak                   | Hedef                      |
|---------------|--------------------------|----------------------------|
| Factory Droid | `.factory/settings.json` | `~/.factory/settings.json` |
| Claude Code   | `.claude/settings.json`  | `~/.claude/settings.json`  |

Bu repodaki her `settings.json` dosyası, birleştirmeye hazır tam hook yapılandırmasını içerir. Olay eşlemeleri ve zaman aşımları için dosyaları inceleyin.

### Seçmeli Kurulum

Yalnızca ihtiyacınız olanları seçin. Aşağıdaki örnekler `.factory/` kullanır; Claude Code için `.claude/` ile değiştirin.

```bash
# Yalnızca planlama hook'ları (notify.py, save-plan.py için gereklidir)
cp .factory/hooks/plan-mode.py ~/.factory/hooks/
cp .factory/hooks/save-plan.py ~/.factory/hooks/
cp .factory/hooks/notify.py ~/.factory/hooks/

# Yalnızca bellek sistemi
cp .factory/hooks/memory-load.py ~/.factory/hooks/
cp .factory/hooks/memory-save.py ~/.factory/hooks/

# Yalnızca commit skill'i
cp -r .factory/skills/commit ~/.factory/skills/
```

> **Not:** `save-plan.py`, çalışma zamanında `notify.py`'yi import eder. Her zaman `notify.py`'yi de birlikte kopyalayın.

Ardından ilgili hook kayıtlarını `settings.json` dosyanıza ekleyin.

## Nasıl Çalışır

### Planlama Modu

"plan this feature" veya "planla" gibi bir şey yazdığınızda ya da karmaşık bir istek gönderdiğinizde (puanlama ile tespit edilir), hook 5 fazlı bir iş akışı enjekte eder:

1. **Keşfet** -- Kod tabanı bağlamını topla
2. **Soru Sor** -- Kullanıcıdan gereksinimleri netleştir (zorunlu)
3. **Tasarla** -- Uygulama planını hazırla
4. **Sun** -- Planı onaya sun
5. **Bekle** -- Onaylanana kadar kod yazma

Tamamlanan planlar masaüstü bildirimleriyle birlikte `~/.factory/plans/<proje>/` (veya `~/.claude/plans/<proje>/`) dizinine kaydedilir.

### Otomatik Bellek

Bellek sistemi, ajana oturumlar arası kalıcı ve projeye özel bir bellek sağlar:

- Oturum başında `memory-load.py`, `~/.factory/memory/<proje>/MEMORY.md` dosyasını okur ve bağlama enjekte eder
- Oturum sonunda `memory-save.py`, ajanın yeni öğrendiklerini kaydetmesini hatırlatır
- Bellek dosyaları proje bazında ana indeks ve konu dosyalarıyla düzenlenir

### Sıkıştırma Sonrası Yeniden Enjeksiyon

Bağlam penceresi sıkıştırıldığında AGENTS.md veya CLAUDE.md talimatları kaybolur. `compact-reinject.py` hook'u sıkıştırma olaylarını tespit eder ve dosyayı proje dizininizden yeniden okuyarak talimatlarınızı canlı tutar.

### Commit Skill'i

`/commit` skill'i, commit öncesi tam git bağlamını toplar (status, diff, branch, son log), reponuzun mevcut commit stilini taklit eder, git güvenlik protokolünü uygular ve `--amend`, `--wip`, `--push`, `--all` gibi bayrakları destekler.

## Gereksinimler

- Python 3.8+
- Factory Droid veya Claude Code (veya her ikisi)

## Platform Farklılıkları

| Özellik                    | Factory Droid        | Claude Code         |
|----------------------------|----------------------|---------------------|
| Plan modu çıkış olayı      | `ExitSpecMode`       | `ExitPlanMode`      |
| Yeniden enjeksiyon hedefi  | `AGENTS.md`          | `CLAUDE.md`         |
| `/init` skill'i            | Evet (CLAUDE.md)     | Hayır (yerleşik)    |
| Bellek yolları             | `~/.factory/memory/` | `~/.claude/memory/` |
| Plan kayıt yolları         | `~/.factory/plans/`  | `~/.claude/plans/`  |

## Lisans

MIT
