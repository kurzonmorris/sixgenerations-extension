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
| `import --csv <file>` | Read a Crosslist export. Dry run unless `--apply` |
| `photos` | Download every photo still missing. Resumable |
| `backup` | Take one now |
| `restore` | Put the newest backup back |
| `restore --file <name>` | Put a particular one back |
| `migrate` | Bring the database up to date (also happens automatically on start) |
| `version` | Which version is running |

A backup also runs by itself every morning at 2:30.

## Loading your inventory

**The easy way: the Files page.** Open `http://<your-server>:8770/files`, choose
the CSV, press **Upload it**. It shows you what importing would do — how many
new, how many updated, how many photographs it would queue — and nothing is
written until you press **Import it**.

No shares, no `cp`, no quoting paths with spaces in them. It works from a phone
over Tailscale too.

The same page has **Take a copy away**: the whole inventory, or just the items
still to be checked, or the sold ones, as a CSV that opens in LibreOffice Calc.
Backups can be downloaded from there as well.

### Or from the command line

Put the Crosslist export where the container can see it:

```bash
mkdir -p /mnt/user/appdata/sixgenbot-data/imports
# copy listings-2026-09-15.csv into that folder, then:
docker exec sixgenbot python -m sixgenbot import --csv /data/imports/listings-2026-09-15.csv
```

That is a **dry run** — it reads the whole file, tells you what it would do, and
writes nothing. Expect something like:

```
2125 rows read — 2125 new, 0 updated, 0 unchanged.
405 have no SKU, 639 share one. 9098 photos to fetch.
```

Happy with it? Run the same command with `--apply` on the end. Running it twice
is safe: the second time reports *0 new, 2125 unchanged*.

## Downloading the photographs

**Do this before the Crosslist subscription ends.** Every photo is hosted on
their servers, and for items never listed anywhere it is the only copy.

**Photos** in the left menu, or `http://<server>:8770/photos`.

It tells you how many are **safely here** and how many are **still only on
Crosslist**. Press **Fetch them** — or put `50` in the box first if you want to
watch it work once before letting it run.

It runs in the background, so you can close the page. The number does not move on
its own: press **Check again** when you want a newer one. **Stop** stops it within
a few seconds, and starting again picks up where it left off — nothing is fetched
twice.

Anything that failed is listed with the reason the server gave, and is tried again
the next time you press Fetch them.

Expect a couple of GB and a while: 9,098 photos, five at a time, which is polite
to their servers.

### Or from the command line

```bash
docker exec sixgenbot python -m sixgenbot photos
docker exec sixgenbot python -m sixgenbot check
```

## Working through the backlog

**To review** in the left menu, or `http://<server>:8770/review`.

Three lists across the top:

| List | What it is |
|---|---|
| Not checked yet | Everything nobody has confirmed |
| **Never listed** | The withdrawn stock — photographed, priced, not online |
| Listed, not checked | Already up, details unconfirmed |

Open **Choose what is shown** and tick only the things you want to work on — if
today's job is sizes, tick *SKU*, *Title* and *Size UK* and nothing else. That
choice does two things: it sets the columns in the list, and it sets which boxes
appear on the next screen. It is remembered.

Then tick the items, press **Work on the ticked items**, correct them, and press
**Save all**. Up to 40 at a time.

**"I have checked this one"** is what takes an item off the list. Saving a
correction on its own does not — so you can fix a size now and confirm the rest
later. Nothing on this screen goes to Vinted, eBay or the shop.

Items are listed in the order you walk the room: column, then box, then item
number.

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
docker rm -f sixgenbot
docker run -d --name sixgenbot --restart unless-stopped \
  -p 8770:8770 -v /mnt/user/appdata/sixgenbot-data:/data sixgenbot
docker exec sixgenbot python -m sixgenbot check
```

**`docker restart` is not enough, and looks like it worked.** A container is
built from an image once, when it is created. Rebuilding the image leaves the
running container exactly as it was, so `restart` brings back the *old* code with
no error to say so — the giveaway is a command the new version should have being
rejected as an invalid choice. The container has to be removed and run again.

On Compose, `docker compose -f sixgenbot/docker-compose.yml up -d --build` does
recreate the container, so it does not have this problem.

**Your data is untouched** — it lives in the other folder, and the database
upgrades itself on start. `check` prints the schema version, which is the quickest
way to see the new code is really running.

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
