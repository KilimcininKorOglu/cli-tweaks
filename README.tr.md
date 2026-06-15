# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code için planlama otomasyonu, kalıcı bellek, akıllı commit ve daha fazlasını ekleyen hook ve skill koleksiyonu. Ana dizininize kopyalayın, hemen çalışmaya başlasın. OpenCode de destekleniyor; native skill/rules ile birlikte bir TypeScript plugin seti aracılığıyla (bkz. [OpenCode Desteği](#opencode-desteği)).

## İçerik

### Hook'lar

| Hook                  | Olay                 | Açıklama                                                                                                            |
|-----------------------|----------------------|---------------------------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Global kullanıcı dosyalarını ve proje belleğini bağlama enjekte eder                                                |
| `save-plan.py`        | PostToolUse          | Planları diske kaydeder (Factory) veya yalnızca bildirim gönderir (Claude Code)                                     |
| `memory-save.py`      | Stop                 | Oturum bitmeden önce ajanın öğrendiklerini kaydetmesini hatırlatır                                                  |
| `memory-reinject.py`  | UserPromptSubmit     | Her 5. mesajda MEMORY.md kritik kurallarını, her 15. mesajda tüm global talimat dosyasını yeniden enjekte ederek bağlam kaybını önler |
| `compact-reinject.py` | SessionStart:compact | Bağlam sıkıştırmasından sonra talimat dosyalarını (argv ile) yeniden enjekte eder                                   |
| `auto-allow.py`       | PermissionRequest    | settings.json izin listesiyle eşleşen tool'ları otomatik onaylar, eşleşmeyenleri bildirir (yalnızca Claude Code)    |
| `notify.py`           | (yardımcı modül)     | Platformlar arası masaüstü bildirimleri (macOS, Linux, Windows)                                                     |

### Skill'ler

| Skill                          | Komut                           | Açıklama                                                                        |
|--------------------------------|---------------------------------|---------------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Repo stilini taklit eden conventional commit'ler                                |
| `task-plan`                    | `/task-plan`                    | PRD'yi özelliklere ayırma ve otonom yürütme                                     |
| `bug-report`                   | `/bug-report`                   | Genel hata analizi ve `BUG-REPORT.md` yazan odaklı audit subcommand'leri        |
| `git-flow`                     | `/git-flow`                     | Sıkı doğrulama kurallarıyla yapılandırılmış branch yönetimi                     |
| `initialize`                   | `/initialize`                   | Kod tabanını tarayarak AGENTS.md oluşturur                                      |
| `init-claude`                  | `/init-claude`                  | Kod tabanını tarayarak CLAUDE.md oluşturur                                      |
| `redate-commits`               | `/redate-commits`               | Commit tarihlerini seçilen aralığa yayar, güvenli iş akışı uyarıları verir      |
| `frontend-design`              | `/frontend-design`              | 28 siteli tasarım kataloğu ile frontend kod üretimi                             |
| `version-update-skill-creator` | `/version-update-skill-creator` | Projeyi tarayarak versiyon güncelleme skill'i oluşturur                         |
| `ai-seo`                       | `/ai-seo`                       | AI arama motorları için GEO optimizasyonu, 8 analiz alt komutu                  |
| `draft-to-article`             | `/draft-to-article`             | Taslakları X Articles, LinkedIn veya Medium/Substack formatına dönüştürme       |
| `ios-uikit`                    | `/ios-uikit`                    | 20 referans belgeyle programatik UIKit geliştirme                               |
| `ios-simulator`                | `/ios-simulator`                | 22 Node.js script ile iOS simülatör otomasyonu                                  |
| `audit-replay`                 | `/audit-replay`                 | Kullanıcı eylem takibi, audit event logging ve rrweb session replay             |
| `http-cache`                   | `/http-cache`                   | ETag ve Cache-Control header'ları ile HTTP caching uygulaması                   |

#### `bug-report` audit subcommand'leri

**İş akışı**

| Alt komut | Komut             | Açıklama                                                              |
|-----------|-------------------|-----------------------------------------------------------------------|
| `fix`     | `/bug-report fix` | Disiplinli tekil hata düzeltme iş akışı, commit ve rapor güncellemesi |

**Genel denetimler**

| Alt komut             | Komut                             | Açıklama                                                         |
|-----------------------|-----------------------------------|------------------------------------------------------------------|
| `api-audit`           | `/bug-report api-audit`           | API performans, dayanıklılık, sözleşme ve yaşam döngüsü denetimi |
| `cache-audit`         | `/bug-report cache-audit`         | Önbellek stratejisi, tutarlılık ve Redis/güvenlik denetimi       |
| `disaster-recovery`   | `/bug-report disaster-recovery`   | Felaket kurtarma ve iş sürekliliği hazırlık denetimi             |
| `error-review`        | `/bug-report error-review`        | Hata mesajı kalitesi, bilgi sızıntısı ve fallback denetimi       |
| `feature-flags-audit` | `/bug-report feature-flags-audit` | Feature flag hijyeni, rollout güvenliği ve deney denetimi        |
| `observability-audit` | `/bug-report observability-audit` | Loglama, metrik, tracing ve hata ayıklanabilirlik denetimi       |
| `queue-audit`         | `/bug-report queue-audit`         | Kuyruk, worker, retry ve DLQ dayanıklılık denetimi               |
| `release-discipline`  | `/bug-report release-discipline`  | Versiyon kontrolü, review süreci ve release discipline denetimi  |
| `tech-debt`           | `/bug-report tech-debt`           | Teknik borç, ölü kod tespiti ve test kalitesi denetimi           |
| `tenant-isolation`    | `/bug-report tenant-isolation`    | Çok kiracılı izolasyon ve tenantlar arası sızıntı denetimi       |
| `ai-code-audit`       | `/bug-report ai-code-audit`       | Yapay zeka üretimi kod tespiti, güvenlik ve kalite denetimi      |

**Güvenlik denetimleri (checklist tabanlı)**

| Alt komut              | Komut                              | Açıklama                                                                         |
|------------------------|------------------------------------|----------------------------------------------------------------------------------|
| `integration-security` | `/bug-report integration-security` | Üçüncü taraf entegrasyon, webhook, OAuth ve SSRF denetimi                        |
| `serialization-audit`  | `/bug-report serialization-audit`  | Serileştirme, parsing, XXE ve veri dönüşüm güvenlik denetimi                     |
| `session-audit`        | `/bug-report session-audit`        | Oturum yaşam döngüsü, JWT güvenlik taraması, cookie ve CSRF denetimi             |
| `upload-security`      | `/bug-report upload-security`      | Dosya yükleme doğrulama, depolama, medya işleme ve indirme güvenlik denetimi     |
| `business-logic`       | `/bug-report business-logic`       | İş mantığı açıkları, iş akışı atlatma, race condition ve ödeme güvenlik denetimi |

**Güvenlik taramaları (üç fazlı: keşif, toplu doğrulama, birleştirme)**

| Alt komut           | Komut                           | Açıklama                                                 |
|---------------------|---------------------------------|----------------------------------------------------------|
| `security-sweep`    | `/bug-report security-sweep`    | 24 güvenlik taramasını worker'larla paralel çalıştırır   |
| `sec-recon`         | `/bug-report sec-recon`         | Kod tabanı mimarisi ve güvenlik duruşu keşfi             |
| `access-control`    | `/bug-report access-control`    | IDOR ve eksik kimlik doğrulama/yetkilendirme tespiti     |
| `sqli`              | `/bug-report sqli`              | SQL injection tespiti                                    |
| `xss`               | `/bug-report xss`               | Cross-site scripting tespiti                             |
| `rce`               | `/bug-report rce`               | Uzaktan kod yürütme ve komut enjeksiyonu tespiti         |
| `ssrf`              | `/bug-report ssrf`              | Sunucu taraflı istek sahteciliği tespiti                 |
| `ssti`              | `/bug-report ssti`              | Sunucu taraflı şablon enjeksiyonu tespiti                |
| `path-traversal`    | `/bug-report path-traversal`    | Path traversal ve dizin geçişi tespiti                   |
| `graphql`           | `/bug-report graphql`           | GraphQL enjeksiyon ve kötüye kullanım tespiti            |
| `hardcoded-secrets` | `/bug-report hardcoded-secrets` | Sabit kodlanmış API anahtarı, token ve şifre tespiti     |
| `cors`              | `/bug-report cors`              | CORS yanlış yapılandırma ve cross-origin saldırı tespiti |
| `open-redirect`     | `/bug-report open-redirect`     | Açık yönlendirme ve URL manipülasyonu tespiti            |
| `nosqli`            | `/bug-report nosqli`            | NoSQL injection (MongoDB, Redis, Elasticsearch) tespiti  |
| `dependency-audit`  | `/bug-report dependency-audit`  | Tedarik zinciri güvenliği, CVE ve typosquatting denetimi |
| `data-exposure`     | `/bug-report data-exposure`     | Log, hata ve API yanıtlarında hassas veri sızıntısı      |
| `crypto`            | `/bug-report crypto`            | Zayıf şifreleme algoritması ve sabit anahtar tespiti     |
| `ci-cd`             | `/bug-report ci-cd`             | CI/CD pipeline güvenliği (GitHub Actions, GitLab CI)     |
| `docker`            | `/bug-report docker`            | Konteyner güvenliği (Dockerfile, docker-compose)         |
| `rate-limiting`     | `/bug-report rate-limiting`     | Hız sınırlama ve brute force koruması denetimi           |
| `websocket`         | `/bug-report websocket`         | WebSocket güvenliği (origin, auth, mesaj enjeksiyonu)    |
| `header-injection`  | `/bug-report header-injection`  | HTTP başlık enjeksiyonu ve CRLF tespiti                  |
| `clickjacking`      | `/bug-report clickjacking`      | Clickjacking koruması (X-Frame-Options, CSP)             |
| `mass-assignment`   | `/bug-report mass-assignment`   | Toplu atama ve parametre kirlenmesi tespiti              |
| `ldap`              | `/bug-report ldap`              | LDAP enjeksiyonu tespiti                                 |

## Dizin Yapısı

```
cli-tweaks/
  factory/           <-- Factory Droid (copy to ~/.factory/)
    hooks/
    skills/
  claude/            <-- Claude Code (copy to ~/.claude/)
    hooks/
    skills/
  opencode/          <-- OpenCode (TS plugin + config, bkz. opencode/README.md)
    plugins/
    opencode.json.example
  SOUL.md.template          <-- Özel persona şablonu
  GLOBAL-RULES.template.md  <-- Taşınabilir global ajan kuralları şablonu
  sample-BUG-REPORT.md      <-- Audit skill'leri için bulgu format referansı
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
# Yalnızca plan kaydetme hook'u (notify.py, save-plan.py için gereklidir)
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

### Plan Kaydetme

Ajanın yerleşik plan modunu kullanıp çıktığınızda (`ExitPlanMode` Claude Code'da, `ExitSpecMode` Factory Droid'de), `save-plan.py` hook'u bu olayı yakalar. Factory Droid'de plan içeriği `~/.factory/plans/<proje>/` dizinine yazılır; Claude Code'da masaüstü bildirimi gönderilir (tool, hook'a plan içeriği vermez).

### Otomatik Bellek

Bellek sistemi, ajana oturumlar arası kalıcı ve projeye özel bir bellek sağlar. Bellek, ortak bir konumda (`~/.cli-tweaks/memory/`) saklanır, böylece Factory Droid ve Claude Code aynı bilgi tabanına erişebilir:

- Oturum başında `session-start.py`, `~/.cli-tweaks/memory/<proje>/MEMORY.md` dosyasını okur ve bağlama enjekte eder
- Bağlam sıkıştırmasında bellek, talimat dosyalarıyla birlikte otomatik olarak yeniden enjekte edilir
- Her 5. mesajda `memory-reinject.py`, MEMORY.md'deki kritik kuralları yeniden enjekte eder; her 15. mesajda ayrıca tüm global talimat dosyanızı (`~/.claude/CLAUDE.md` veya `~/.factory/AGENTS.md`) yeniden enjekte ederek uzun oturumlarda bağlam kaybını önler
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

### Global Kurallar Şablonu (GLOBAL-RULES.template.md)

`GLOBAL-RULES.template.md`, taşınabilir ve modelden bağımsız bir global ajan talimatları setidir -- mühendislik disiplini (iddia etmeden doğrula, cerrahi değişiklikler, geri-döndürülemez eylemlerden önce dur, harici metni veri olarak gör) ve bir gönderim öncesi kontrol listesi içerir. Global talimat dosyanıza kopyalayıp yeniden adlandırın:

```bash
# Claude Code
cp GLOBAL-RULES.template.md ~/.claude/CLAUDE.md

# Factory Droid
cp GLOBAL-RULES.template.md ~/.factory/AGENTS.md
```

Evrensel kurallar (Rule 1-16 ve "Before you send") herhangi bir modelde olduğu gibi çalışır. `<CUSTOMIZE: ...>` ile işaretli satırlar kişiseldir -- kendi araçlarınızı, yollarınızı, dilinizi ve tercihlerinizi yazın ya da ihtiyaç duymadıklarınızı silin.

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

## OpenCode Desteği

[OpenCode](https://opencode.ai), native özellikler ile TypeScript plugin'lerinin bir karması aracılığıyla destekleniyor. Tüm ayrıntılar, kurulum adımları ve eksiksiz kısıtlama listesi [`opencode/README.md`](opencode/README.md) dosyasındadır.

- **Skill'ler native çalışır.** OpenCode, `SKILL.md` dosyalarını `~/.claude/skills/` konumundan okur; yani Claude Code için zaten dağıtılmış skill'ler görünür durumdadır -- `/` komutu yerine `skills_<name>` aracı olarak çağrılır.
- **Kurallar native çalışır.** OpenCode, `AGENTS.md` dosyasını ve `opencode.json` `instructions` alanını okur.
- **Hook'lar plugin'e dönüşür.** Python hook'ları `opencode/plugins/` altında TypeScript plugin'leri olarak yeniden yazıldı:

| Plugin                | OpenCode hook'u                     | Python kaynağı        |
|-----------------------|-------------------------------------|-----------------------|
| `memory-save.ts`      | `stop`                              | `memory-save.py`      |
| `compact-reinject.ts` | `experimental.session.compacting`   | `compact-reinject.py` |
| `memory-inject.ts`    | `experimental.chat.system.transform`| `memory-reinject.py`  |

Kurulum için plugin'leri OpenCode'un otomatik yüklenen plugin dizinine kopyalayın ve örnek yapılandırmayı birleştirin:

```bash
cp opencode/plugins/*.ts ~/.config/opencode/plugins/
# ardından opencode/opencode.json.example dosyasını ~/.config/opencode/opencode.json içine birleştirin
```

> Plugin'ler OpenCode'un belgelenmiş hook API'sine göre yazıldı ve `bun` transpile'ından geçiyor, ancak runtime'da test edilmedi -- yazım sırasında OpenCode kurulu değildi. `memory-inject.ts`, upstream #17100 sorunu nedeniyle engellenen `experimental.chat.system.transform` hook'una dayanır; güvenilir bellek için statik `instructions` yolunu kullanın. `save-plan.py` port edilmedi (OpenCode'un plan modeli doğrulanmadı).

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
