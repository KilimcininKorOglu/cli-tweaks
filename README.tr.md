# cli-tweaks

[English](README.md)

Factory Droid ve Claude Code için planlama otomasyonu, kalıcı bellek, akıllı commit ve daha fazlasını ekleyen hook, skill ve output style koleksiyonu. Ana dizininize kopyalayın, hemen çalışmaya başlasın.

## İçerik

### Hook'lar

| Hook                  | Olay                 | Açıklama                                                                                                            |
|-----------------------|----------------------|---------------------------------------------------------------------------------------------------------------------|
| `session-start.py`    | SessionStart/compact | Global kullanıcı dosyalarını ve proje belleğini bağlama enjekte eder                                                |
| `save-plan.py`        | PreToolUse           | Plan onay beklerken bildirim gönderir; Factory'de ayrıca planı diske kaydeder                                        |
| `notify-ask.py`       | PreToolUse           | Soru cevap beklerken ilk sorunun başlığıyla bildirim gönderir                                                       |
| `notify-stop.py`      | Stop/StopFailure     | Turn bittiğinde son mesajdan veya hatadan tek satırlık alıntıyla bildirim gönderir                                  |
| `memory-save.py`      | Stop                 | MEMORY.md'yi güncellemesini hatırlatır; satır sınırına yaklaşınca eski girdileri topic dosyalarına taşır ve bozuk dosyayı standart yapıya migration yapar |
| `memory-reinject.py`  | UserPromptSubmit     | Her 5. mesajda MEMORY.md kritik kurallarını, her 15. mesajda tüm global talimat dosyasını yeniden enjekte ederek bağlam kaybını önler |
| `compact-reinject.py` | SessionStart:compact | Bağlam sıkıştırmasından sonra talimat dosyalarını (argv ile) yeniden enjekte eder                                   |
| `git-protect.py`      | PreToolUse (Bash)    | Global gitignore'daki dosyalara `git add -f/--force` uygulanmasını engeller                                         |
| `notify.py`           | (yardımcı modül)     | Platformlar arası masaüstü bildirimleri (macOS, Linux, Windows)                                                     |

### Skill'ler

| Skill                          | Komut                           | Açıklama                                                                        |
|--------------------------------|---------------------------------|---------------------------------------------------------------------------------|
| `commit`                       | `/commit`                       | Repo stilini taklit eden conventional commit'ler                                |
| `task-plan`                    | `/task-plan`                    | PRD'yi özelliklere ayırma ve otonom yürütme                                     |
| `bug-report`                   | `/bug-report`                   | Genel hata analizi ve `BUG-REPORT.md` yazan odaklı audit subcommand'leri        |
| `initialize` / `init-claude`   | `/initialize`, `/init-claude`   | Kod tabanını tarayarak AGENTS.md (Factory) veya CLAUDE.md (Claude) oluşturur    |
| `redate-commits`               | `/redate-commits`               | Commit tarihlerini seçilen aralığa yayar, güvenli iş akışı uyarıları verir      |
| `frontend-design`              | `/frontend-design`              | 28 siteli tasarım kataloğu ile frontend kod üretimi                             |
| `version-update-skill-creator` | `/version-update-skill-creator` | Projeyi tarayarak versiyon güncelleme skill'i oluşturur                         |
| `ai-seo`                       | `/ai-seo`                       | AI arama motorları için GEO optimizasyonu: 7 analizlik sıralı tarama, audit ve fix modu |
| `draft-to-article`             | `/draft-to-article`             | Taslakları X Articles, LinkedIn veya Medium/Substack formatına dönüştürme       |
| `ios-uikit`                    | `/ios-uikit`                    | 20 referans belgeyle programatik UIKit geliştirme                               |
| `ios-simulator`                | `/ios-simulator`                | 22 Node.js script ile iOS simülatör otomasyonu                                  |
| `audit-replay`                 | `/audit-replay`                 | Kullanıcı eylem takibi, audit event logging ve rrweb session replay             |
| `http-cache`                   | `/http-cache`                   | ETag ve Cache-Control header'ları ile HTTP caching uygulaması                   |
| `add-log`                      | `/add-log`                      | Merkezi request, audit ve application logging ekler                             |
| `goal-prep`                    | `/goal-prep`                    | Serbest metni doğrulanabilir `/goal` tamamlanma koşuluna dönüştürür             |
| `no-ai`                        | `/no-ai`                        | Metinden yaygın AI üretimi yazı kalıplarını kaldırır                            |
| `check-golang`                 | `/check-golang`                 | Dört Go taraması (govulncheck, gosec, golangci-lint, modernize) çalıştırıp sıralı rapor üretir |
| `check-swift`                  | `/check-swift`                  | Dört Swift taraması (dependency-check, semgrep, SwiftLint, swift-format) çalıştırıp sıralı rapor üretir |
| `check-rust`                   | `/check-rust`                   | Dört Rust taraması (cargo-audit, cargo-deny, clippy, edition kontrolü) çalıştırıp sıralı rapor üretir |
| `check-js`                     | `/check-js`                     | Dört JS/TS taraması (paket audit, semgrep, ESLint, knip) çalıştırıp sıralı rapor üretir |
| `check-php`                    | `/check-php`                    | Dört PHP taraması (composer audit, Psalm taint, PHPStan, Rector) çalıştırıp sıralı rapor üretir |
| `go-time-int64`                | `/go-time-int64`                | Sıcak Go struct'larındaki `time.Time` alanlarını `int64` ile değiştirip bellek ve GC yükünü azaltır |
| `pg-fair-queue`                | `/pg-fair-queue`                | Write-time block-ID round-robin ile adil multi-tenant Postgres task queue tasarlar |
| `pg-insert-perf`               | `/pg-insert-perf`               | Buffer'lı batch veya COPY ve doğru boyutlu pool ile Postgres insert'lerini hızlandırır |

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
| `security-sweep`    | `/bug-report security-sweep`    | 24 güvenlik taramasını rolling 2-worker havuzuyla çalıştırır |
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

### Output Style'lar

Yalnızca Claude Code. Factory Droid'in output style sözleşmesi yok, bu yüzden bu ağaç `factory/` altına aynalanmaz.

| Style        | Dosya                                | Açıklama                                                                    |
|--------------|--------------------------------------|------------------------------------------------------------------------------|
| `ASD-STE100` | `claude/output-styles/ASD-STE100.md` | Basitleştirilmiş teknik İngilizce: kısa cümle, etken çatı, cümle başına tek talimat, uydurma metafor yok, hedge yok, iltifat yok, önce sonuç |

Dosyayı `~/.claude/output-styles/` altına kopyalayın, sonra `/output-style` ile seçin. Claude Code output style'ı oturum başında okur, yani bir düzenleme sonraki oturumda veya style'ı yeniden seçtiğinizde etkili olur.

## Dizin Yapısı

```
cli-tweaks/
  factory/           <-- Factory Droid (~/.factory/ içine kopyalayın)
    hooks/
    skills/
    settings.json.example
  claude/            <-- Claude Code (~/.claude/ içine kopyalayın)
    hooks/
    skills/
    output-styles/
    settings.json.example
  SOUL.md.template          <-- Özel persona şablonu
  MEMORY.template.md        <-- Canonical proje MEMORY.md yapısı
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
npx degit KilimcininKorOglu/cli-tweaks/claude/output-styles /tmp/cli-tweaks-styles
cp -r /tmp/cli-tweaks-hooks/* ~/.claude/hooks/
cp -r /tmp/cli-tweaks-skills/* ~/.claude/skills/
mkdir -p ~/.claude/output-styles && cp -r /tmp/cli-tweaks-styles/* ~/.claude/output-styles/
rm -rf /tmp/cli-tweaks-hooks /tmp/cli-tweaks-skills /tmp/cli-tweaks-styles
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
mkdir -p ~/.claude/output-styles && cp -r claude/output-styles/* ~/.claude/output-styles/
```

### Hook Kaydı

Dosyaları kopyaladıktan sonra, hook tanımlarını `settings.json` dosyanıza birleştirin:

| Platform      | Kaynak                          | Hedef                        |
|---------------|---------------------------------|------------------------------|
| Factory Droid | `factory/settings.json.example` | `~/.factory/settings.json`   |
| Claude Code   | `claude/settings.json.example`  | `~/.claude/settings.json`    |

Örnek dosyadaki `hooks` bölümünü mevcut ayarlarınıza kopyalayın veya örneği başlangıç noktası olarak kullanın.

### Seçmeli Kurulum

Yalnızca ihtiyacınız olanları seçin. Aşağıdaki örnekler `factory/` kullanır; Claude Code için `claude/` ile değiştirin.

```bash
# Yalnızca bildirim hook'ları (notify.py, ikisi için de gereklidir)
cp factory/hooks/save-plan.py ~/.factory/hooks/
cp factory/hooks/notify-ask.py ~/.factory/hooks/
cp factory/hooks/notify-stop.py ~/.factory/hooks/
cp factory/hooks/notify.py ~/.factory/hooks/

# Yalnızca bellek sistemi
cp factory/hooks/session-start.py ~/.factory/hooks/
cp factory/hooks/memory-save.py ~/.factory/hooks/

# Yalnızca commit skill'i
cp -r factory/skills/commit ~/.factory/skills/

# Yalnızca output style (sadece Claude Code)
mkdir -p ~/.claude/output-styles
cp claude/output-styles/ASD-STE100.md ~/.claude/output-styles/
```

> **Not:** `save-plan.py`, `notify-ask.py` ve `notify-stop.py`, çalışma zamanında `notify.py`'yi import eder. Hangisini kopyalarsanız kopyalayın, `notify.py`'yi de birlikte alın.

Ardından ilgili hook kayıtlarını `settings.json` dosyanıza ekleyin.

## Nasıl Çalışır

### Plan Kaydetme

Ajanın yerleşik plan modunu kullanıp çıktığınızda (`ExitPlanMode` Claude Code'da, `ExitSpecMode` Factory Droid'de), `save-plan.py` hook'u bu olayı yakalar.

Her iki platform da hook'u `PreToolUse` olayına kaydeder. Bu olay, onay istemi sizi beklemeye başlamadan **önce** çalışır. Bildirimin işe yaradığı an tam olarak budur: plan ekrandadır ve cevabınızı bekler. `PostToolUse` ise ancak siz cevap verdikten sonra çalışırdı, yani bildirim için çok geç olurdu. Bildirim proje adını gösterir, böylece birden fazla oturum açıkken hangisinin sizi beklediğini ayırt edebilirsiniz.

Hook aracı asla bloke etmez: çıkış kodu 0 verir ve stdout'a hiçbir şey yazmaz, onay istemi etkilenmez.

Factory Droid'de hook ayrıca plan içeriğini `~/.factory/plans/<proje>/` dizinine yazar. Artık onaydan önce çalıştığı için, planı onaylasanız da onaylamasanız da arşivlenir. Claude Code'da tool hook'a plan içeriği vermez, bu yüzden yalnızca bildirim gönderilir.

### Otomatik Bellek

Bellek sistemi, ajana oturumlar arası kalıcı ve projeye özel bir bellek sağlar. Bellek, ortak bir konumda (`~/.cli-tweaks/memory/`) saklanır, böylece Factory Droid ve Claude Code aynı bilgi tabanına erişebilir:

- Oturum başında `session-start.py`, `~/.cli-tweaks/memory/<proje>/MEMORY.md` dosyasını okur ve bağlama enjekte eder
- Bağlam sıkıştırmasında bellek, talimat dosyalarıyla birlikte otomatik olarak yeniden enjekte edilir
- Her 5. mesajda `memory-reinject.py`, MEMORY.md'deki kritik kuralları yeniden enjekte eder; her 15. mesajda ayrıca tüm global talimat dosyanızı (`~/.claude/CLAUDE.md` veya `~/.factory/AGENTS.md`) yeniden enjekte ederek uzun oturumlarda bağlam kaybını önler
- Oturum sonunda `memory-save.py`, ajanın yeni öğrendiklerini kaydetmesini hatırlatır, MEMORY.md 200 satır sınırına yaklaşınca eski girdileri topic dosyalarına taşımayı önerir ve dosya bozuksa standart dört bölümlü yapıya migration yapar
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
  "hookNotifyPlanSave": true,
  "hookNotifyAskUser": true,
  "hookNotifyStop": true
}
```

- `hookNotifyPlanSave`: Plan onay beklerken bildirim (varsayılan: `false`)
- `hookNotifyAskUser`: Soru cevap beklerken bildirim (varsayılan: `false`)
- `hookNotifyStop`: Turn bittiğinde veya hatayla sonlandığında bildirim (varsayılan: `false`)

Her anahtar JSON `true` olmalıdır. `"false"` metni dahil başka her değer özelliği kapalı bırakır ve stderr'e bildirilir.

## Gereksinimler

- Python 3.8+ (Factory Droid ve Claude Code hook'ları)

## Platform Farklılıkları

| Özellik                    | Factory Droid    | Claude Code       |
|----------------------------|------------------|-------------------|
| Global yapılandırma dizini | `~/.factory/`    | `~/.claude/`      |
| Ortak veri dizini          | `~/.cli-tweaks/` | `~/.cli-tweaks/`  |
| Hook yapılandırma dosyası  | `settings.json`  | `settings.json`   |
| Hook çalışma ortamı        | Python shell     | Python shell      |
| Plan modu çıkış olayı      | `ExitSpecMode`   | `ExitPlanMode`    |
| Kullanıcı soru aracı       | `AskUser`        | `AskUserQuestion` |
| Yeniden enjeksiyon hedefi  | `AGENTS.md`      | `CLAUDE.md`       |
| Skill çağırma ön eki       | `/`              | `/`               |
| Output style               | desteklenmiyor   | `~/.claude/output-styles/` |

## Lisans

MIT
