"""Guarded Q2 01.01.03.02 adaptation of Valve Oil's version-prefix popup fix.

Only QIDI_Client/bin/qidiclient is replaced; no firmware manifest or board image
is altered. Unknown bytes or a busy printer are refused. Run through authorized
system-service execution. Binary preimages stay private on the printer.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import urllib.parse
import urllib.request

SOURCE = Path('/home/qidi/QIDI_Client/bin/qidiclient')
BACKUP = Path('/home/qidi/q2-touchscreen-popup-20261123')
STOCK = 'c222bb9c77df6fe714e974f915834841be96c291bb75d44cd6f4d371e174f423'
PATCHED = 'efc4f97012ce2ce1f90d54cf7bfec616907a7f48e33fe892b51aa90712bcee76'
SIZE = 91597520
OFFSETS = (0x227078, 0x227220)
OLD = bytes.fromhex('40020054')
NEW = bytes.fromhex('49020054')


def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def query(names):
    url = 'http://127.0.0.1:7125/printer/objects/query?' + '&'.join(urllib.parse.quote(n) for n in names)
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.load(r)['result']['status']


def admit_idle():
    names = ['webhooks', 'print_stats', 'heaters', 'box_extras', 'tltg_box_rfid', 'configfile']
    s = query(names)
    s = query(names + s['heaters']['available_heaters'])
    if (s['webhooks']['state'] != 'ready' or s['print_stats']['state'] not in ('standby', 'complete', 'cancelled')
            or s['box_extras']['is_tool_change'] or s['tltg_box_rfid']['job']['running']
            or s['configfile']['save_config_pending']
            or any(s[n]['target'] != 0 for n in s['heaters']['available_heaters'])):
        raise RuntimeError('Printer must be ready, idle, saved, and all heaters off')
    manifest = json.loads(Path('/home/qidi/update/firmware_manifest.json').read_text())
    if manifest['SOC']['version'] != '01.01.03.02' or not manifest['SOC']['file'].startswith('QD_Q2_SOC_'):
        raise RuntimeError('Not the reviewed Q2 release')
    return s


def stage(source, destination, patch=False):
    if source.is_symlink() or not source.is_file() or source.stat().st_size != SIZE:
        raise RuntimeError('Unexpected touchscreen file')
    with source.open('rb') as f, destination.open('xb') as out:
        position = 0
        while block := f.read(1 << 20):
            b = bytearray(block)
            if patch:
                for offset in OFFSETS:
                    if position <= offset < position + len(b):
                        i = offset - position
                        if b[i:i+4] != OLD:
                            raise RuntimeError('Comparison branch differs from reviewed bytes')
                        b[i:i+4] = NEW
            out.write(b)
            position += len(b)
        out.flush()
        os.fsync(out.fileno())


def install(staged, metadata):
    os.chmod(staged, stat.S_IMODE(metadata.st_mode))
    os.chown(staged, metadata.st_uid, metadata.st_gid)
    os.replace(staged, SOURCE)
    fd = os.open(SOURCE.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['check', 'apply', 'rollback'])
    args = parser.parse_args()
    if SOURCE.is_symlink() or SOURCE.stat().st_size != SIZE:
        raise RuntimeError('Unexpected touchscreen file')
    current = digest(SOURCE)
    if current not in (STOCK, PATCHED):
        raise RuntimeError('Unreviewed touchscreen hash; preserving it')
    print('CURRENT', current, flush=True)
    if args.operation == 'check':
        return
    if os.geteuid() != 0:
        raise RuntimeError('Authorized system-service execution required')
    before = admit_idle()
    if (args.operation == 'apply' and current == PATCHED) or (args.operation == 'rollback' and current == STOCK):
        print('Already in requested state')
        return
    if BACKUP.is_symlink():
        raise RuntimeError('Refusing linked backup directory')
    BACKUP.mkdir(mode=0o700, exist_ok=True)
    original = BACKUP / 'qidiclient.stock'
    if args.operation == 'apply' and not original.exists():
        stage(SOURCE, original)
    if original.is_symlink() or digest(original) != STOCK:
        raise RuntimeError('Stock rollback hash mismatch')
    (BACKUP / 'before-status.json').write_text(json.dumps(before, indent=2))
    metadata = SOURCE.stat()
    fd, name = tempfile.mkstemp(prefix='.q2-popup-', dir=SOURCE.parent)
    os.close(fd)
    staged = Path(name)
    staged.unlink()
    stage(original, staged, patch=args.operation == 'apply')
    expected = PATCHED if args.operation == 'apply' else STOCK
    if digest(staged) != expected:
        staged.unlink()
        raise RuntimeError('Staged output hash mismatch')
    subprocess.run(['systemctl', 'is-active', '--quiet', 'qidi-client.service'], check=True)
    stopped = False
    replaced = False
    try:
        # Check again after building the ~92 MB candidate, before restarting the UI.
        admit_idle()
        subprocess.run(['systemctl', 'stop', 'qidi-client.service'], check=True, timeout=45)
        stopped = True
        if digest(SOURCE) != current:
            raise RuntimeError('Touchscreen changed during staging')
        install(staged, metadata)
        replaced = True
        if digest(SOURCE) != expected:
            raise RuntimeError('Installed hash mismatch')
        subprocess.run(['systemctl', 'start', 'qidi-client.service'], check=True, timeout=45)
        subprocess.run(['systemctl', 'is-active', '--quiet', 'qidi-client.service'], check=True)
    except BaseException:
        if replaced:
            # Preserve a running system on failure; always return to exact stock.
            restore = SOURCE.with_name('.q2-popup-restore')
            if restore.exists():
                raise RuntimeError('Unexpected rollback staging file; manual recovery required')
            stage(original, restore)
            install(restore, metadata)
        if stopped:
            subprocess.run(['systemctl', 'start', 'qidi-client.service'], timeout=45)
        raise
    finally:
        if staged.exists():
            staged.unlink()
    report = {'operation': args.operation, 'before_sha256': current, 'after_sha256': expected,
              'offsets': [hex(n) for n in OFFSETS], 'stock_backup': str(original),
              'only_service_restarted': 'qidi-client.service'}
    (BACKUP / 'result.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
