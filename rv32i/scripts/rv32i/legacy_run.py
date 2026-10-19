"""Run a copy-space image, forwarding streams and returning the guest exit code."""
import argparse
import json
from contextlib import ExitStack
import os
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "modules"))
import dependencies
from rv32i import EXIT_CODE, Layout, SPACE_BYTES, STATUS


def word(raw, address):
    return sum(((raw[(address+i)//8] >> (7-(address+i)%8)) & 1) << i for i in range(32))


def run_new(args):
    """Ordinary stdin boot; terminal metadata and optional dump use fd 3/4."""
    from copycode.vm2.machine import require_compatible, space_bits_for_bytes
    from copycode.vm2.terminal import attach_terminal
    from copycode.vm2.transport import run_stream
    manifest_path = args.image.with_name(args.image.name + ".json")
    manifest = json.loads(manifest_path.read_text())
    bits = space_bits_for_bytes(args.space_bytes)
    if "boundary" not in manifest:
        raise ValueError("image lacks boundary manifest; rebuild with current --new-emulator generator")
    require_compatible(manifest["boundary"], bits, manifest["processor_n"])
    if args.trace is not None and not manifest.get("trace"):
        raise ValueError("rebuild with --trace-mode full/channels")
    if manifest.get("monitor"):
        if args.output_path is not None or args.dump_space is not None:
            raise ValueError("segment output/snapshots are stored under --segments; omit --out/--dump-space")
        if args.segments is None or args.input_path is None:
            raise ValueError("cooperative image requires --segments NEW_DIR and --in FILE")
        from copycode.vm2.checkpoint import execute_segments
        result = execute_segments(args.space, args.image, manifest, args.input_path, args.segments,
                                  max_segments=args.max_segments, checkpoint_from=args.checkpoint_from,
                                  timeout=args.timeout, ticks=args.ticks or 0)
        if args.trace is not None:
            if not manifest.get("trace"):
                raise ValueError("rebuild with --trace-mode full/channels")
            entries=[]
            for entry in result["segments"]:
                saved=json.loads((Path(entry["path"])/"checkpoint.json").read_text())
                entries.append(dict(path=entry["path"],trace=str(Path(entry["path"])/"debug.bin"),
                                    audit=saved["trace_audit"],totals=saved["trace_totals"]))
            args.trace.write_text(json.dumps(dict(format="PCS2-index-v1",manifest=str(args.segments/"image.json"),
                                                  segments=entries),indent=2)+"\n")
        print("Saved space: " + result["checkpoint"], file=sys.stderr)
        if not result["complete"]:
            return 75
        if result["terminal"]["guest_status"] != 10:
            return 125
        return result["terminal"]["exit_code"] & 255
    if args.trace:
        raise ValueError("rebuild with --trace-mode full/channels and use --segments")
    if args.segments or args.checkpoint_from:
        raise ValueError("rebuild with --segment-budget before segmented execution")
    with tempfile.TemporaryDirectory(prefix="rv32i-run-") as directory, ExitStack() as files:
        source = files.enter_context(args.image.open("rb"))
        image = files.enter_context((Path(directory)/"terminal.bin").open("w+b"))
        attach_terminal(source, image, bits, manifest["processor_n"], manifest["labels"]["halt"],
                        snapshot=args.dump_space is not None, exit_address=manifest["exit_code_bit"],
                        guest_status_address=manifest["status_bit"])
        inp = files.enter_context(args.input_path.open("rb", buffering=0)) if args.input_path else sys.stdin.buffer
        out = files.enter_context(args.output_path.open("wb", buffering=0)) if args.output_path else sys.stdout.buffer
        dump = files.enter_context(args.dump_space.open("wb", buffering=0)) if args.dump_space else None
        result = run_stream(args.space, image, bits, manifest["processor_n"], input_stream=inp,
                            stdout=out, debug=sys.stderr.buffer, snapshot=dump,
                            ticks=args.ticks or 0, timeout=args.timeout, description=manifest["boundary"])
    if result.terminal["guest_status"] != 10:
        print(f"RV32I stopped with status {result.terminal['guest_status']}", file=sys.stderr)
        return 125
    return result.terminal["exit_code"] & 255


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--space", type=Path, default=None)
    parser.add_argument("--space-bytes", type=lambda text: int(text, 0), default=None)
    parser.add_argument("--stream", action="store_true", help="send the packet and guest input to the standard core through IN")
    parser.add_argument("--ticks", type=int)
    parser.add_argument("--segments", type=Path, help="new immutable segment session")
    parser.add_argument("--max-segments", type=int, default=1)
    parser.add_argument("--checkpoint-from", type=Path, help="source checkpoint folder; preserved")
    parser.add_argument("--timeout", type=float, default=120, help="new-emulator wall-clock timeout")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--dump-space", type=Path)
    parser.add_argument("--in", dest="input_path", type=Path)
    parser.add_argument("--out", dest="output_path", type=Path)
    parser.add_argument("--new-emulator", action="store_true",
                        help="stdin boot on ordinary space; fd 3 status, optional fd 4 snapshot")
    args = parser.parse_args()
    if args.new_emulator and args.stream:
        parser.error("--stream is not available on the new emulator")
    if args.ticks is not None and args.ticks < 0:
        parser.error("ticks must not be negative")
    if args.space is None:
        args.space = (Path(os.environ.get("SPACE_EMULATOR", str(dependencies.VM2_ROOT / "space")))
                      if args.new_emulator else ROOT / "build/bin/space")
    if args.space_bytes is None:
        # The bulk image needs at least 8 MiB; the stream image keeps the old default.
        args.space_bytes = (8 * 1024 * 1024) if args.new_emulator else SPACE_BYTES
    try:
        if args.new_emulator:
            return run_new(args)
        layout = Layout(args.space_bytes)
        with tempfile.TemporaryDirectory(prefix="rv32i-run-") as directory, ExitStack() as files:
            dump = args.dump_space or Path(directory) / "space.bin"
            command = [str(args.space), "--dump-space", str(dump)]
            if not args.stream:
                command += ["--core", str(args.image)]
            if args.ticks is not None:
                command += ["--ticks", str(args.ticks)]
            if args.trace:
                command += ["--trace", str(args.trace)]
            descriptors = []
            for path, output in [(args.input_path, False), (args.output_path, True)]:
                if path is None:
                    descriptors.append(None)
                else:
                    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC if output else os.O_RDONLY
                    descriptor = os.open(path, flags, 0o666)
                    files.callback(os.close, descriptor)
                    descriptors.append(descriptor)
            # Direct file descriptors: no host-side buffering or guest execution.
            forwarding_errors = []
            if args.stream:
                # Feed the fixed packet first, then relay live guest input. No
                # program decoding or space state changes happen in this relay.
                packet = files.enter_context(args.image.open("rb", buffering=0))
                process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=descriptors[1])

                def forward():
                    try:
                        for source in (packet.fileno(), descriptors[0] if descriptors[0] is not None else 0):
                            while True:
                                chunk = os.read(source, 65536)
                                if not chunk:
                                    break
                                remaining = memoryview(chunk)
                                while remaining:
                                    remaining = remaining[os.write(process.stdin.fileno(), remaining):]
                    except BrokenPipeError:
                        pass
                    except OSError as error:
                        forwarding_errors.append(error)
                    finally:
                        process.stdin.close()

                feeder = threading.Thread(target=forward, daemon=True)
                feeder.start()
                process.wait()
                result = process
            else:
                result = subprocess.run(command, stdin=descriptors[0], stdout=descriptors[1])
            if forwarding_errors:
                raise forwarding_errors[0]
            if result.returncode:
                return 125
            raw = dump.read_bytes()
            layer_bytes = layout.layer_bits//8
            complete = (len(raw) == layout.space_bytes
                        and raw[:layer_bytes] == bytes(layer_bytes))
            if not complete:
                print("RV32I did not complete (possibly tick limit)", file=sys.stderr)
                return 125
            status = word(raw, STATUS)
            if status != 10:
                print(f"RV32I stopped with status {status}", file=sys.stderr)
                return 125
            return word(raw, EXIT_CODE) & 255
    except (OSError, ValueError, KeyError, TimeoutError) as error:
        print(str(error), file=sys.stderr)
        return 125


if __name__ == "__main__":
    sys.exit(main())
