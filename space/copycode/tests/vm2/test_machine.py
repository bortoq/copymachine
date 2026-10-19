#!/usr/bin/env python3
"""Layout contract, consumer configuration and incompatible-manifest checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'compat/vm2'))
from machine import PROTOCOL, describe, require_compatible, space_bits_for_bytes
from boundary import Format, protocol

for bits, slots in [(65520, 8), (30000, 9), (space_bits_for_bytes(8*1024*1024), 256),
                    (space_bits_for_bytes(64*1024*1024), 256), (space_bits_for_bytes(256*1024*1024), 256)]:
    desc = describe(bits, slots)
    f = Format(bits, slots)
    assert desc['image_bytes'] == (bits+7)//8
    assert desc['processor']['bits'] == f.layer_bits
    assert [x['width_bits'] for x in desc['instruction']['fields']] == [f.z, f.a, f.a]
    ops, req, rsp = protocol(bits)
    for record, (fields, n) in [('req', req), ('rsp', rsp)]:
        assert desc['records'][record]['bits'] == n
        assert {v['name']: (v['offset_bits'], v['width_bits'])
                for v in desc['records'][record]['fields']} == fields
    assert ops == desc['contract']['operations']
    assert require_compatible(json.loads(json.dumps(desc)), bits, slots) == desc
    assert f.devices['stdin'] == bits+1
    assert f.devices['status'] == bits+4 and f.devices['snapshot'] == bits+5
    assert desc['terminal']['record_bytes'] == 80

try:
    describe(8*1024*1024*8-4, 256)
except ValueError as error:
    assert 'no room' in str(error)
else:
    raise AssertionError('obsolete four-position channel layout accepted')

with tempfile.TemporaryDirectory() as directory:
    tmp = Path(directory)
    desc = describe(65520, 8)
    manifest = tmp/'machine.json'
    manifest.write_text(json.dumps(desc))
    # External consumer chooses module path independently of binary location.
    env = dict(os.environ, PYTHONPATH=str(ROOT/'compat/vm2'))
    command = [sys.executable, '-m', 'machine', '-s', '65520', '-p', '8']
    result = subprocess.run(command+['--check', str(manifest)], cwd=tmp, env=env,
                            capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == desc
    # Revision 2's pipeline identity must not match the new tick contract.
    obsolete = json.loads(json.dumps(desc))
    obsolete['contract']['tick'] = dict(
        memory_intervals='all active source and destination intervals pairwise disjoint',
        phases=['device-transfer','sys-control','sys-answer'],
        transfers_per_device=1, requests_per_sys=1,
        seek_close_transfer_conflict='separate-ticks', close_sys_answer='disabled')
    try:
        require_compatible(obsolete,65520,8)
    except ValueError:
        pass
    else:
        raise AssertionError('obsolete same-tick SYS pipeline accepted')
    changed = tmp/'changed.def'
    changed.write_text(PROTOCOL.read_text().replace('status, 8', 'status, 16'))
    altered = describe(65520, 8, protocol_path=changed)
    assert altered['records']['rsp']['bits'] == desc['records']['rsp']['bits']+8
    assert altered['protocol_id'] != desc['protocol_id']
    assert altered['layout_id'] != desc['layout_id']
    result = subprocess.run(command+['--protocol', str(changed), '--check', str(manifest)],
                            cwd=tmp, env=env, capture_output=True, text=True)
    assert result.returncode != 0 and 'incompatible boundary' in result.stderr
    for bad in (describe(30000, 8), dict(desc, schema='unknown'),
                dict(desc, boot={}), dict(desc, layout_id='forged')):
        try:
            require_compatible(bad, 65520, 8)
        except ValueError:
            pass
        else:
            raise AssertionError('incompatible manifest accepted')

print('machine: layouts, JSON CLI, configurable import and incompatibility checks passed')
