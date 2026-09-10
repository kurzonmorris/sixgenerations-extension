# sixgenbot

**v_0.1.0 — stage 1, the skeleton.** It runs, it logs, it loads modules, and it
serves two pages. There is no database and nothing about Vinted yet: that is
stages 2 and 5 of `../docs/SIXGENBOT_PLAN.md`.

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

## Tests

```bash
python -m pytest sixgenbot/tests -q
```
