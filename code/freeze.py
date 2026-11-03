"""
Freeze the plan (plan Section 11, step 4): check everything is in place, write plan/PLAN_LOCK.json, commit it,
tag the commit `demand-plan` and push both. The tag's push time, recorded by GitHub, is the evidence that the plan,
code, data and weights were fixed before any model forecast real GB demand.

Run once, from code/, in the model environment, on the machine that holds the data and the cached weights:
    python freeze.py            checks only; prints what would be locked
    python freeze.py --tag      checks, writes the lock, commits, tags and pushes
"""
import os, sys, re, json, glob, platform, subprocess, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import common as C, models as M

TAG = 'demand-plan'
LOCKED_FILES = ['plan/PLAN.md', 'code/requirements-models.txt'] + sorted(
    os.path.relpath(p, C.ROOT) for p in glob.glob(os.path.join(HERE, '*.py')))


def git(*a):
    return subprocess.run(['git', '-C', C.ROOT, *a], capture_output=True, text=True, check=True).stdout.strip()


def fail(msg):
    sys.exit('Freeze refused: ' + msg)


def checks():
    git('fetch', '-q', 'origin')
    if git('status', '--porcelain'): fail('uncommitted changes:\n' + git('status', '--short'))
    if git('rev-parse', 'HEAD') != git('rev-parse', 'origin/main'): fail('local main differs from origin/main; pull or push first')
    if TAG in git('tag', '--list').split(): fail(f'tag {TAG} already exists')
    for f in ('data/fetch_manifest.json', 'code/selftest_models.txt', 'results/power.json'):
        if not os.path.exists(os.path.join(C.ROOT, f)): fail(f'{f} not found')
        if not git('ls-files', f): fail(f'{f} is not committed')
    st = open(os.path.join(HERE, 'selftest_models.txt')).read()
    if 'OVERALL: PASS' not in st or 'FAIL' in st: fail('selftest_models.txt does not show an overall pass')
    if glob.glob(os.path.join(C.ROOT, 'results', 'attempt*')): fail('a real-run attempt already exists')

    man = json.load(open(os.path.join(C.DATA, 'fetch_manifest.json')))
    data = {}
    for f, v in man['files'].items():
        h = C.sha(os.path.join(C.DATA, f))
        if h != v['sha256']: fail(f'data/{f} does not match fetch_manifest.json')
        data[f] = h

    from huggingface_hub import hf_hub_download
    weights = {}
    for name, (repo, rev) in M.REVISIONS.items():
        h = C.sha(hf_hub_download(repo, 'model.safetensors', revision=rev))
        m = re.search(rf'{name}: weights \S+ sha256 ([0-9a-f]{{64}})', st)
        if not m or m.group(1) != h: fail(f'{name} weights differ from those in selftest_models.txt')
        if h not in open(os.path.join(C.ROOT, 'plan', 'PLAN.md')).read(): fail(f'{name} weights hash is not in the plan')
        weights[name] = h

    return dict(
        tag=TAG, frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
        parent_commit=git('rev-parse', 'HEAD'),
        files_sha256={f: C.sha(os.path.join(C.ROOT, f)) for f in LOCKED_FILES},
        data_sha256=data, data_fetched_utc=man['fetched_utc'],
        weights_sha256=weights, revisions={k: list(v) for k, v in M.REVISIONS.items()}, settings=M.SETTINGS,
        versions=M.versions(), python=platform.python_version(),
        constants=dict(ISSUE_TIME=C.ISSUE_TIME, INPUT_CUTOFF=C.INPUT_CUTOFF, CONTEXT_LEN=C.CONTEXT_LEN, FILL_MAX=C.FILL_MAX,
                       TRAIN_DAYS=C.TRAIN_DAYS, FULL_START=C.FULL_START, FULL_END=C.FULL_END, POST_RELEASE=C.POST_RELEASE,
                       M_THRESHOLD=C.M_THRESHOLD, BOOT_B=C.BOOT_B, BOOT_BLOCK=C.BOOT_BLOCK, L1_SD_MW=C.L1_SD_MW,
                       L1_DRAWS=C.L1_DRAWS, L1_FLAG=C.L1_FLAG),
        seeds=dict(bootstrap=20261103, l1_first=20261104),
        power_sha256=C.sha(os.path.join(C.ROOT, 'results', 'power.json')),
    )


def main(tag):
    lock = checks()
    print(json.dumps(lock, indent=1))
    if not tag:
        print('\nAll checks pass. Run `python freeze.py --tag` to freeze.'); return
    p = os.path.join(C.ROOT, 'plan', 'PLAN_LOCK.json')
    json.dump(lock, open(p, 'w'), indent=1)
    git('add', 'plan/PLAN_LOCK.json')
    git('commit', '-q', '-m', f'Freeze: {TAG}, plan, code, data and weights locked before any model forecast of real GB demand')
    git('tag', '-a', TAG, '-m', f'Preregistered plan frozen {lock["frozen_utc"]}')
    git('push', '-q', 'origin', 'main'); git('push', '-q', 'origin', TAG)
    print(f'\nFrozen. Tag {TAG} at {git("rev-parse", "HEAD")[:7]}, pushed. Next: python run.py real')


if __name__ == '__main__':
    main('--tag' in sys.argv)
