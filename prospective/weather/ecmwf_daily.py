"""
Daily collection of ECMWF open-data weather forecasts for Great Britain (Brief 2, revision 4: the prospective track).

Each run downloads one forecast run of ECMWF's IFS model from the free open-data service (CC-BY-4.0), keeps only a
box around Great Britain, and records what was downloaded, when, and its SHA-256 in `manifest.csv`. The download
time is the evidence that the forecast existed before the weather it describes: keep the manifest under version
control and push it regularly.

Variables: 2 m temperature (2t), surface solar radiation downwards (ssrd, accumulated), 10 m wind (10u, 10v) and
total cloud cover (tcc). Steps: 0 to 72 hours, every 3 hours, which covers the next day in full.

Usage (from the folder holding this script):
    python ecmwf_daily.py                    # today's 00 UTC run
    python ecmwf_daily.py --date 2026-11-02  # a run still on the portal (about the last 2-3 days)
    python ecmwf_daily.py --check            # the self-test: no download, writes and reads a synthetic GRIB file

The open-data portal keeps only the most recent runs, so a missed day cannot be recovered later: run this daily.
Attribution required by the licence: "Contains modified Copernicus/ECMWF data" (see ECMWF's Terms of Use).
"""
import argparse, csv, datetime as dt, hashlib, os, socket, sys, time

PARAMS = ['2t', 'ssrd', '10u', '10v', 'tcc']
STEPS = list(range(0, 73, 3))
GB_BOX = dict(lat_min=49.0, lat_max=61.0, lon_min=-9.0, lon_max=2.5)     # Great Britain and surrounding sea
SOURCES = ['ecmwf', 'aws', 'azure', 'google']                           # the open portal, then its cloud copies
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'data')
MANIFEST = os.path.join(HERE, 'manifest.csv')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()


def crop_to_gb(grib_path, nc_path):
    """Keep the GB box from every field in the GRIB file and write one NetCDF file. Returns the variable names."""
    import cfgrib, xarray as xr
    parts = []
    for ds in cfgrib.open_datasets(grib_path, backend_kwargs=dict(indexpath='')):
        lon = ds.longitude
        if float(lon.max()) > 180:                                      # 0..360 grids: shift to -180..180
            ds = ds.assign_coords(longitude=((lon + 180) % 360) - 180).sortby('longitude')
        lat_slice = slice(GB_BOX['lat_max'], GB_BOX['lat_min']) if ds.latitude[0] > ds.latitude[-1] \
            else slice(GB_BOX['lat_min'], GB_BOX['lat_max'])
        sub = ds.sel(latitude=lat_slice, longitude=slice(GB_BOX['lon_min'], GB_BOX['lon_max']))
        parts.append(sub.drop_vars([c for c in ('heightAboveGround', 'surface') if c in sub.coords]))
    merged = xr.merge(parts, compat='override')
    merged.to_netcdf(nc_path)
    return sorted(merged.data_vars)


def download(date, run, raw_path, resol):
    from ecmwf.opendata import Client
    last = None
    for src in SOURCES:
        try:
            Client(source=src, model='ifs', resol=resol, maximum_retries=3, retry_after=30).retrieve(
                date=date.strftime('%Y%m%d'), time=run, stream='oper', type='fc',
                step=STEPS, param=PARAMS, target=raw_path)
            return src
        except Exception as e:                                          # try the next copy of the data
            last = e
            print(f'  {src}: {e}', file=sys.stderr)
    raise RuntimeError(f'all sources failed; last error: {last}')


def log(row):
    new = not os.path.exists(MANIFEST)
    with open(MANIFEST, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new: w.writeheader()
        w.writerow(row)


def collect(date, run, resol, keep_raw):
    os.makedirs(OUT, exist_ok=True)
    stem = f'ifs_{resol}_{date:%Y%m%d}_{run:02d}z'
    raw, nc = os.path.join(OUT, stem + '.grib2'), os.path.join(OUT, stem + '_gb.nc')
    if os.path.exists(nc):
        print(f'{stem}: already collected'); return
    t0 = dt.datetime.now(dt.timezone.utc)
    src = download(date, run, raw, resol)
    variables = crop_to_gb(raw, nc)
    row = dict(run_date=f'{date:%Y-%m-%d}', run_utc=f'{run:02d}', resol=resol, source=src,
               downloaded_utc=t0.isoformat(timespec='seconds'), file=os.path.basename(nc), sha256=sha(nc),
               bytes=os.path.getsize(nc), raw_sha256=sha(raw), variables=' '.join(variables))
    if not keep_raw: os.remove(raw)
    log(row)
    print(f'{stem}: {len(variables)} variables from {src}; {row["bytes"]:,} bytes; sha256 {row["sha256"][:12]}…')


def self_test():
    """No network: writes a synthetic global GRIB field, crops it and checks the box and the values."""
    import tempfile, numpy as np, eccodes
    tmp = tempfile.mkdtemp(); g = os.path.join(tmp, 't.grib2'); n = os.path.join(tmp, 't.nc')
    h = eccodes.codes_grib_new_from_samples('regular_ll_sfc_grib2')
    for k, v in dict(Ni=1440, Nj=721, iDirectionIncrementInDegrees=0.25, jDirectionIncrementInDegrees=0.25,
                     latitudeOfFirstGridPointInDegrees=90, longitudeOfFirstGridPointInDegrees=0,
                     latitudeOfLastGridPointInDegrees=-90, longitudeOfLastGridPointInDegrees=359.75,
                     shortName='2t', typeOfLevel='heightAboveGround', level=2).items():
        eccodes.codes_set(h, k, v)
    lat = np.repeat(np.linspace(90, -90, 721), 1440); lon = np.tile(np.arange(1440) * 0.25, 721)
    lon180 = ((lon + 180) % 360) - 180
    eccodes.codes_set_values(h, 273.15 + lat + lon180 / 100)          # value encodes position, to check the crop
    with open(g, 'wb') as f: eccodes.codes_write(h, f)
    eccodes.codes_release(h)
    names = crop_to_gb(g, n)
    import xarray as xr
    ds = xr.open_dataset(n); v = ds[names[0]]
    ok_box = (float(ds.latitude.min()) >= 49 and float(ds.latitude.max()) <= 61
              and float(ds.longitude.min()) >= -9 and float(ds.longitude.max()) <= 2.5)
    pt = float(v.sel(latitude=51.5, longitude=-0.25)); ok_val = abs(pt - (273.15 + 51.5 - 0.0025)) < 0.05
    print(('PASS' if ok_box else 'FAIL'), 'crop keeps only the GB box',
          f'({float(ds.latitude.min())}..{float(ds.latitude.max())}, {float(ds.longitude.min())}..{float(ds.longitude.max())})')
    print(('PASS' if ok_val else 'FAIL'), f'values survive the crop and the longitude shift (London cell {pt:.3f} K)')
    print('OVERALL:', 'PASS' if ok_box and ok_val else 'FAIL')
    return ok_box and ok_val


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--date', help='run date, YYYY-MM-DD (default: today, UTC)')
    a.add_argument('--run', type=int, default=0, choices=[0, 12], help='run hour UTC (default 0)')
    a.add_argument('--resol', default='0p25', choices=['0p25', '0p1'], help='grid (0p1 published from 20 Oct 2026)')
    a.add_argument('--keep-raw', action='store_true', help='keep the global GRIB file as well (about 30 MB a day)')
    a.add_argument('--check', action='store_true', help='run the offline self-test and stop')
    args = a.parse_args()
    if args.check: sys.exit(0 if self_test() else 1)
    socket.setdefaulttimeout(120)        # a stalled connection raises after 2 minutes, so the retries and mirrors work
    stamp = lambda: dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    print(f'=== start {stamp()}', flush=True)
    date = dt.date.fromisoformat(args.date) if args.date else dt.datetime.now(dt.timezone.utc).date()
    for attempt in range(3):                                            # the 00 UTC run appears around 07-08 UTC
        try:
            collect(date, args.run, args.resol, args.keep_raw); break
        except Exception as e:
            print(f'attempt {attempt + 1} failed at {stamp()}: {e}', file=sys.stderr, flush=True)
            if attempt < 2: time.sleep(600)
    else:
        print(f'=== end {stamp()}: FAILED', flush=True)
        sys.exit('collection failed for this run; try again later the same day, before it leaves the portal')
    print(f'=== end {stamp()}: ok', flush=True)
