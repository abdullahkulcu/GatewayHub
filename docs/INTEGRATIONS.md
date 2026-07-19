# Entegrasyonlar

GatewayHub, kaynak sistemdeki veriyi kendi canonical modeline çeker. Faz 0'da
tek somut adapter **ClickUp**'tır (yalnızca okuma: backfill + poll). **Jira
adapter'ı Faz 2'ye kadar mevcut değildir** — bu bölümde Jira için adım
yoktur, çünkü henüz yazılmamıştır (bkz. `docs/PRD.md` Bölüm 8).

## ClickUp

### 1. Personal API Token alın

1. ClickUp'ta sağ üstteki avatarınıza tıklayın → **Settings**.
2. Sol menüden **Apps** sekmesine gidin.
3. **API Token** bölümünde **Generate** (veya mevcut token'ı **Copy**)
   butonuna tıklayın. Token `pk_` ile başlar.

Bu token kişisel hesabınızın tüm yetkilerini taşır; GatewayHub'a sadece
okuma amacıyla gireceğiniz için paylaşılan/production bir hesap yerine
kendi hesabınızın token'ını kullanmanız önerilir.

### 2. Token'ı GatewayHub'a girin

Token panelden (Settings) girilir, `.env`'e **asla** yazılmaz — bkz.
`GOAL.md` yapılandırma kuralları. Panelin Settings sayfası henüz
uygulanmadıysa (bu iş `PROGRESS.md`'de T25), aynı işlemi doğrudan API
üzerinden yapabilirsiniz:

```bash
TOKEN="$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@local","password":"<parolanız>"}' | jq -r .access_token)"

curl -s -X PUT http://localhost:8000/api/settings/clickup-token \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"token":"pk_..."}'
```

Token, ClickUp'a gerçekten doğrulanmadan (`GET /team` çağrısı) kabul
edilmez; geçersizse `422` döner. Kabul edildikten sonra API yanıtlarında
her zaman maskeli görünür (`pk_****`) — veritabanında Fernet ile şifreli
saklanır, hiçbir zaman loglanmaz.

### 3. Senkronize edilecek workspace/list'leri seçin

Hangi workspace ve list'lerin senkronize edileceğini keşfetmek için:

```bash
# Erişebildiğiniz workspace'ler (ClickUp'ta "Team" denir)
curl -s http://localhost:8000/api/settings/clickup/workspaces \
  -H "Authorization: Bearer $TOKEN"

# Bir workspace'teki tüm list'ler (klasörlü + klasörsüz, düz liste)
curl -s http://localhost:8000/api/settings/clickup/workspaces/<workspace_id>/lists \
  -H "Authorization: Bearer $TOKEN"
```

Seçtiğiniz list ID'lerini kapsam olarak kaydedin:

```bash
curl -s -X PUT http://localhost:8000/api/settings/sync-scope \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"workspace_id":"<workspace_id>","list_ids":["<list_id_1>","<list_id_2>"]}'
```

### 4. Poll aralığını ayarlayın (opsiyonel)

Varsayılan 60 saniyedir; değiştirmek için:

```bash
curl -s -X PUT http://localhost:8000/api/settings/poll-interval \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"poll_interval_seconds":300}'
```

Worker bu değeri her döngü başında veritabanından tazeden okur — restart
gerekmez (FR-SET-2).

### 5. Senkronizasyon durumunu kontrol edin

```bash
curl -s http://localhost:8000/api/settings/sync-status -H "Authorization: Bearer $TOKEN"
```

`last_synced_at`, `next_poll_at` ve varsa `last_sync_error` döner.

### Faz 0'da neler senkronize edilir?

Task/subtask (flat, `parent_id` referanslı), statü, statü kategorisi
(en iyi çaba eşlemesi — ClickUp'ta native "cancelled" tipi yoktur),
assignee (e-posta üzerinden GatewayHub kullanıcılarına eşlenir — eşleşmeyen
e-postalar sessizce atlanır), öncelik, bitiş tarihi, etiketler ve yorumlar.
Yazma (write-back) **yoktur** — ClickUp'ta yapılan değişiklikler her poll
döngüsünde GatewayHub'a akar, ancak GatewayHub'dan ClickUp'a hiçbir şey
yazılmaz (Faz 1'e kadar).

### Rate limit

ClickUp API çağrıları bir token-bucket ile sınırlandırılır
(`providers/rate_limit.py`); limit aşıldığında istekler kuyruğa
alınıp yavaşlar, senkronizasyon asla hata ile durmaz (FR-SYNC-4).

## Jira

Henüz mevcut değil. `docs/PRD.md` Faz 2 kapsamında read-only bir Jira
adapter'ı planlanıyor; `TaskProvider` arayüzü (`backend/providers/base.py`)
bunun için tasarlandı ama somut bir Jira sınıfı henüz yazılmadı.
