"""Validate reference-bake JSON data; never claim visual or collision acceptance."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("physics")
    p.add_argument("aliases")
    p.add_argument("--repeat")
    p.add_argument("--body-samples")
    p.add_argument("--import-audit")
    p.add_argument("--frames", type=int)
    p.add_argument("--scale", type=float, default=.08)
    p.add_argument("--tolerance", type=float, default=1e-4)
    p.add_argument("--output")
    a = p.parse_args()
    require(a.scale > 0 and a.tolerance > 0, "Scale and tolerance must be positive")
    data, aliases = read(a.physics), read(a.aliases)
    rows = data["samples"]
    dynamic = {k for k, v in aliases.items() if v["dynamic"]}
    require(rows and dynamic, "Empty samples or dynamic bone set")
    require(len(dynamic) == data["physicsBones"], "Physics bone count differs")
    if a.frames is not None:
        require(len(rows) == a.frames, "Frame count differs")
    for i, row in enumerate(rows):
        require(row["frame"] == i, f"Timeline mismatch at sample {i}")
        require(set(row["bones"]) == dynamic, f"Bone set mismatch at sample {i}")
        for name, pose in row["bones"].items():
            q, loc = pose["rotation"], pose["location"]
            require(len(q) == 4 and len(loc) == 3, f"Invalid pose shape: {i}/{name}")
            require(all(math.isfinite(x) for x in q + loc), f"Nonfinite pose: {i}/{name}")
            require(abs(sum(x*x for x in q)-1) < 1e-3, f"Nonunit quaternion: {i}/{name}")
    report = {"status": "numeric_data_verified_visual_review_required",
              "frames": len(rows), "physics_bones": len(dynamic),
              "sha256": digest(a.physics)}
    if a.repeat:
        require(digest(a.repeat) == report["sha256"], "Repeated bake is not byte-identical")
        report["repeat_byte_identical"] = True
    if a.body_samples:
        by_name = {v["name"]: k for k, v in aliases.items()}
        require(len(by_name) == len(aliases), "Original bone names are ambiguous")
        errors = []
        for reference in read(a.body_samples):
            frame = reference["frame"]
            require(0 <= frame < len(rows), "Body reference frame outside bake")
            for name, target in reference["static_collider_bone_world"].items():
                x, y, z = rows[frame]["world"][by_name[name]]
                error = math.dist(target, (x*a.scale, -z*a.scale, y*a.scale))
                require(math.isfinite(error), "Nonfinite body error")
                errors.append(error)
        require(bool(errors) and max(errors) < a.tolerance, "Body collider poses do not align")
        report.update(body_samples=len(errors), max_body_position_error_m=max(errors))
    if a.import_audit:
        audit = read(a.import_audit)
        require(audit["body_fingerprint_before"] == audit["body_fingerprint_after"],
                "Nonphysical body animation changed during import")
        error = audit["max_world_position_error"]
        require(math.isfinite(error) and error < a.tolerance, "Physics world import does not align")
        require(audit["no_blender_physics"] is True, "Blender physics must not run a second solve")
        report.update(body_action_unchanged=True, max_import_world_error_m=error)
    result = json.dumps(report, ensure_ascii=False, indent=2)
    if a.output:
        Path(a.output).write_text(result + "\n", encoding="utf8")
    print(result)


if __name__ == "__main__":
    main()
