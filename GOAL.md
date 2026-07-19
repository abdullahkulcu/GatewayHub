# GatewayHub — Geliştirme Görevi

Sen GatewayHub projesinin tek geliştiricisisin. GatewayHub; ClickUp/Jira gibi task management araçlarının üzerine kurulan, self-hosted, open source bir görünüm katmanıdır (lens). Bu repo'da `docs/PRD.md` dosyası ürünün tam gereksinim dokümanıdır ve **bağlayıcıdır** — her kararında önce PRD'ye bak.

## GÖREV (GOAL)

**Faz 0'ı (Read-only Lens) uçtan uca, çalışır ve test edilmiş şekilde tamamla.** Faz 0'ın kapsamı ve başarı kriterleri PRD Bölüm 8'de tanımlıdır. Özet: ClickUp read-only adapter (backfill + poll), canonical model (Postgres), çoklu kullanıcı auth + varsayılan admin, liste ve board görünümleri (subtasklar bağımsız render edilebilir), temel filtreler, keyboard gezinme, Settings temel sayfası, Docker Compose ile tek komut kurulum.

## ÇALIŞMA DÖNGÜSÜ (her çağrıda aynen uygula)

1. `PROGRESS.md` dosyasını oku. Yoksa: PRD Faz 0 kapsamını küçük, tek oturumda bitirilebilir tasklara böl, checkbox listesi olarak `PROGRESS.md`'ye yaz, ilk taskı seç.
2. `[ ]` durumundaki **en üstteki** taskı seç. Bir çağrıda **yalnızca bir task** tamamla.
3. Taskı uygula. Kod yaz, test yaz, testleri çalıştır (`make test` / `pytest` / `npm test`). Testler geçmeden task bitmiş sayılmaz.
4. `PROGRESS.md`'yi güncelle: taskı `[x]` yap, altına tek satır not düş (ne yapıldı, önemli karar varsa nedeni).
5. Anlamlı bir commit at: `feat(scope): açıklama` formatında, İngilizce commit mesajı.
6. Engellendiysen (dış bilgi eksik, PRD'de belirsizlik, API davranışı beklenmedik): taskı `[!]` işaretle, `PROGRESS.md`'nin en üstündeki `## BLOCKED` bölümüne soruyu yaz ve **dur**. Tahmin yürüterek ilerleme.
7. Tüm tasklar `[x]` ise: `PROGRESS.md`'nin en üstüne `## FAZ 0 TAMAM` yaz, Faz 0 başarı kriterlerini tek tek kontrol edip her birinin karşılandığını kanıtıyla (dosya/test referansı) listele ve dur. **Faz 1'e kendiliğinden başlama.**

## TEKNOLOJİ VE YAPI (sabit, tartışmaya kapalı)

- Backend: **Python 3.12 + FastAPI**, SQLAlchemy 2 + Alembic, Postgres 16, Redis 7.
- Frontend: **React + Vite + TypeScript**, TanStack Query, Tailwind. Panel `frontend/` dizininde ayrı build, FastAPI static olarak serve eder.
- Worker: ayrı process (`worker/`), poll scheduler burada çalışır.
- Repo yapısı: `backend/` (app, models, api, providers, settings), `frontend/`, `worker/`, `docs/`, `docker-compose.yml`, `Makefile` (`make dev`, `make test`, `make lint`).
- Provider soyutlaması: `backend/providers/base.py` içinde `TaskProvider` abstract class — `backfill()`, `fetch_changes(since)`, `parse_webhook(payload)` (Faz 0'da NotImplemented bırakılabilir), `push_change(change)` (Faz 0'da NotImplemented), `capabilities()`. ClickUp adapter'ı `backend/providers/clickup.py`. **Core kodda hiçbir yerde ClickUp'a özel mantık olmayacak.**
- Canonical model: PRD Bölüm 7'deki tablo taslağına uy. Subtask ayrı varlık DEĞİLDİR; `parent_id` referanslı flat `tasks` tablosu.

## YAPILANDIRMA KURALLARI (kritik)

- `.env` yalnızca statik değerler içerir: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `APP_PORT`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. `.env.example` her zaman güncel tutulur.
- ClickUp/Jira token'ları ve tüm entegrasyon ayarları **panelden** girilir, `settings` tablosunda **şifreli** saklanır (Fernet, anahtar `SECRET_KEY`'den türetilir), asla loglanmaz, API response'larında maskelenir (`pk_****`).
- İlk boot'ta `ADMIN_EMAIL`/`ADMIN_PASSWORD` ile varsayılan admin oluşturulur (varsayılan `admin@local`/`changeme`); ilk girişte parola değişikliği zorunlu.
- Poll aralığı ve sync kapsamı (workspace/space/list seçimi) panelden ayarlanır, worker restart'sız sıcak okur (her döngü başında settings'i DB'den çeker).

## KALİTE KURALLARI

- Her backend modülü için pytest testi; adapter için ClickUp API mock'lu testler (responses/respx). Coverage hedefi: core ve provider katmanında ≥ %80.
- `ruff` + `mypy` temiz; frontend'de `tsc --noEmit` temiz.
- Hiçbir secret commit edilmez; `git diff --staged` içinde token/parola görürsen commit'i durdur.
- README: kurulum 10 satırı geçmez — `cp .env.example .env` → `docker compose up` → tarayıcıda panel → Settings'ten ClickUp token gir.

## KAPSAM KORUMASI (guardrails)

- Faz 0 dışına çıkma: write-back yok, webhook yok, AI yok, WebSocket yok, plugin yok. Bu özelliklerin "temelini atmak" da yasak — YAGNI.
- PRD ile çeliştiğini düşündüğün bir durum görürsen kod yazma, `## BLOCKED`'a yaz ve dur.
- Var olan testleri asla silme veya zayıflatma; kırılan testi düzelt.
- `docs/PRD.md` ve `GOAL.md` dosyalarını değiştirme — bunlar insan tarafından yönetilir.
