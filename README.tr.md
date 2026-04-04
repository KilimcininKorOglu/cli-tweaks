# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code için planlama otomasyonu, kalıcı bellek, akıllı commit ve daha fazlasını ekleyen hook ve skill koleksiyonu. Ana dizininize kopyalayın, hemen çalışmaya başlasın.

## İçerik

### Hook'lar

| Hook                  | Olay                 | Açıklama                                                                                                         |
|-----------------------|----------------------|------------------------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Global kullanıcı dosyalarını ve proje belleğini bağlama enjekte eder                                             |
| `plan-mode.py`        | UserPromptSubmit     | Anahtar kelime veya karmaşıklık puanlamasıyla planlama ihtiyacını tespit eder, 5 fazlı iş akışı enjekte eder     |
| `save-plan.py`        | PostToolUse          | Planları diske kaydeder (Factory) veya yalnızca bildirim gönderir (Claude Code)                                  |
| `memory-save.py`      | Stop                 | Oturum bitmeden önce ajanın öğrendiklerini kaydetmesini hatırlatır                                               |
| `compact-reinject.py` | SessionStart:compact | Bağlam sıkıştırmasından sonra talimat dosyalarını (argv ile) yeniden enjekte eder                                |
| `auto-allow.py`       | PermissionRequest    | settings.json izin listesiyle eşleşen tool'ları otomatik onaylar, eşleşmeyenleri bildirir (yalnızca Claude Code) |
| `notify.py`           | (yardımcı modül)     | Platformlar arası masaüstü bildirimleri (macOS, Linux, Windows)                                                  |

### Skill'ler

| Skill                          | Komut                           | Açıklama                                                                  |
|--------------------------------|---------------------------------|---------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Repo stilini taklit eden conventional commit'ler                          |
| `task-plan`                    | `/task-plan`                    | PRD'yi özelliklere ayırma ve otonom yürütme                               |
| `bug-report`                   | `/bug-report`                   | Genel hata analizi ve `BUG-REPORT.md` yazan odaklı audit subcommand'leri |
| `git-flow`                     | `/git-flow`                     | Sıkı doğrulama kurallarıyla yapılandırılmış branch yönetimi               |
| `initialize`                   | `/initialize`                   | Kod tabanını tarayarak AGENTS.md oluşturur                                |
| `init-claude`                  | `/init-claude`                  | Kod tabanını tarayarak CLAUDE.md oluşturur                                |
| `implement-plan`               | `/implement-plan`               | Açık plan tetiklerinde ExitSpecMode-first override destekli planlama      |
| `redate-commits`               | `/redate-commits`               | Commit tarihlerini seçilen aralığa yayar, güvenli iş akışı uyarıları verir |
| `frontend-design`              | `/frontend-design`              | Özgün, prodüksiyon kalitesinde frontend arayüzleri                        |
| `version-update-skill-creator` | `/version-update-skill-creator` | Projeyi tarayarak versiyon güncelleme skill'i oluşturur                   |

#### `bug-report` audit subcommand'leri

| Alt komut | Komut | Açıklama |
|-----------|-------|----------|
| `auditcodex` | `/bug-report auditcodex` | Codex CLI ile diff tabanlı denetim ve doğrulanmış bulguların BUG-REPORT.md'ye yazılması |
| `api-audit` | `/bug-report api-audit` | API performans, dayanıklılık, sözleşme ve yaşam döngüsü denetimi |
| `cache-audit` | `/bug-report cache-audit` | Önbellek stratejisi, tutarlılık ve Redis/güvenlik denetimi |
| `disaster-recovery` | `/bug-report disaster-recovery` | Felaket kurtarma ve iş sürekliliği hazırlık denetimi |
| `error-review` | `/bug-report error-review` | Hata mesajı kalitesi, bilgi sızıntısı ve fallback denetimi |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hijyeni, rollout güvenliği ve deney denetimi |
| `integration-security` | `/bug-report integration-security` | Üçüncü taraf entegrasyon, webhook ve OAuth güvenlik denetimi |
| `observability-audit` | `/bug-report observability-audit` | Loglama, metrik, tracing ve hata ayıklanabilirlik denetimi |
| `payment-security` | `/bug-report payment-security` | Ödeme akışı ve finansal işlem güvenlik denetimi |
| `queue-audit` | `/bug-report queue-audit` | Kuyruk, worker, retry ve DLQ dayanıklılık denetimi |
| `release-discipline` | `/bug-report release-discipline` | Versiyon kontrolü, review süreci ve release discipline denetimi |
| `serialization-audit` | `/bug-report serialization-audit` | Serileştirme, parsing ve veri dönüşüm güvenlik denetimi |
| `session-audit` | `/bug-report session-audit` | Oturum yaşam döngüsü, cookie, CSRF ve state yönetimi denetimi |
| `tech-debt` | `/bug-report tech-debt` | Teknik borç haritalama ve önceliklendirme denetimi |
| `tenant-isolation` | `/bug-report tenant-isolation` | Çok kiracılı izolasyon ve tenantlar arası sızıntı denetimi |
| `test-review` | `/bug-report test-review` | Test paketi kalitesi, kapsam boşlukları ve strateji denetimi |
| `upload-security` | `/bug-report upload-security` | Dosya yükleme ve medya işleme güvenlik denetimi |
| `ai-code-audit` | `/bug-report ai-code-audit` | Yapay zeka üretimi kod tespiti, güvenlik ve kalite denetimi |
| `dead-code` | `/bug-report dead-code` | Ölü kod, kullanılmayan tanımlar ve temizlik denetimi |

> Geçiş notu: `/api-audit`, `/error-review` ve `/auditcodex` gibi bağımsız audit komutları artık `/bug-report <subcommand>` altında toplandı.

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
cp factory/hooks/session-start.py ~/.factory/hooks/
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

Bellek sistemi, ajana oturumlar arası kalıcı ve projeye özel bir bellek sağlar. Bellek, ortak bir konumda (`~/.cli-tweaks/memory/`) saklanır, böylece Factory Droid ve Claude Code aynı bilgi tabanına erişebilir:

- Oturum başında `session-start.py`, `~/.cli-tweaks/memory/<proje>/MEMORY.md` dosyasını okur ve bağlama enjekte eder
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

`session-start.py` hook'u listelenen tüm dosyaları oturum başında ve bağlam sıkıştırmasından sonra enjekte eder. `SOUL.md.template` dosyasında örnek bir "sert sevgi" personası bulunur -- kopyalayıp kendi tercihinize göre özelleştirin.

### Masaüstü Bildirimleri

Masaüstü bildirimleri `settings.json` dosyanızda özellik bazında yapılandırılır:

```json
{
  "hookNotifyAutoAllow": true,
  "hookNotifyPlanSave": true
}
```

- `hookNotifyAutoAllow`: İzin listesinde olmayan tool'lar için bildirimler (yalnızca Claude Code, varsayılan: `true`)
- `hookNotifyPlanSave`: Plan kaydedildiğinde bildirimler (varsayılan: `false`)

## Gereksinimler

- Python 3.8+ (Factory Droid, Claude Code)

## Platform Farklılıkları

| Özellik                    | Factory Droid    | Claude Code       |
|----------------------------|------------------|-------------------|
| Global yapılandırma dizini | `~/.factory/`    | `~/.claude/`      |
| Ortak veri dizini          | `~/.cli-tweaks/` | `~/.cli-tweaks/`  |
| Hook yapılandırma dosyası  | `settings.json`  | `settings.json`   |
| Plan modu çıkış olayı      | `ExitSpecMode`   | `ExitPlanMode`    |
| Kullanıcı soru aracı       | `AskUser`        | `AskUserQuestion` |
| Yeniden enjeksiyon hedefi  | `AGENTS.md`      | `CLAUDE.md`       |
| Subagent terminolojisi     | "worker"         | "Explore"         |
| Skill çağırma ön eki       | `/`              | `/`               |
| `/init-claude` skill'i     | Evet (CLAUDE.md) | Hayır (yerleşik)  |
| `/initialize` skill'i      | Hayır            | Evet (AGENTS.md)  |
| `auto-allow.py` hook'u     | Hayır            | Evet (v2.0.45+)   |

## Lisans

MIT
