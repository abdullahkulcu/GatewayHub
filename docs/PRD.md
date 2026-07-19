# GatewayHub — Ürün Gereksinim Dokümanı (PRD)

> Çalışma adı: **GatewayHub** (nihai isim sonra planlanacak). Sürüm: v0.2 — 19 Temmuz 2026
> Durum: Açık sorular karara bağlandı (bkz. Bölüm 10 — Karar Günlüğü). Faz 0 başlamaya hazır.

---

## 1. Vizyon

Developer'lar çalıştıkları şirketin task management aracını seçemez; ClickUp, Jira gibi araçlar yönetim kararıyla gelir ve developer bu araçların UX kısıtlarıyla yaşamak zorunda kalır. GatewayHub bu araçların **yerine geçmez** — üzerlerine kurulan, developer'ın kendi kontrolünde, self-hosted bir **görünüm katmanıdır (lens)**. Kaynak sistemdeki veriyi kendi canonical modeline çeker, developer'ın istediği şekilde sunar ve yapılan değişiklikleri kaynak sisteme geri yazar.

Superhuman'ın Gmail'e yaptığını, GatewayHub ClickUp/Jira'ya yapar: altındaki sistemi değiştirmeden deneyimi değiştirir.

## 2. Ürün İlkeleri

Bu ilkeler her tasarım kararında bağlayıcıdır; bir özellik bu ilkelerle çelişiyorsa özellik kaybeder.

1. **Lens, replacement değil.** Kaynak sistem (ClickUp/Jira) her zaman source of truth'tur. Çakışma ve şüphe durumunda kaynak sistem kazanır.
2. **Provider-agnostic core.** Çekirdek kod hiçbir yerde ClickUp'a özel mantık içermez; tüm provider'a özgü davranış `TaskProvider` adapter'ının arkasındadır.
3. **Flat canonical model.** Sistemde "subtask" diye ayrı bir varlık yoktur; her şey task'tır, hiyerarşi sadece bir `parent_id` referansıdır. Görünüm katmanı hiyerarşiyi istediği gibi yorumlar.
4. **Local-first hız.** UI hiçbir zaman kaynak sistemin API'sini beklemez. Okuma local store'dan, yazma optimistic + arka planda queue ile.
5. **Kaybolmayan yazma.** Kullanıcının yaptığı hiçbir değişiklik sessizce kaybolmaz; write-back başarısızsa görünür şekilde işaretlenir ve yeniden denenebilir.
6. **Tek komutla ayağa kalkma.** `docker compose up` + API token = çalışan sistem. Kurulum dokümanı bir ekran boyunu geçmez.
7. **AI süs, sync çekirdek.** AI özellikleri sync güvenilirliğinin üzerine gelir; hiçbir AI özelliği sync garantilerini zayıflatamaz.

## 3. Hedefler ve Hedef Olmayanlar

**Hedefler:** Abdullah'ın (ve benzer profildeki developer'ların) günlük ClickUp acısını çözmek; open source topluluğun kolayca adapter yazabileceği bir çekirdek sunmak; keyboard-first, hızlı bir günlük çalışma paneli olmak.

**Hedef olmayanlar (non-goals):**
- SaaS olarak satılmak, multi-tenant altyapı, billing, org yönetimi.
- Kaynak sistemin tüm özelliklerini birebir kopyalamak (ör. ClickUp Goals, Whiteboards, Docs kapsam dışı).
- Standalone task management aracı olmak (provider bağlantısı olmadan çalışma modu yok — en azından v1'de).
- Mobil uygulama.
- Gerçek zamanlı çok kullanıcılı collaboration (aynı anda aynı task'ı düzenleyen iki GatewayHub kullanıcısı senaryosu v1'de optimize edilmez).

## 4. Hedef Kullanıcı ve Senaryolar

**Birincil kullanıcı:** Şirketinin task aracını değiştiremeyen ama kendi görünümünü kontrol etmek isteyen developer. Self-hosted kuracak teknik yetkinliğe sahip.

**İkincil kullanıcı:** Küçük ekip lead'i — ekibi için tek instance kurup 3-10 kişiyle kullanır.

Temel senaryolar:

- **S1 — Sabah rutini:** Kullanıcı paneli açar, "bana atanmış, aktif sprint'teki tüm tasklar ve subtasklar" görünümünü flat liste olarak görür. ClickUp'ta bu görünüm subtasklar parent'a gömülü olduğu için mümkün değildir.
- **S2 — Board'da subtask:** Kullanıcı board görünümünde bir subtask'ı bağımsız kart olarak görür, "In Progress" kolonuna sürükler; değişiklik saniyeler içinde ClickUp'a yansır.
- **S3 — Hızlı triage:** Kullanıcı klavyeyle (j/k gezinme, tek tuş status/assignee değişimi) 20 task'ı 2 dakikada triage eder.
- **S4 — Çevrimdışı kaynak:** ClickUp down veya rate-limited iken kullanıcı okumaya devam eder; yazdıkları queue'da bekler, ClickUp dönünce akar.
- **S5 (Faz 3) — Parse to subtask:** Kullanıcı bir araştırma taskının sonucunu yapıştırır, "subtasklara böl" der; AI geçmiş taskların konvansiyonuna uygun subtask önerileri üretir, kullanıcı onaylar, tasklar ClickUp'a yazılır.

## 5. Fonksiyonel Gereksinimler

Numaralandırma: `FR-<alan>-<no>`. Öncelik: M (Must), S (Should), C (Could) — faz bazında yeniden yorumlanır.

### 5.1 Sync (okuma yönü)

- **FR-SYNC-1 (M):** Sistem, yapılandırılmış provider'dan (Faz 0: ClickUp) seçili workspace/space/list kapsamındaki taskları, subtaskları, statüleri, assignee'leri, tag'leri, öncelikleri, due date'leri ve yorumları çeker ve canonical modele yazar.
- **FR-SYNC-2 (M):** İlk kurulum sonrası tam senkronizasyon (backfill) yapılır; sonrasında artımlı sync çalışır.
- **FR-SYNC-3 (M):** Birincil sync mekanizması periyodik poll'dur (aralık panelden yapılandırılabilir, varsayılan: 1 dk). Webhook desteği opsiyoneldir ve Faz 2+'da hızlandırıcı olarak eklenir; webhook ve poll aynı idempotent upsert yolunu kullanır. Poll-first tercihi bilinçlidir: self-hosted kurulumda public endpoint zorunluluğu yaratmaz.
- **FR-SYNC-4 (M):** Provider rate limit'leri token-bucket ile yönetilir; limit aşımında sync yavaşlar, asla hata ile durmaz.
- **FR-SYNC-5 (S):** Sync durumu UI'da görünürdür: son başarılı sync zamanı, bekleyen değişiklik sayısı, hata durumu.
- **FR-SYNC-6 (C):** Silinen taskların tespiti (poll sırasında diff) ve soft-delete olarak işaretlenmesi.

### 5.2 Canonical Model

- **FR-MODEL-1 (M):** Tüm iş öğeleri tek `task` varlığında tutulur. `parent_id` opsiyonel bir referanstır; subtask ayrı bir tür değildir.
- **FR-MODEL-2 (M):** Her task, provider kimliğini (`provider`, `provider_task_id`) ve sync meta verisini (`last_synced_at`, `provider_updated_at`, `sync_version`) taşır.
- **FR-MODEL-3 (M):** Provider'a özgü, canonical modele haritalanamayan alanlar `provider_raw` (JSONB) alanında saklanır — veri kaybı olmaz, gerekirse ileride haritalanır.
- **FR-MODEL-4 (S):** Statüler provider'dan dinamik alınır; canonical model statüleri sabit bir enum'a zorlamaz, ancak opsiyonel bir kategori haritası sunar (todo / in_progress / done / cancelled).

### 5.3 Görünüm ve UX

- **FR-UI-1 (M):** Liste görünümü — filtrelenebilir (assignee, statü, tag, liste, parent var/yok), sıralanabilir flat task listesi. Subtasklar bağımsız satır olarak listelenebilir.
- **FR-UI-2 (M):** Board görünümü — statü kolonlu kanban; subtasklar bağımsız kart olarak gösterilebilir (aç/kapa toggle). Kart üzerinde parent task'a küçük referans rozeti bulunur.
- **FR-UI-3 (M):** Keyboard-first navigasyon: gezinme, seçim, statü değişimi, assignee değişimi, hızlı arama (command palette, `Cmd/Ctrl+K`) klavyeyle yapılabilir.
- **FR-UI-4 (M):** Task detay paneli: açıklama (markdown render), yorumlar, subtask listesi, aktivite meta verisi.
- **FR-UI-5 (S):** Kaydedilebilir görünümler ("Benim sprint'im", "Review bekleyenler" gibi filtre setleri).
- **FR-UI-6 (S):** Sync durumu rozetleri: task bazında "yazma bekliyor / yazma başarısız / senkron" göstergesi.
- **FR-UI-7 (C):** Koyu/açık tema, yoğunluk ayarı.

### 5.4 Write-back (yazma yönü)

- **FR-WB-1 (M):** Desteklenen alan değişiklikleri provider'a geri yazılır. Faz 1 kapsamı: statü, assignee, öncelik, due date, task adı, yorum ekleme.
- **FR-WB-2 (M):** Yazmalar optimistic uygulanır: local store anında güncellenir, değişiklik outbound queue'ya girer, worker provider'a yazar.
- **FR-WB-3 (M):** Her outbound yazma idempotency key taşır; tekrar denemeler duplicate etki yaratmaz.
- **FR-WB-4 (M):** Yazma başarısızsa: exponential backoff ile N deneme; kalıcı başarısızlıkta task UI'da "yazılamadı" işaretlenir ve kullanıcı tek tıkla yeniden deneyebilir veya local değişikliği geri alabilir.
- **FR-WB-5 (M):** Çakışma kuralı: alan bazında karşılaştırma; kullanıcının yazması queue'dayken provider'dan aynı alana daha yeni bir değişiklik geldiyse provider kazanır, kullanıcıya "üzerine yazıldı" bildirimi gösterilir. (İlke 1.)
- **FR-WB-6 (S):** Yeni task/subtask oluşturma (Faz 1 sonu veya Faz 2).
- **FR-WB-7 (C):** Task taşıma (liste/board arası), tag ekleme/çıkarma.

### 5.5 Provider Soyutlaması

- **FR-PROV-1 (M):** `TaskProvider` interface'i tanımlıdır: `backfill()`, `fetch_changes(since)`, `parse_webhook(payload)`, `push_change(change)`, `capabilities()`.
- **FR-PROV-2 (M):** `capabilities()` provider'ın neleri desteklediğini bildirir (ör. `supports_subtask_independent_status`, `supports_multiple_assignees`, `max_rate`); core ve UI, desteklenmeyen aksiyonları bu bilgiye göre gizler/devre dışı bırakır.
- **FR-PROV-3 (M):** Faz 0-1'de tek somut adapter: ClickUp. Interface, ikinci adapter (Jira) yazılabilecek netlikte dokümante edilir.
- **FR-PROV-4 (S):** Adapter geliştirici rehberi (`CONTRIBUTING-ADAPTERS.md`) ve adapter conformance test suite'i.

### 5.6 AI Özellikleri (Faz 3)

- **FR-AI-1 (M/Faz3):** Parse-to-subtask: kullanıcının verdiği serbest metin (araştırma çıktısı, toplantı notu), geçmiş tasklardan RAG ile çekilen konvansiyon örnekleri eşliğinde LLM'e verilir; yapılandırılmış subtask önerileri döner.
- **FR-AI-2 (M/Faz3):** AI hiçbir zaman doğrudan yazmaz — tüm öneriler kullanıcı onayından (approval gate) geçer, onaylananlar normal write-back yolunu kullanır. (`ai-research-kb`'deki approval gate deseniyle aynı.)
- **FR-AI-3 (S/Faz3):** Geçmiş tasklar embed edilir; benzer task arama ("bu daha önce yapıldı mı?") özelliği sunulur.
- **FR-AI-4 (C/Faz3):** Task açıklaması iyileştirme / şablona oturtma önerisi.
- **FR-AI-5 (M/Faz3):** LLM sağlayıcısı yapılandırılabilir (Anthropic API varsayılan); API anahtarı kullanıcınındır, self-hosted kurulumda dışarı veri sızmaz (RAG store local).

### 5.7 Ayarlar ve Yönetim Paneli (Settings)

Tüm sistem yapılandırması panelden görülebilir ve yönetilebilir olmalıdır. `.env` yalnızca **statik/bootstrap** değerler içerir: DB bağlantısı, Redis bağlantısı, uygulama secret key'i, port ve varsayılan admin bilgileri. Provider (ClickUp/Jira) bağlantı bilgileri **hiçbir zaman** `.env`'de tutulmaz; yalnızca panelden girilir, veritabanında şifreli saklanır.

- **FR-SET-0 (M):** Varsayılan admin: ilk boot'ta `.env`'deki `ADMIN_EMAIL` / `ADMIN_PASSWORD` (varsayılan: `admin@local` / `changeme`) ile bir admin kullanıcısı oluşturulur; ilk girişte parola değişikliği zorunludur.

- **FR-SET-1 (M):** Panelde bir Settings alanı bulunur: provider bağlantıları (token ekleme/test etme/yenileme), sync ayarları (poll aralığı, kapsam: hangi workspace/space/list'ler senkronlanacak), UI tercihleri.
- **FR-SET-2 (M):** Ayar değişiklikleri restart gerektirmez; worker ayarları sıcak okur (ör. poll aralığı değişince bir sonraki döngüde uygulanır).
- **FR-SET-3 (M):** Kullanıcı yönetimi panelden yapılır: kullanıcı ekleme/çıkarma, parola sıfırlama. İlk sürümde rol modeli basittir: `admin` (settings + kullanıcı yönetimi) ve `member` (task görünümleri ve yazma).
- **FR-SET-4 (M):** Sync ve queue durumu Settings altında görünürdür: son poll zamanı, sıradaki poll, bekleyen/başarısız yazma sayısı, provider rate limit durumu; başarısız yazmalar buradan topluca yeniden denenebilir.
- **FR-SET-5 (S):** Ayarların export/import'u (JSON) — instance taşıma ve yedekleme kolaylığı.
- **FR-SET-6 (S):** Kullanıcı bazlı tercihler (tema, varsayılan görünüm, klavye düzeni) sistem ayarlarından ayrı tutulur.
- **FR-SET-7 (C):** Audit log: settings ve kullanıcı yönetimi değişikliklerinin kim/ne zaman kaydı.

### 5.8 Extension / Plugin Sistemi (Faz 4 — vizyon)

- **FR-EXT-1:** Core immutable'dır (imzalı/sabit image); genişletmeler sandboxed plugin SDK üzerinden çalışır.
- **FR-EXT-2:** Plugin'ler permission modeli ile sınırlıdır (hangi veriye okuma/yazma, hangi UI alanına ekleme).
- **FR-EXT-3:** AI destekli plugin geliştirme akışı: Claude Code benzeri bir ajan yalnızca plugin dizininde kod üretebilir; koruma MD konvansiyonuyla değil, dosya sistemi izolasyonu + process sandbox + code review gate ile sağlanır.
- Bu faz bilinçli olarak detaylandırılmamıştır; Faz 3 tamamlanmadan tasarımına başlanmaz.

## 6. Fonksiyonel Olmayan Gereksinimler

- **NFR-1 Performans:** Liste/board görünümleri local store'dan beslenir; 5.000 task'lık workspace'te görünüm açılışı < 500 ms, filtre değişimi < 200 ms hedeflenir.
- **NFR-2 Güvenilirlik:** Write-back queue kalıcıdır (restart'ta kaybolmaz). Poll-first modelde tutarlılık garantisi poll aralığıdır; webhook eklendiğinde (Faz 2+) poll, webhook kaçaklarını kapatan reconciliation görevi görür.
- **NFR-3 Deployment:** Docker Compose ile tek komut kurulum; bileşenler: app (API+UI), worker, Postgres, Redis. Yapılandırma `.env` üzerinden.
- **NFR-4 Güvenlik:** Provider token'ları veritabanında şifreli (at-rest encryption, uygulama anahtarı env'den) saklanır ve asla loglanmaz. Sistem baştan çoklu kullanıcıdır: kullanıcı/parola auth (bcrypt/argon2), session veya JWT; ilk admin bootstrap'te oluşturulur, sonraki kullanıcılar panelden eklenir (FR-SET-3). Webhook eklendiğinde (Faz 2+) endpoint imza doğrulaması yapar.
- **NFR-5 Gözlemlenebilirlik:** Yapılandırılmış loglar; sync ve queue metrikleri (bekleyen/başarısız yazma sayısı) basit bir status endpoint'inden okunabilir.
- **NFR-6 Lisans ve dağıtım:** MIT lisansı. GitHub'da public repo, sürümleme SemVer, imajlar GHCR'de.
- **NFR-7 Veri sahipliği:** Tüm cache/canonical veri kullanıcının kendi Postgres'indedir; telemetri yoktur (opt-in bile v1'de yok — sıfır arama eve).

## 7. Mimari Özet

```
                    ┌────────────────────────────┐
                    │        Web UI (React)       │
                    │  liste / board / detay /    │
                    │  command palette            │
                    └────────────┬───────────────┘
                                 │ REST/WS (local, hızlı)
                    ┌────────────▼───────────────┐
                    │        App Service          │
                    │  API + auth + görünümler    │
                    └──────┬──────────────┬──────┘
                           │              │
                 ┌─────────▼───┐   ┌──────▼─────────┐
                 │  Postgres   │   │ Redis / Queue   │
                 │ canonical   │   │ outbound writes │
                 │ store       │   │ (idempotent)    │
                 └─────────▲───┘   └──────┬─────────┘
                           │              │
                    ┌──────┴──────────────▼──────┐
                    │        Sync Worker          │
                    │  poll scheduler (+webhook,  │
                    │  Faz 2+ ops.) +             │
                    │  write-back dispatcher      │
                    └────────────┬───────────────┘
                                 │ TaskProvider interface
                    ┌────────────▼───────────────┐
                    │   ClickUp Adapter (Faz 0)   │
                    │   Jira Adapter (Faz 2)      │
                    └────────────────────────────┘
```

Veri akışı kuralları: UI yalnızca App Service ile konuşur; provider API'sine hiçbir zaman UI'dan doğrudan istek gitmez. Tüm provider trafiği Sync Worker üzerinden ve adapter'ın içinden geçer.

### Canonical model taslağı (tasks tablosu, özet)

| Alan | Tip | Not |
|---|---|---|
| id | uuid | GatewayHub kimliği |
| provider | text | `clickup`, `jira`... |
| provider_task_id | text | unique(provider, provider_task_id) |
| parent_id | uuid null | hiyerarşi sadece referans |
| title, description | text | description markdown |
| status | text | provider'dan dinamik |
| status_category | enum | todo/in_progress/done/cancelled (haritalı) |
| assignees | uuid[] | users tablosuna |
| priority, due_date, tags | — | nullable |
| provider_raw | jsonb | haritalanamayan her şey |
| provider_updated_at, last_synced_at, sync_version | timestamptz/int | çakışma çözümü için |
| write_state | enum | synced / pending / failed |

## 8. Fazlar

### Faz 0 — Read-only Lens (hedef: 2-3 hafta yarı zamanlı)

Amaç: "Evet, ben bunu istiyordum" hissinin doğrulanması. Kapsam: ClickUp adapter (yalnızca okuma: backfill + poll, webhook yok), yorumların okunması dahil; canonical model + Postgres; çoklu kullanıcı auth (bootstrap admin + panelden kullanıcı ekleme, FR-SET-3); liste ve board görünümleri; subtaskların bağımsız render'ı; temel filtreler; keyboard gezinme; Settings temel sayfası (provider token, sync kapsamı, poll aralığı — FR-SET-1); Docker Compose kurulumu.
**Kapsam dışı:** her türlü yazma (provider'a), AI, webhook.
**Başarı kriteri:** Abdullah bir hafta boyunca günlük task takibini ClickUp arayüzü yerine GatewayHub'tan yapıyor (yazma gerektiğinde ClickUp'a geçmek serbest), en az bir teammate ikinci kullanıcı olarak eklenip kendi görünümünü kullanabiliyor ve S1/S2'nin okuma tarafı sorunsuz.

### Faz 1 — Write-back (hedef: +3-4 hafta)

Kapsam: outbound queue + idempotency, optimistic UI, statü/assignee/öncelik/due date/başlık yazma, yorum ekleme, çakışma kuralı (FR-WB-5), sync durum rozetleri, UI canlı güncelleme (WebSocket yerine basit polling: panel local API'yi 1 dk aralıkla yeniler — aralık Settings'ten yapılandırılabilir), Settings'in tamamlanması (FR-SET-2/4), task oluşturma (faz sonunda). Webhook bu fazda yok; Faz 2+'da hızlandırıcı olarak değerlendirilir.
**Başarı kriteri:** İki hafta boyunca ClickUp arayüzünü açmadan günlük iş yürütülebiliyor; hiçbir değişiklik sessizce kaybolmadı; "yazılamadı" durumları görünür ve kurtarılabilir.

### Faz 2 — Provider Soyutlaması + Topluluk (hedef: +3 hafta)

Kapsam: `TaskProvider` interface'inin sertleştirilmesi, capabilities mekanizması, adapter conformance test suite, adapter geliştirici dokümanı, Jira adapter'ının en azından read-only ilk sürümü (interface'in gerçekten provider-agnostic olduğunun kanıtı), README/dokümantasyon/ekran görüntüleriyle public duyuru (Show HN, r/selfhosted).
**Başarı kriteri:** Jira read-only adapter core'da tek satır değişiklik gerektirmeden çalışıyor; dışarıdan en az bir kişi kendi instance'ını kurabildi.

### Faz 3 — AI Katmanı (hedef: +4 hafta)

Kapsam: task embed pipeline'ı + local vektör arama, parse-to-subtask (RAG + approval gate), benzer task arama, yapılandırılabilir LLM sağlayıcısı.
**Başarı kriteri:** Gerçek bir araştırma taskı, parse-to-subtask ile ekip konvansiyonuna uygun subtasklara bölünüp onay sonrası ClickUp'a yazıldı; öneri kalitesi "elle yazmaktan hızlı" eşiğini geçiyor.

### Faz 4 — Plugin/Extension Sistemi (vizyon, tarihsiz)

Sandboxed plugin SDK, permission modeli, AI destekli plugin geliştirme akışı. Faz 3 bitmeden tasarım başlamaz; bu PRD'de yalnızca yön olarak yer alır.

## 9. Riskler

| Risk | Etki | Azaltma |
|---|---|---|
| ClickUp API/ToS değişikliği, rate limit sıkılaşması | Yüksek | Provider-agnostic core; reconciliation poll aralığı yapılandırılabilir; ToS'un kurulum öncesi gözden geçirilmesi |
| Two-way sync'te veri kaybı → güven kaybı | Yüksek | İlke 1 ve 5; FR-WB-4/5; kalıcı queue; kapsamlı adapter testleri |
| Webhook güvenilmezliği | Orta | Poll ile reconciliation (FR-SYNC-3) — webhook hızlandırıcı, poll garanti |
| Kapsam şişmesi (AI/plugin hevesi) | Yüksek | Faz disiplini: Faz 0-1 bitmeden AI koduna başlanmaz |
| Tek geliştirici tükenmişliği | Orta | Fazların küçük ve tek başına değerli olması; Faz 0 tek başına bile kullanışlı |
| Provider model uyumsuzlukları (statü setleri, çoklu assignee vs.) | Orta | `capabilities()` + `provider_raw` ile kayıpsız saklama |

## 10. Karar Günlüğü

| # | Konu | Karar | Tarih |
|---|---|---|---|
| 1 | İsim | Çalışma adı **GatewayHub**; nihai isim ileride planlanacak. Not: Connexease'in "Gateway" ürünüyle isim çakışması riski open source duyurusundan önce değerlendirilmeli. | 19.07.2026 |
| 2 | Backend | **Python (FastAPI)** + **React panel**. Performans darboğazında worker Go'ya taşınabilir. | 19.07.2026 |
| 3 | Faz 0'da yorumlar | **Dahil** — okuma tarafında yorumlar Faz 0 kapsamında. | 19.07.2026 |
| 4 | Ekip modu | **Baştan çoklu kullanıcı** — bootstrap admin + panelden kullanıcı yönetimi (FR-SET-3), basit admin/member rolleri. | 19.07.2026 |
| 5 | Sync mekanizması | **Poll-first** — webhook yok (Faz 2+'da opsiyonel hızlandırıcı). Tüm sync ayarları panelden yönetilir; sağlam Settings yapısı birinci sınıf gereksinim (Bölüm 5.7). | 19.07.2026 |
| 6 | Realtime UI | **Polling** — panel 1 dk aralıkla yeniler (Settings'ten yapılandırılabilir); WebSocket v1'de yok. | 19.07.2026 |
