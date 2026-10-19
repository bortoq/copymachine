"""Cache libraries compiled by the actual guest, paused before its next read."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/pforth'))
from common import RV32I_ROOT
import dependencies
from copycode.hostpaths import output_dir
from copycode.vm1.machine import field
from vm2compile.artifact import load, resume, save


def library_image(names):
    base = output_dir(ROOT) / 'initialized'
    observer = output_dir(ROOT) / 'observe-emulator'
    identity = dict(base=hashlib.sha256((base / 'manifest.json').read_bytes()).hexdigest(),
                    observer=hashlib.sha256(observer.read_bytes()).hexdigest(), sources=[])
    for name in names:
        source = (dependencies.COPYCODE_ROOT / 'forth' / name).read_bytes()
        assert source.endswith(b'\n') and all(len(line) < 255 for line in source.splitlines())
        identity['sources'].append([name, hashlib.sha256(source).hexdigest()])
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        target = output_dir(ROOT) / 'guest-libraries' / key
        if (target / 'image/manifest.json').is_file():
            assert json.loads((target / 'library.json').read_text()) == identity
            load(target / 'image')  # Verify every stored payload, not just the cache name.
            base = target / 'image'
            continue
        payload, manifest = load(base)
        mapping = json.loads(payload['map.json'])
        registers = mapping['regions']['registers']['at']
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='loading-', dir=target.parent) as temporary:
            temporary = Path(temporary)
            raw = temporary / 'snapshot.bin'
            env = dict(os.environ, PFORTH_REG_BITS=str(registers), PFORTH_STOP_AT_READ='1',
                       PFORTH_STOP_INPUT_OFFSET=str(len(payload['boot.bin']) + len(source)),
                       PFORTH_DUMP=str(raw))
            command = [str(observer), '-s', str(manifest['vm1']['size']),
                       '-p', str(manifest['vm1']['slots'])]
            with tempfile.TemporaryFile() as incoming, (temporary / 'stderr.log').open('wb') as stderr:
                incoming.write(payload['boot.bin'] + source)
                incoming.seek(0)
                result = subprocess.run(command, stdin=incoming,
                                        stdout=subprocess.PIPE, stderr=stderr, env=env, timeout=500)
            assert result.returncode == 0 and not result.stdout, (name, result.returncode, result.stdout)
            data = raw.read_bytes()
            assert field(data, registers + 1024, 32) == 20, (name, field(data, registers + 1024, 32))
            assert field(data, registers + manifest['rv32i']['status_offset'], 32) != 10, name
            assert f"input_offset={len(payload['boot.bin']) + len(source)}" in (temporary / 'stderr.log').read_text(), name
            compiled, compiled_manifest = resume(base, raw)
            ready = temporary / 'ready'
            save(ready / 'image', compiled, compiled_manifest)
            (ready / 'library.json').write_text(json.dumps(identity, indent=2) + '\n')
            shutil.move(str(ready), target)
        print('PASS guest compiled library:', name, flush=True)
        base = target / 'image'
    return base


def run_guest(name, names, lines, expected, *, timeout=580):
    image = library_image(names)
    folder = output_dir(ROOT) / 'verification' / name
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'result.json').unlink(missing_ok=True)
    task = ('\n'.join(lines) + '\n').encode()
    assert all(len(line) < 255 for line in task.splitlines())
    (folder / 'input.fth').write_bytes(task)
    with (folder / 'stdout.bin').open('wb') as stdout, (folder / 'stderr.bin').open('wb') as stderr:
        result = subprocess.run([str(ROOT / 'pforth'), 'run', str(image)], input=task,
                                stdout=stdout, stderr=stderr, timeout=timeout)
    actual = (folder / 'stdout.bin').read_bytes()
    errors = (folder / 'stderr.bin').read_bytes()
    assert result.returncode == 0, (name, result.returncode, actual[-1000:], errors[-1000:])
    assert actual == expected, (name, actual, expected)
    assert not errors, errors
    record = dict(result='PASS', guest_execution=True, library_manifest_sha256=
                  hashlib.sha256((image / 'manifest.json').read_bytes()).hexdigest(),
                  input_sha256=hashlib.sha256(task).hexdigest(),
                  stdout_sha256=hashlib.sha256(actual).hexdigest())
    (folder / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print('PASS guest Forth:', name, flush=True)
