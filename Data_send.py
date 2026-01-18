import os
import sys
import time
import struct
import argparse

try:
    import serial
except Exception as e:
    serial = None

DEFAULT_PORT = "COM5"       
DEFAULT_BAUD = 115200
DEFAULT_BLOCK = 32  
DEFAULT_FILE = "ekg.txt"
DEFAULT_SLEEP = 0.125


def load_samples(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")

    samples = []
    with open(path, "r") as f:
        for lineno, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                samples.append(int(s))
            except ValueError:
                raise ValueError(f"Invalid integer on line {lineno} in {path}: {s}")

    if not samples:
        raise ValueError("No samples loaded from file")

    return samples


def choose_format(samples, force_signed=False, force_unsigned=False):
    if force_signed and force_unsigned:
        raise ValueError("Cannot force both signed and unsigned")

    mn = min(samples)
    mx = max(samples)

    if force_signed:
        fmt = "<h"
        if mn < -32768 or mx > 32767:
            raise ValueError("Values out of int16 range for signed format")
        return fmt

    if force_unsigned:
        fmt = "<H"
        if mn < 0 or mx > 65535:
            raise ValueError("Values out of uint16 range for unsigned format")
        return fmt

    
    if mn < 0:
        if mn < -32768 or mx > 32767:
            raise ValueError("Values out of int16 range for signed format")
        return "<h"
    else:
        if mx > 65535:
            raise ValueError("Values out of uint16 range for unsigned format")
        return "<H"


def main(argv=None):
    argv = argv or sys.argv[1:]
    p = argparse.ArgumentParser(description="Send ECG samples from a text file over serial in blocks")
    p.add_argument("-p", "--port", default=DEFAULT_PORT, help="Serial port (default: %(default)s)")
    p.add_argument("-b", "--baud", type=int, default=DEFAULT_BAUD, help="Baud rate")
    p.add_argument("-f", "--file", default=DEFAULT_FILE, help="Input text file with one integer per line")
    p.add_argument("-n", "--block-samples", type=int, default=DEFAULT_BLOCK, help="Number of samples per block")
    p.add_argument("-s", "--sleep", type=float, default=DEFAULT_SLEEP, help="Sleep (seconds) between blocks")
    p.add_argument("--hz", type=float, help="Target sample rate in Hz (overrides --sleep). Sleep will be block_samples / hz")
    p.add_argument("--one-shot", action="store_true", help="Send a single block and exit (useful for testing)")
    p.add_argument("--force-signed", action="store_true", help="Force signed int16 packing")
    p.add_argument("--force-unsigned", action="store_true", help="Force unsigned uint16 packing")

    args = p.parse_args(argv)

    samples = load_samples(args.file)
    fmt = choose_format(samples, force_signed=args.force_signed, force_unsigned=args.force_unsigned)

    print(f"Loaded {len(samples)} samples from {args.file}")
    print(f"Using format {fmt} (little-endian, {'signed' if fmt=="<h" else 'unsigned'})")

    if args.hz is not None:
        if args.hz <= 0:
            raise ValueError("--hz must be > 0")
        args.sleep = float(args.block_samples) / float(args.hz)
        print(f"Target sample rate: {args.hz} Hz -> sleep per block set to {args.sleep:.6f} s (block size={args.block_samples})")

    if serial is None:
        raise RuntimeError("pyserial is not installed or could not be imported. Install with: pip install pyserial")

    ser = None
    try:
        ser = serial.Serial(args.port, args.baud, timeout=1)
    except Exception as e:
        raise RuntimeError(f"Could not open serial port {args.port}: {e}")

    idx = 0
    try:
        def build_block():
            nonlocal idx
            block = []
            for _ in range(args.block_samples):
                block.append(samples[idx])
                idx += 1
                if idx >= len(samples):
                    idx = 0
            return block

        if args.one_shot:
            block = build_block()
            packet = b"".join(struct.pack(fmt, s) for s in block)
            ser.write(packet)
            print(f"Sent one block of {len(block)} samples")
            return

        print(f"Starting continuous send to {args.port} at {args.baud} bps. Block size={args.block_samples}, sleep={args.sleep}s")
        while True:
            block = build_block()
            packet = b"".join(struct.pack(fmt, s) for s in block)
            ser.write(packet)
            time.sleep(args.sleep)

    except KeyboardInterrupt:
        print("Interrupted by user, exiting...")
    finally:
        if ser is not None and getattr(ser, 'is_open', False):
            try:
                ser.close()
            except Exception:
                pass


if __name__ == '__main__':
    main()
