# GatewayHub

Self-hosted, open source read/write lens over your team's task management tool
(ClickUp first; provider-agnostic core). See `docs/PRD.md` for the full
product spec and `GOAL.md` / `PROGRESS.md` for current development status.

## Kurulum

```
cp .env.example .env
docker compose up
```

Panel `http://localhost:8000` adresinde açılır. Settings sayfasından ClickUp
token'ınızı girin.

Ya da tek komutla: `./setup.sh` (`.env` kurar, `docker compose up` çalıştırır, panel hazır olunca URL'i yazdırır).
