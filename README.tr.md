# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code için planlama otomasyonu, kalıcı bellek, akıllı commit ve daha fazlasını ekleyen hook ve skill koleksiyonu. Ana dizininize kopyalayın, hemen çalışmaya başlasın.

## İçerik

### Hook'lar

| Hook                  | Olay                 | Açıklama                                                                                                     |
|-----------------------|----------------------|--------------------------------------------------------------------------------------------------------------|
| `plan-mode.py`        | UserPromptSubmit     | Anahtar kelime veya karmaşıklık puanlamasıyla planlama ihtiyacını tespit eder, 5 fazlı iş akışı enjekte eder |
| `save-plan.py`        | PostToolUse          | Tamamlanan planları diske kaydeder, masaüstü bildirimi gönderir                                              |
| `memory-load.py`      | SessionStart/compact | Projeye özel belleği (MEMORY.md + konu dosyaları) bağlama yükler                                             |
| `memory-save.py`      | Stop                 | Oturum bitmeden önce ajanın öğrendiklerini kaydetmesini hatırlatır                                           |
| `compact-reinject.py` | SessionStart:compact | Bağlam sıkıştırmasından sonra AGENTS.md veya CLAUDE.md'yi yeniden enjekte eder                               |
| `global-inject.py`    | SessionStart/compact | settings.json listesindeki global kullanıcı dosyalarını (AGENTS.md, SOUL.md vb.) enjekte eder                |
| `notify.py`           | (yardımcı modül)     | Platformlar arası masaüstü bildirimleri (macOS, Linux, Windows)                                              |

### Skill'ler

| Skill                                  | Komut             | Aciklama                                                   |
|----------------------------------------|-------------------|------------------------------------------------------------|
| `commit`                               | `/commit`         | Repo stilini taklit eden conventional commit'ler           |
| `task-plan`                            | `/task-plan`      | PRD'yi ozelliklere ayirma ve otonom yurutme                |
| `bug-report`                           | `/bug-report`     | Sistematik hata analizi ve yapilandirilmis rapor olusturma |
| `dead-code`                            | `/dead-code`      | 3 fazli analiz ve temizlik yol haritasiyla olu kod denetimi|
| `git-flow`                             | `/git-flow`       | Siki dogrulama kurallariyla yapilandirilmis branch yonetimi|
| `initialize` (yalnizca Claude Code)    | `/initialize`     | Kod tabanini tarayarak AGENTS.md olusturur                 |
| `init-claude` (yalnizca Factory Droid) | `/init-claude`    | Kod tabanini tarayarak CLAUDE.md olusturur                 |
| `implement-plan`                       | `/implement-plan` | AskUser sorulariyla interaktif planlama                    |

## Dizin Yapısı

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
  SOUL.md.template   <-- Özel persona şablonu
```

## Kurulum

### Hızlı Kurulum (degit)

Tüm repoyu klonlamaya gerek yok. [degit](https://github.com/Rich-Harris/degit) yalnızca ihtiyacınız olan dosyaları kopyalar.

**Sıfırdan kurulum** (mevcut yapılandırma yok):

```bash
# Factory Droid
npx degit KilimcininKorOglu/cli-tweaks/factory ~/.factory

# Claude Code
npx degit KilimcininKorOglu/cli-tweaks/claude ~/.claude
```

**Mevcut kurulumla birleştirme**:

```bash
# Factory Droid
npx degit KilimcininKorOglu/cli-tweaks/factory/hooks /tmp/cli-tweaks-hooks
npx degit KilimcininKorOglu/cli-tweaks/factory/skills /tmp/cli-tweaks-skills
cp -r /tmp/cli-tweaks-hooks/* ~/.factory/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.factory/skills/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills

# Claude Code
npx degit KilimcininKorOglu/cli-tweaks/claude/hooks /tmp/cli-tweaks-hooks
npx degit KilimcininKorOglu/cli-tweaks/claude/skills /tmp/cli-tweaks-skills
cp -r /tmp/cli-tweaks-hooks/* ~/.claude/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.claude/skills/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills
```

### Alternatif: git clone

```bash
git clone https://github.com/KilimcininKorOglu/cli-tweaks.git
cd cli-tweaks

# Factory Droid
cp -r factory/hooks/* ~/.factory/hooks/
cp -r factory/skills/* ~/.factory/skills/

# Claude Code
cp -r claude/hooks/* ~/.claude/hooks/
cp -r claude/skills/* ~/.claude/skills/
```

### Hook Kaydı

Dosyaları kopyaladıktan sonra, hook tanımlarını `settings.json` dosyanıza birleştirin:

| Platform      | Kaynak                          | Hedef                      |
|---------------|---------------------------------|----------------------------|
| Factory Droid | `factory/settings.json.example` | `~/.factory/settings.json` |
| Claude Code   | `claude/settings.json.example`  | `~/.claude/settings.json`  |

Örnek dosyadaki `hooks` bölümünü mevcut ayarlarınıza kopyalayın veya örneği başlangıç noktası olarak kullanın.

### Seçmeli Kurulum

Yalnızca ihtiyacınız olanları seçin. Aşağıdaki örnekler `factory/` kullanır; Claude Code için `claude/` ile değiştirin.

```bash
# Yalnızca planlama hook'ları (notify.py, save-plan.py için gereklidir)
cp factory/hooks/plan-mode.py ~/.factory/hooks/
cp factory/hooks/save-plan.py ~/.factory/hooks/
cp factory/hooks/notify.py ~/.factory/hooks/

# Yalnızca bellek sistemi
cp factory/hooks/memory-load.py ~/.factory/hooks/
cp factory/hooks/memory-save.py ~/.factory/hooks/

# Yalnızca commit skill'i
cp -r factory/skills/commit ~/.factory/skills/
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
- Bağlam sıkıştırmasında bellek, talimat dosyalarıyla birlikte otomatik olarak yeniden enjekte edilir
- Oturum sonunda `memory-save.py`, ajanın yeni öğrendiklerini kaydetmesini hatırlatır
- Bellek dosyaları proje bazında ana indeks ve konu dosyalarıyla düzenlenir

### Sıkıştırma Sonrası Yeniden Enjeksiyon

Bağlam penceresi sıkıştırıldığında AGENTS.md veya CLAUDE.md talimatları ve proje belleği kaybolur. Compact hook'ları sıkıştırma olaylarını tespit eder ve hem talimat dosyalarını hem de belleği yeniden enjekte ederek bağlamınızı canlı tutar.

### Commit Skill'i

`/commit` skill'i, commit öncesi tam git bağlamını toplar (status, diff, branch, son log), reponuzun mevcut commit stilini taklit eder, git güvenlik protokolünü uygular ve `--amend`, `--wip`, `--push`, `--all` gibi bayrakları destekler.

### Özel Persona (SOUL.md)

Ajanın sizinle nasıl iletişim kurduğunu şekillendiren özel bir persona tanımlayabilirsiniz. Yapılandırma dizininizde bir `SOUL.md` dosyası oluşturun ve `settings.json`'daki `globalInjectFiles` listesine ekleyin:

```json
{
  "globalInjectFiles": [
    "~/.factory/AGENTS.md",
    "~/.factory/SOUL.md"
  ]
}
```

`global-inject.py` hook'u listelenen tüm dosyaları oturum başında ve bağlam sıkıştırmasından sonra enjekte eder. `SOUL.md.template` dosyasında örnek bir "sert sevgi" personası bulunur -- kopyalayıp kendi tercihinize göre özelleştirin.

## Gereksinimler

- Python 3.8+
- Factory Droid veya Claude Code (veya her ikisi)

## Platform Farklılıkları

| Özellik                    | Factory Droid        | Claude Code         |
|----------------------------|----------------------|---------------------|
| Plan modu çıkış olayı      | `ExitSpecMode`       | `ExitPlanMode`      |
| Yeniden enjeksiyon hedefi  | `AGENTS.md`          | `CLAUDE.md`         |
| `/init-claude` skill'i    | Evet (CLAUDE.md)     | Hayır (yerleşik)    |
| `/initialize` skill'i     | Hayır                | Evet (AGENTS.md)    |
| Bellek yolları             | `~/.factory/memory/` | `~/.claude/memory/` |
| Plan kayıt yolları         | `~/.factory/plans/`  | `~/.claude/plans/`  |

## Lisans

MIT
