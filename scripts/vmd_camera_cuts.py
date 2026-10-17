"""Read VMD 0002 adjacent camera keys; emit zero-based frame-pair cut indices."""
import argparse
import json
import struct
from pathlib import Path


def camera_frames(data):
    if len(data) < 54 or not data[:30].rstrip(b"\0").endswith(b"0002"):
        raise ValueError("Expected a complete VMD 0002 header")
    offset = 50  # 30-byte signature + 20-byte model name
    for record_size in (111, 23):  # bone tracks, then morph tracks
        if offset + 4 > len(data):
            raise ValueError("Truncated VMD section count")
        count = struct.unpack_from("<I", data, offset)[0]
        offset += 4 + record_size * count
        if offset > len(data):
            raise ValueError("Truncated VMD animation section")
    if offset + 4 > len(data):
        raise ValueError("Missing camera section count")
    count = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    if offset + 61 * count > len(data):
        raise ValueError("Truncated VMD camera section")
    return sorted({struct.unpack_from("<I", data, offset + 61*i)[0] for i in range(count)})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("vmd")
    p.add_argument("--start-frame", type=int, default=0, help="Zero-based source VMD frame")
    p.add_argument("--frame-count", type=int, required=True)
    p.add_argument("--output")
    a = p.parse_args()
    if a.start_frame < 0 or a.frame_count < 1:
        p.error("Start must be nonnegative and frame count must be positive")
    frames = camera_frames(Path(a.vmd).read_bytes())
    transitions = [b for x, b in zip(frames, frames[1:]) if b-x == 1]
    pairs = [b-a.start_frame-1 for b in transitions
             if 0 <= b-a.start_frame-1 < a.frame_count-1]
    result = json.dumps({"source_frame_start": a.start_frame,
                         "source_frame_count": a.frame_count,
                         "camera_keys": len(frames), "cut_pairs": pairs}, indent=2)
    if a.output:
        Path(a.output).write_text(result + "\n", encoding="utf8")
    print(result)


if __name__ == "__main__":
    main()
