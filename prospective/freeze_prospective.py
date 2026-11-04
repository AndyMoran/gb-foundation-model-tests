"""
Freeze the prospective plan (prospective/PLAN.md, Section 8, step 3).

Checks: a clean working tree that matches GitHub; no tag yet; the self-test (with --models) passed and is committed;
a real-input stand-in run of the current script is committed; the data and weights match the demand study's lock.
Then writes prospective/PROSPECTIVE_LOCK.json, commits it, tags `prospective-plan`, pushes both, and reports success
only once GitHub has the commit and the tag. Git's own error messages are printed if anything fails.

    python prospective/freeze_prospective.py          checks only; prints what would be locked
    python prospective/freeze_prospective.py --tag    freezes
"""
import datetime as dt, glob, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(ROOT, 'code'))
import common as C, models as M

TAG = 'prospective-plan'
SCRIPT = 'prospective/forecasts/forecast_daily.py'
LOCKED = ['prospective/PLAN.md', SCRIPT, 'code/common.py', 'code/inputs.py', 'code/baselines.py', 'code/models.py',
          'code/fetch.py', 'code/requirements-models.txt', 'data/bank_holidays_ew.json']


def git(*a):
    r = subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def fail(msg):
    sys.exit('Freeze refused: ' + msg)


def checks():
    git('fetch', '-q', 'origin', '--tags')
    if git('status', '--porcelain')[1]: fail('uncommitted changes:\n' + git('status', '--short')[1])
    if git('rev-parse', 'HEAD')[1] != git('rev-parse', 'origin/main')[1]: fail('local main differs from origin/main; pull or push first')
    if TAG in git('ls-remote', '--tags', 'origin', TAG)[1]: fail(f'tag {TAG} already exists on GitHub')
    st = 'prospective/forecasts/selftest_prospective.txt'
    if not git('ls-files', st)[1]: fail(f'{st} is not committed')
    txt = open(os.path.join(ROOT, st)).read()
    if 'OVERALL: PASS' not in txt or 'FAIL' in txt or 'PASS  P7' not in txt: fail('the self-test, with --models, has not passed')
    pre = [p for p in glob.glob(os.path.join(ROOT, 'prospective/forecasts/preflight/*.json'))
           if git('ls-files', os.path.relpath(p, ROOT))[1]]
    script_sha = C.sha(os.path.join(ROOT, SCRIPT))
    if not any((lambda r: r['test'] and r['stand_in'] and r['script_sha256'] == script_sha)(json.load(open(p))) for p in pre):
        fail('no committed real-input stand-in run of the current script in prospective/forecasts/preflight/')
    study = json.load(open(os.path.join(ROOT, 'plan', 'PLAN_LOCK.json')))
    if C.sha(os.path.join(C.DATA, 'bank_holidays_ew.json')) != study['data_sha256']['bank_holidays_ew.json']:
        fail('data/bank_holidays_ew.json differs from the demand study lock')
    from huggingface_hub import hf_hub_download
    for name, (repo, rev) in M.REVISIONS.items():
        if C.sha(hf_hub_download(repo, 'model.safetensors', revision=rev)) != study['weights_sha256'][name]:
            fail(f'{name} weights differ from the demand study lock')
    return dict(tag=TAG, frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                parent_commit=git('rev-parse', 'HEAD')[1],
                files_sha256={f: C.sha(os.path.join(ROOT, f)) for f in LOCKED},
                weights_sha256=study['weights_sha256'], revisions={k: list(v) for k, v in M.REVISIONS.items()},
                versions=M.versions(), seed_scoring=20270401, window_end='2027-03-31')


def main(tag):
    lock = checks(); print(json.dumps(lock, indent=1))
    if not tag: print(f'\nAll checks pass. Run `python prospective/freeze_prospective.py --tag` to freeze.'); return
    p = os.path.join(ROOT, 'prospective', 'PROSPECTIVE_LOCK.json'); json.dump(lock, open(p, 'w'), indent=1)
    for step in (('add', 'prospective/PROSPECTIVE_LOCK.json'),
                 ('commit', '-q', '-m', 'Freeze: prospective plan, daily script and lock, before the first prospective forecast'),
                 ('tag', '-a', TAG, '-m', f'Prospective plan frozen {lock["frozen_utc"]}'),
                 ('push', 'origin', 'main'), ('push', 'origin', TAG)):
        code, out = git(*step)
        if code: sys.exit(f'FREEZE INCOMPLETE at "git {" ".join(step)}":\n{out}\nFix this, then push the commit and the tag by hand.')
    git('fetch', '-q', 'origin', '--tags')
    on_main = git('merge-base', '--is-ancestor', 'HEAD', 'origin/main')[0] == 0
    tag_there = TAG in git('ls-remote', '--tags', 'origin', TAG)[1]
    if not (on_main and tag_there): sys.exit('FREEZE INCOMPLETE: GitHub does not show the commit and the tag yet; push them by hand.')
    print(f'\nFrozen: tag {TAG} at {git("rev-parse", "--short", "HEAD")[1]}, confirmed on GitHub. Schedule the daily task next.')


if __name__ == '__main__':
    main('--tag' in sys.argv)
