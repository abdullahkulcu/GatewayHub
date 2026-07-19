# GatewayHub — İlerleme Takibi (Faz 0)

Faz 0 kapsamı PRD Bölüm 8'e göre küçük tasklara bölünmüştür. Her çağrıda `[ ]`
durumundaki en üstteki task tamamlanır.

- [x] T1: Proje iskeleti — dizin yapısı (backend/, frontend/, worker/, docs/), Makefile (dev/test/lint), .env.example, docker-compose.yml iskeleti (postgres+redis+app+worker), README iskeleti. Backend: FastAPI app + pydantic Settings (.env okuma) + `/healthz` endpoint + pytest/ruff/mypy kurulumu.
  - `backend/app/{config.py,main.py}` + `backend/tests/test_health.py` (pytest yeşil, ruff+mypy temiz). `docker-compose.yml`'e worker servisi henüz eklenmedi — worker'ın gerçek bir davranışı olmadan (T16) compose'a eklemek yarım bırakılmış bileşen olurdu; worker `Dockerfile`'ı ve compose servisi T26'da tamamlanacak.
- [x] T2: SQLAlchemy 2 + Alembic kurulumu, DB engine/session yönetimi, Postgres bağlantısı; ilk (boş) migration.
  - `backend/app/db.py` (engine/SessionLocal/Base/get_db), `backend/alembic/` (env.py app metadata'sını okuyor, script.py.mako modern tip sözdizimiyle), `016ecf2912ae_baseline` boş migration. `backend/tests/conftest.py` her test session'ında `alembic upgrade head`'i gerçek bir test Postgres'ine (`gatewayhub_test`) karşı çalıştırıyor — testler SQLite/mock değil gerçek Postgres kullanıyor (PRD Postgres'i sabit teknoloji sayıyor).
- [x] T3: Canonical model — `users` tablosu (id, email, password_hash, role, must_change_password) + migration + testler.
  - `backend/app/models/user.py` (`UserRole` enum `admin`/`member`, DB'de `values_callable` ile küçük harf saklanıyor), migration `5eb669c2a523_add_users_table`. `tests/conftest.py`'deki `db_session` fixture'ı SQLAlchemy 2.0 `join_transaction_mode="create_savepoint"` kullanacak şekilde güncellendi — IntegrityError testinden sonra da outer transaction bozulmadan rollback edilebiliyor.
- [x] T4: Canonical model — `tasks` tablosu (PRD Bölüm 7 taslağı: id, provider, provider_task_id, parent_id, title, description, status, status_category, assignees, priority, due_date, tags, provider_raw, provider_updated_at, last_synced_at, sync_version, write_state) + migration + testler.
  - `backend/app/models/task.py`, migration `2fdf9a9f755d_add_tasks_table`. `parent_id` aynı `tasks` tablosuna self-FK (subtask ayrı varlık değil — FR-MODEL-1). `(provider, provider_task_id)` unique constraint idempotent upsert için temel. `provider_raw` JSONB ile haritalanamayan alanlar kayıpsız saklanıyor (FR-MODEL-3).
- [x] T5: Canonical model — `comments` tablosu (task_id, author, body, provider_comment_id, created_at) + migration + testler.
  - `backend/app/models/comment.py`, migration `e88b152305a4_add_comments_table`. `task_id` -> `tasks.id` `ON DELETE CASCADE`; `(task_id, provider_comment_id)` unique constraint idempotent upsert için. `author` provider'daki görünen isim (GatewayHub `users` tablosuna FK değil — yorum sahibi GatewayHub kullanıcısı olmayabilir).
- [ ] T6: Canonical model — `settings` tablosu (key/value, şifreli değer) + Fernet şifreleme yardımcıları (SECRET_KEY'den anahtar türetme) + testler.
- [ ] T7: Auth — parola hashleme (argon2/bcrypt), login endpoint'i (JWT/session), ilk boot admin oluşturma (ADMIN_EMAIL/ADMIN_PASSWORD), ilk girişte parola değişikliği zorunluluğu + testler.
- [ ] T8: Kullanıcı yönetimi API'leri (admin only): ekleme/çıkarma/listeleme, parola sıfırlama + testler.
- [ ] T9: `TaskProvider` abstract class (`backend/providers/base.py`): backfill(), fetch_changes(since), parse_webhook(payload) [NotImplemented], push_change(change) [NotImplemented], capabilities() + testler.
- [ ] T10: ClickUp adapter — token doğrulama, workspace/space/list keşif çağrıları (respx mock'lu testler).
- [ ] T11: ClickUp adapter — backfill(): task/subtask/status/assignee/tag/priority/due_date çekme ve canonical modele upsert + testler.
- [ ] T12: ClickUp adapter — yorumların backfill'i (comments) + testler.
- [ ] T13: ClickUp adapter — fetch_changes(since): artımlı sync + testler.
- [ ] T14: Rate limit yönetimi — token-bucket wrapper (FR-SYNC-4) + testler.
- [ ] T15: Settings API — provider token ekleme/test etme (maskeleme `pk_****`), sync kapsamı (workspace/space/list seçimi), poll aralığı ayarı + testler.
- [ ] T16: Worker process — poll scheduler: her döngü başında settings'i DB'den sıcak okuma, ClickUp adapter çağırma, idempotent upsert, sync durumu kaydı (son başarılı sync, hata) + testler.
- [ ] T17: Tasks API — liste endpoint'i (filtreler: assignee, statü, tag, liste, parent var/yok; sıralama) + testler.
- [ ] T18: Tasks API — detay endpoint'i (açıklama, yorumlar, subtask listesi, aktivite meta verisi) + testler.
- [ ] T19: Sync/queue durum API'si (son poll zamanı, sıradaki poll, hata durumu — FR-SYNC-5/FR-SET-4 okuma tarafı) + testler.
- [ ] T20: Frontend iskelet — Vite + React + TS + Tailwind + TanStack Query kurulumu, FastAPI static serve entegrasyonu, login sayfası + ilk girişte parola değişikliği akışı.
- [ ] T21: Frontend — Liste görünümü (filtrelenebilir, sıralanabilir, subtasklar bağımsız satır).
- [ ] T22: Frontend — Board görünümü (statü kolonlu, subtask bağımsız kart + parent rozeti, aç/kapa toggle).
- [ ] T23: Frontend — Task detay paneli (markdown açıklama, yorumlar, subtask listesi, aktivite meta verisi).
- [ ] T24: Frontend — Keyboard-first navigasyon (j/k, statü/assignee hızlı değişim, command palette Cmd/Ctrl+K).
- [ ] T25: Frontend — Settings sayfası (provider token, sync kapsamı, poll aralığı, kullanıcı yönetimi UI).
- [ ] T26: Docker Compose — tam entegrasyon (app: API+UI static serve, worker, postgres, redis) tek komutla ayağa kalkma; Dockerfile'lar.
- [ ] T27: `setup.sh` — kullanıcı isteği: makineye indirip tek script ile kurulum (`.env` yoksa `.env.example`'dan oluştur + rastgele `SECRET_KEY` üret + `docker compose up -d --build` + hazır olduğunda panel URL'ini yazdır). README'deki `cp .env.example .env && docker compose up` akışının yerini almaz, ona ek pratik bir kısayoldur.
- [ ] T28: README finalize (≤10 satır kurulum, `setup.sh` seçeneğine referans), Faz 0 kapsam kontrolü.
- [ ] T29: Kalite geçişi — ruff+mypy+tsc temiz, coverage ≥%80 core+provider, tüm testler yeşil; Faz 0 başarı kriterleri kontrolü.
