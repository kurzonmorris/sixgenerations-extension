# Installing sixgenbot — copy and paste

Every block below can be pasted straight into a terminal. Nothing needs editing
unless a line says so.

**On Unraid:** open the web interface, click the **>_** terminal icon at the top
right, and paste there.

---

## 1. Get the code

```bash
mkdir -p /mnt/user/appdata
cd /mnt/user/appdata
git clone https://github.com/kurzonmorris/sixgenerations-extension.git sixgen
cd sixgen
```

Already cloned it before? Update instead:

```bash
cd /mnt/user/appdata/sixgen
git checkout main
git pull
```

## 2. Make the data folder

This is where the database, the photos, the exports and the backups live.
**Everything worth keeping is in this one folder.**

```bash
mkdir -p /mnt/user/appdata/sixgenbot-data
cp /mnt/user/appdata/sixgen/sixgenbot/config.example.toml \
   /mnt/user/appdata/sixgenbot-data/config.toml
```

## 3. Start it

**Either** with Docker Compose, if you have the Compose Manager plugin:

```bash
cd /mnt/user/appdata/sixgen
docker compose -f sixgenbot/docker-compose.yml up -d --build
```

**Or** without it — plain Docker, which works on any Unraid install:

```bash
cd /mnt/user/appdata/sixgen
docker build -t sixgenbot -f sixgenbot/Dockerfile .
docker run -d \
  --name sixgenbot \
  --restart unless-stopped \
  -p 8770:8770 \
  -v /mnt/user/appdata/sixgenbot-data:/data \
  sixgenbot
```

Both do the same thing. The plain-Docker one needs no plugin, so use that if in
any doubt.

## 4. Open it

```
http://<your-server>:8770/
```

On Unraid that is usually `http://tower.local:8770/` or the server's IP address.
**Over Tailscale the same address works from your phone**, with nothing exposed
to the internet.

You should see *"sixgenbot is running"*, three modules loaded, and *"The database
is ready and empty"*.

## 5. Check it is healthy

```bash
docker exec sixgenbot python -m sixgenbot check
```

That prints every module, the schema version, the item count and the backups. It
exits with an error if anything is broken, so it is the one command to run after
any update.

---

## Running it without Docker

On a desktop or the Windows VM, for trying things out:

```bash
cd sixgen
pip install -r sixgenbot/requirementsDev.txt
SIXGENBOT_DATA=./data python -m sixgenbot serve
```

On Windows PowerShell the last line is:

```powershell
$env:SIXGENBOT_DATA = ".\data"
python -m sixgenbot serve
```

---

## The commands worth knowing

Run them all the same way — `docker exec sixgenbot python -m sixgenbot <command>`:

| Command | What it does |
|---|---|
| `check` | Everything loaded? How many items? When was the last backup? |
| `backup` | Take one now |
| `restore` | Put the newest backup back |
| `restore --file <name>` | Put a particular one back |
| `migrate` | Bring the database up to date (also happens automatically on start) |
| `version` | Which version is running |

A backup also runs by itself every morning at 2:30.

## Backups, and the offsite copy

Backups land in:

```
/mnt/user/appdata/sixgenbot-data/backups/
```

The newest 14 are kept, each one opened and checked when it is written. **For the
offsite copy, point pCloud Drive or rclone at that one folder.** sixgenbot never
holds a pCloud password, which is one fewer thing to lose.

To prove a backup works — worth doing once, now, while there is nothing to lose:

```bash
docker exec sixgenbot python -m sixgenbot backup
docker exec sixgenbot python -m sixgenbot restore
```

The database being replaced is always kept beside it as `.beforeRestore`.

## Updating to a new version

```bash
cd /mnt/user/appdata/sixgen
git pull
docker build -t sixgenbot -f sixgenbot/Dockerfile .
docker restart sixgenbot
docker exec sixgenbot python -m sixgenbot check
```

Your data is untouched — it lives in the other folder. The database upgrades
itself on start.

---

## If something is wrong

**The page will not load**

```bash
docker ps | grep sixgenbot          # is it running?
docker logs --tail 50 sixgenbot     # what did it say?
```

**Port 8770 is already taken.** Change the left-hand number only:

```bash
docker rm -f sixgenbot
docker run -d --name sixgenbot --restart unless-stopped \
  -p 8880:8770 \
  -v /mnt/user/appdata/sixgenbot-data:/data \
  sixgenbot
```

Then open `http://<your-server>:8880/`.

**It says a module did not load.** The page names it, and so does
`docker exec sixgenbot python -m sixgenbot check`. Everything else keeps working
— that is deliberate.

**Start again from scratch**, keeping the data:

```bash
docker rm -f sixgenbot
cd /mnt/user/appdata/sixgen && git pull
docker build -t sixgenbot -f sixgenbot/Dockerfile .
docker run -d --name sixgenbot --restart unless-stopped \
  -p 8770:8770 -v /mnt/user/appdata/sixgenbot-data:/data sixgenbot
```

**Where everything is**

| | |
|---|---|
| Code | `/mnt/user/appdata/sixgen/` |
| Data, photos, exports | `/mnt/user/appdata/sixgenbot-data/` |
| Database | `/mnt/user/appdata/sixgenbot-data/sixgenbot.sqlite` |
| Backups | `/mnt/user/appdata/sixgenbot-data/backups/` |
| Settings | `/mnt/user/appdata/sixgenbot-data/config.toml` |
| Log file | `/mnt/user/appdata/sixgenbot-data/logs/sixgenbot.log` |

## Settings

Edit `config.toml` in the data folder, then `docker restart sixgenbot`. Anything
left out uses its default — you only need the lines you want to change.

```toml
[web]
port = 8770

[logging]
level = "INFO"      # DEBUG when hunting a problem

[modules]
disabled = []       # e.g. ["backups"] to switch one off
```

Tokens and keys go in `secrets.toml` beside it, never in `config.toml` and never
in the repo.

## Moving to HexOS later

Copy the data folder across, clone the code, and run the same Docker command.
Nothing in it is Unraid-specific.
