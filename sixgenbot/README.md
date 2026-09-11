# sixgenbot

**v_0.2.0 — stage 2, the database.** It runs, logs, loads modules, serves three
pages, and owns a migrated SQLite database that backs itself up every night and
can be restored with one command. Nothing about Vinted yet — that is stage 5 of
`../docs/SIXGENBOT_PLAN.md`, and importing real data is stage 3.

**Installing it: `../docs/INSTALL_GUIDE.md`** — copy and paste, start to finish.

## Run it on the server

```bash
docker compose -f sixgenbot/docker-compose.yml up -d --build
```

Then open `http://<server>:8770/`. Over Tailscale the same address works from a
phone with nothing exposed to the internet.

## Run it on a desktop

```bash
pip install -r sixgenbot/requirementsDev.txt
SIXGENBOT_DATA=./data python -m sixgenbot serve
```

## Check it without opening a port

```bash
python -m sixgenbot check
```

Prints every module and whether it loaded. This is what to run after changing
one — it exits non-zero if anything is broken.

## Settings

Copy `config.example.toml` into the data directory as `config.toml`. Secrets go
in `secrets.toml` beside it, which is gitignored and never appears in an export
or a log line.

## Adding a feature

A feature is a folder under `modules/` with a `module.py` in it:

```python
NAME = "myFeature"
VERSION = "v_0.1.0"

def register(bot):
    bot.templates(Path(__file__).parent / "templates")
    bot.addRoutes(routes.router)
    bot.addMenuItem("My Feature", "/mine", group="ITEMS")
    bot.onEvent("item.changed", routes.recount)
```

Nothing in `core/` changes. **A module never imports another module** — a test
enforces it. They talk through the database and the event bus instead.

## Backups

One runs at 2:30 every morning into `<data>/backups/`, and each is opened and
checked as it is written. The newest 14 are kept.

```bash
docker exec sixgenbot python -m sixgenbot backup     # take one now
docker exec sixgenbot python -m sixgenbot restore    # put the newest back
```

Restoring keeps whatever it replaced beside the database as `.beforeRestore`.
For the offsite copy, point pCloud Drive or rclone at the backup folder —
sixgenbot never holds a pCloud password.

## Tests

```bash
python -m pytest sixgenbot/tests -q
```

50 tests. The one that matters most puts a backup back and checks the data is
all there.
