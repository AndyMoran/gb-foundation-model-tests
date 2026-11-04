# Prospective track: daily ECMWF weather forecasts for Great Britain

`ecmwf_daily.py` saves one ECMWF forecast run a day from the free open-data service, crops it to a box around Great Britain, and records the download time and SHA-256 of each file in `manifest.csv`. The manifest, pushed to a public repository, is the evidence that each weather forecast existed before the weather it describes.

ECMWF's open portal keeps only about the last two or three days of forecasts. A missed day cannot be recovered, so the script must run every day.

## Set up once (WSL)

Use a separate environment, so the locked `tfm` environment is never touched.

```
conda create -y -n wx python=3.11
conda activate wx
pip install ecmwf-opendata cfgrib eccodes xarray netCDF4
git clone https://github.com/AndyMoran/gb-foundation-model-tests.git ~/gb-foundation-model-tests
```

The script is in `prospective/weather/`. Run the offline self-test:

```
cd ~/gb-foundation-model-tests/prospective/weather
python ecmwf_daily.py --check
```

It should end `OVERALL: PASS`. Then collect today's forecast:

```
python ecmwf_daily.py
```

It prints one line per run, for example `ifs_0p25_20261102_00z: 5 variables from ecmwf; 1,203,456 bytes; sha256 …`, and adds a row to `manifest.csv`.

## Run it every day (Windows Task Scheduler)

1. Open **Task Scheduler** and choose **Create Basic Task**. Name it `ECMWF daily`.
2. Trigger: **Daily**, at **09:30** UK time. The 00 UTC run is usually on the portal by about 08:00 UTC.
3. Action: **Start a program**.
   - Program: `wsl.exe`
   - Arguments: `-d Ubuntu -- bash -lc "cd ~/gb-foundation-model-tests/prospective/weather && ~/miniconda3/envs/wx/bin/python ecmwf_daily.py >> collect.log 2>&1"`
4. Finish, then open the task's properties and tick **Run whether user is logged on or not** and **Run task as soon as possible after a scheduled start is missed**.
5. Add a second daily trigger at **15:30** as a safety net. The script skips a run it already has, so a second call costs nothing.

The computer must be on (or able to wake) at those times. Check `collect.log` and the last line of `manifest.csv` once a week.

## Keep the evidence: push every day

Push `manifest.csv` (not the data files) to the project's public repository **every day, straight after collection**, before the forecast day begins. A weekly push would not prove anything: by then several days' weather would already be known. The proof is the push time GitHub records on its own servers (visible in the repository's activity log), not the commit date, which your machine sets.

Once the repository exists, add the push to the scheduled command, so it happens automatically:

```
cd ~/gb-foundation-model-tests/prospective/weather && ~/miniconda3/envs/wx/bin/python ecmwf_daily.py >> collect.log 2>&1 && git add manifest.csv && git commit -q -m "ECMWF forecasts $(date -u +%F)" && git push -q
```

Keep the data files on your machine and back them up; at about 1–2 MB a day they fit comfortably on any drive.

## Licence

ECMWF open data is licensed CC-BY-4.0 under ECMWF's Terms of Use; commercial use is allowed with attribution. Any published result or redistributed file should carry: "Contains modified Copernicus/ECMWF data" or the attribution wording in ECMWF's Terms of Use.

## Changes to the script

- **4 November 2026.** The 09:30 run that day stopped mid-download without logging an error; the 15:30 run collected the day. Two changes: a two-minute network timeout (`socket.setdefaulttimeout(120)`), so a stalled connection raises an error and the existing retries and cloud copies take over; and timestamped `=== start` and `=== end` lines in `collect.log`. What is downloaded, and how it is cropped and hashed, is unchanged.

Recommended Task Scheduler settings (task **Properties → Settings**): **Stop the task if it runs longer than 1 hour**, and **If the task is already running: Stop the existing instance**, so a hung run can never block the 15:30 safety net.
