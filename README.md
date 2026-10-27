# Kobo dashboard

A 600x800 grayscale image (today's date, Hamilton weather, today's Google Calendar events) rebuilt hourly by GitHub Actions and published to GitHub Pages. The Kobo downloads it and uses it as the screensaver.

## 1. GitHub setup

1. Create a new **public** repo and push this folder to it (Pages on private repos needs a paid plan).
2. In Google Calendar: Settings, your calendar, "Integrate calendar", copy **Secret address in iCal format**.
3. In the repo: Settings, Secrets and variables, Actions, add two secrets:
   - `GCAL_ICS_URL`: the iCal address from step 2
   - `DASH_PATH`: a long random string, for example from `openssl rand -hex 16`
4. Settings, Pages, set Source to **GitHub Actions**.
5. Actions tab, run **Build dashboard** once manually.
6. Your image lives at `https://USERNAME.github.io/REPO/DASH_PATH/dashboard.png`. Open it in a browser to check.

Privacy note: the repo is public and so is the image, so anyone with the full URL can see your schedule. The random `DASH_PATH` is what keeps it unguessable. Do not share the URL, and do not commit it to the repo.

## 2. Kobo setup

Connect the Kobo by USB and copy these into the root of the Kobo drive:

- `kobo/.adds/dashboard/` to `.adds/dashboard/`
- `kobo/.adds/nm/dashboard` to `.adds/nm/dashboard`

Edit `.adds/dashboard/config.sh` and set `DASH_URL` to your image URL.

Eject, then tap **Refresh dashboard** in the NickelMenu menu with WiFi available. If it worked, `.adds/dashboard/last_run.log` says `ok` and `.kobo/screensaver/dashboard.png` exists.

Then check Kobo settings for the screensaver option that uses images from the screensaver folder. Keep only `dashboard.png` in that folder so it is the only candidate.

## 3. Local preview

```
pip install -r requirements.txt
python render.py --demo --out preview.png
```

## Not done yet

- Auto refresh on WiFi connect (DHCP hook). Needs testing on your firmware first.
- To-do list and headlines.
