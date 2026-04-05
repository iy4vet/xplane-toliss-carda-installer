#!/usr/bin/env python3
"""
Carda Engine Mod ACF/OBJ Editor for ToLiss A321
===============================================

An installer script that edits .acf and .obj files to install Carda Mod.
Run from the same folder as the *.acf files - i.e. the ToLiss A321
aircraft root folder.

What it does:
  1. Edits engines.obj & blades.obj in objects/ to neutralise stock
     ANIM_hide directives (anim/CFM and anim/IAE → none).
  2. Applies Toliss Carda Fix dataref patches to the 14 Carda engine OBJ
     files: rewrites N1 speed and fan-rotation datarefs from stock X-Plane
     paths to AirbusFBW equivalents, and corrects the LEAP blade rotation
     axis direction.
  3. Edits ALL *.acf files: removes 5 stock engine objects and adds the
     17 Carda replacement objects with correct positions, shadow modes,
     and kill datarefs.

What it does NOT do:
  - Copy base engine model/texture files from the Carda mod folders.
  - Copy livery-specific engine textures.

Usage:
    cd "Airbus A321 (ToLiss)"
    python ../install_carda_minimal.py
    # or:
    python install_carda_minimal.py --aircraft-dir "/path/to/Airbus A321 (ToLiss)"
"""

import argparse
import re
import shutil
import struct
import sys
from dataclasses import dataclass
from pathlib import Path


# ─── Constants ────────────────────────────────────────────────────────────────

FLAGS_NONE = 0
FLAGS_PREFILL = 4
FLAGS_ALL_VIEWS_HIRES = 24

STOCK_OBJECTS_TO_REMOVE = [
    "engines.obj",
    "blades.obj",
    "neo.obj",
    "LEAP1A.obj",
    "leapfast.obj",
]

# Carda engine OBJ files (relative to objects/) that need Toliss dataref fixes.
CARDA_ENGINE_OBJS = [
    "CFM56/cfm56_l_engine.obj",
    "CFM56/cfm56_r_engine.obj",
    "CFM56/cfm56_n1.obj",
    "V2500/iae_l_engine.obj",
    "V2500/iae_r_engine.obj",
    "V2500/iae_n1.obj",
    "LEAP Engines/LEAP_L_Engine.obj",
    "LEAP Engines/LEAP_R_Engine.obj",
    "LEAP Engines/LEAP_N1_L.obj",
    "LEAP Engines/LEAP_N1_R.obj",
    "PW Engines/PW_L_Engine.obj",
    "PW Engines/PW_R_Engine.obj",
    "PW Engines/PW_N1_L.obj",
    "PW Engines/PW_N1_R.obj",
]

# LEAP L/R engine files that also need the blade rotation Y-axis direction fix.
_LEAP_BLADE_FIX_OBJS = {
    "LEAP Engines/LEAP_L_Engine.obj",
    "LEAP Engines/LEAP_R_Engine.obj",
}


# ─── Data Classes ─────────────────────────────────────────────────────────────


@dataclass
class ACFObject:
    """A Misc Object entry to add to the ACF."""

    file_stl: str
    flags: int = 0
    hide_dataref: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    body: int = -1
    gear: int = -1
    wing: int = -1
    phi_ref: float = 0.0
    psi_ref: float = 0.0
    the_ref: float = 0.0
    is_internal: int = 0
    steers_with_gear: int = 0


# ─── Engine Definitions ──────────────────────────────────────────────────────


def _build_all_carda_objects() -> list[ACFObject]:
    """Return the full list of 17 Carda engine objects for a combined install."""

    # CFM56-5B (CEO) - kill=anim/NEO, pos=(0, 0.4, 20.7)
    cfm = [
        ACFObject(
            "CFM56/cfm56_l_engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/NEO",
            0.0,
            0.4,
            20.7,
        ),
        ACFObject(
            "CFM56/cfm56_r_engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/NEO",
            0.0,
            0.4,
            20.7,
        ),
        ACFObject("CFM56/cfm56_n1.obj", FLAGS_PREFILL, "anim/NEO", 0.0, 0.4, 20.7),
        # CFM-Particles.obj intentionally omitted (IAE particles used for combined install)
    ]

    # IAE V2500 (CEO) - kill=anim/NEO, pos=(0, 0.4, 20.7)
    iae = [
        ACFObject(
            "V2500/iae_l_engine.obj", FLAGS_ALL_VIEWS_HIRES, "anim/NEO", 0.0, 0.4, 20.7
        ),
        ACFObject(
            "V2500/iae_r_engine.obj", FLAGS_ALL_VIEWS_HIRES, "anim/NEO", 0.0, 0.4, 20.7
        ),
        ACFObject("V2500/iae_n1.obj", FLAGS_PREFILL, "anim/NEO", 0.0, 0.4, 20.7),
        ACFObject(
            "V2500/particles/IAE-Particles.obj",
            FLAGS_PREFILL,
            "anim/NEO",
            0.0,
            0.0,
            0.0,
        ),
    ]

    # LEAP-1A (NEO) - kill=anim/LEAP/kill
    # Manual: LONG=41.70 LAT=-19.00 VERT=-6.60 → ACF: x=LAT, y=VERT, z=LONG
    #   L: x=-19.0, y=-6.6, z=41.7    R: x=19.0, y=-6.6, z=41.7
    leap = [
        ACFObject(
            "LEAP Engines/particles/LEAP-Particles.obj",
            FLAGS_NONE,
            "anim/LEAP/kill",
            0.0,
            0.0,
            0.0,
        ),
        ACFObject(
            "LEAP Engines/LEAP_L_Engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/LEAP/kill",
            -19.0,
            -6.6,
            41.7,
        ),
        ACFObject(
            "LEAP Engines/LEAP_N1_L.obj",
            FLAGS_PREFILL,
            "anim/LEAP/kill",
            -19.0,
            -6.6,
            41.7,
        ),
        ACFObject(
            "LEAP Engines/LEAP_R_Engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/LEAP/kill",
            19.0,
            -6.6,
            41.7,
        ),
        ACFObject(
            "LEAP Engines/LEAP_N1_R.obj",
            FLAGS_PREFILL,
            "anim/LEAP/kill",
            19.0,
            -6.6,
            41.7,
        ),
    ]

    # PW1100G (NEO) - kill=anim/NEO/kill, same positions as LEAP
    pw = [
        ACFObject(
            "PW Engines/particles/PW-Particles.obj",
            FLAGS_NONE,
            "anim/NEO/kill",
            0.0,
            0.0,
            0.0,
        ),
        ACFObject(
            "PW Engines/PW_L_Engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/NEO/kill",
            -19.0,
            -6.6,
            41.7,
        ),
        ACFObject(
            "PW Engines/PW_N1_L.obj", FLAGS_PREFILL, "anim/NEO/kill", -19.0, -6.6, 41.7
        ),
        ACFObject(
            "PW Engines/PW_R_Engine.obj",
            FLAGS_ALL_VIEWS_HIRES,
            "anim/NEO/kill",
            19.0,
            -6.6,
            41.7,
        ),
        ACFObject(
            "PW Engines/PW_N1_R.obj", FLAGS_PREFILL, "anim/NEO/kill", 19.0, -6.6, 41.7
        ),
    ]

    return cfm + iae + leap + pw


ALL_CARDA_OBJECTS = _build_all_carda_objects()


# ─── Helpers ──────────────────────────────────────────────────────────────────


def format_float32(val: float) -> str:
    """Format a float in X-Plane's single-precision 9-decimal-place style."""
    packed = struct.pack("f", val)
    unpacked = struct.unpack("f", packed)[0]
    return f"{unpacked:.9f}"


# ─── ACF Editor ───────────────────────────────────────────────────────────────


class ACFEditor:
    """Reads, modifies, and writes X-Plane .acf property files."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._header_lines: list[str] = []
        self._properties: dict[str, str] = {}
        self._footer_lines: list[str] = []
        self._read()

    def _read(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_properties = False
        past_properties = False

        for line in lines:
            stripped = line.rstrip("\n\r")
            if stripped.startswith("P "):
                in_properties = True
                past_properties = False
                parts = stripped.split(" ", 2)
                key = parts[1]
                value = parts[2] if len(parts) > 2 else ""
                self._properties[key] = value
            elif in_properties:
                past_properties = True
                in_properties = False
                self._footer_lines.append(line)
            elif past_properties:
                self._footer_lines.append(line)
            else:
                self._header_lines.append(line)

    def save(self, backup: bool = True):
        if backup:
            bak = self.filepath.with_suffix(self.filepath.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(self.filepath, bak)

        sorted_keys = sorted(self._properties.keys())
        with open(self.filepath, "w", encoding="utf-8", newline="\n") as f:
            for line in self._header_lines:
                f.write(line)
            for key in sorted_keys:
                f.write(f"P {key} {self._properties[key]}\n")
            for line in self._footer_lines:
                f.write(line)

    def get_obja_entries(self) -> dict[int, dict[str, str]]:
        entries: dict[int, dict[str, str]] = {}
        for key, value in self._properties.items():
            if key.startswith("_obja/") and key != "_obja/count":
                parts = key.split("/")
                idx = int(parts[1])
                prop = "/".join(parts[2:])
                entries.setdefault(idx, {})[prop] = value
        return entries

    def get_obja_count(self) -> int:
        return int(self._properties.get("_obja/count", "0"))

    def has_object_by_filename(self, filename: str) -> bool:
        for key, value in self._properties.items():
            if key.endswith("/_v10_att_file_stl") and value == filename:
                return True
        return False

    def remove_and_add_objects(
        self,
        filenames_to_remove: list[str],
        objects_to_add: list[ACFObject],
    ) -> tuple[list[str], list[str]]:
        """Remove stock objects and add Carda objects, re-indexing as needed."""
        entries = self.get_obja_entries()

        indices_to_remove: set[int] = set()
        removed_names: list[str] = []
        for idx, props in entries.items():
            stl = props.get("_v10_att_file_stl", "")
            if stl in filenames_to_remove:
                indices_to_remove.add(idx)
                removed_names.append(stl)

        filenames_to_remove_set = set(filenames_to_remove)
        already_present: list[str] = []
        filtered_add: list[ACFObject] = []
        for obj in objects_to_add:
            if (
                obj.file_stl not in filenames_to_remove_set
                and self.has_object_by_filename(obj.file_stl)
            ):
                already_present.append(obj.file_stl)
            else:
                filtered_add.append(obj)

        if not indices_to_remove and not filtered_add:
            return removed_names, already_present

        # Remove old keys
        keys_to_delete = [
            k for k in self._properties if k.startswith("_obja/") and k != "_obja/count"
        ]
        for k in keys_to_delete:
            del self._properties[k]

        # Renumber survivors
        surviving = [
            (idx, props)
            for idx, props in sorted(entries.items())
            if idx not in indices_to_remove
        ]
        new_entries: dict[int, dict[str, str]] = {}
        for new_idx, (_old_idx, props) in enumerate(surviving):
            new_entries[new_idx] = props

        # Append new objects
        next_idx = len(new_entries)
        for obj in filtered_add:
            new_entries[next_idx] = self._acf_obj_to_props(obj)
            next_idx += 1

        # Write back
        for idx, props in sorted(new_entries.items()):
            for prop_name, value in sorted(props.items()):
                self._properties[f"_obja/{idx}/{prop_name}"] = value
        self._properties["_obja/count"] = str(len(new_entries))

        return removed_names, already_present

    @staticmethod
    def _acf_obj_to_props(obj: ACFObject) -> dict[str, str]:
        props: dict[str, str] = {
            "_obj_flags": str(obj.flags),
            "_v10_att_body": str(obj.body),
            "_v10_att_file_stl": obj.file_stl,
            "_v10_att_gear": str(obj.gear),
            "_v10_att_phi_ref": format_float32(obj.phi_ref),
            "_v10_att_psi_ref": format_float32(obj.psi_ref),
            "_v10_att_the_ref": format_float32(obj.the_ref),
            "_v10_att_wing": str(obj.wing),
            "_v10_att_x_acf_prt_ref": format_float32(obj.x),
            "_v10_att_y_acf_prt_ref": format_float32(obj.y),
            "_v10_att_z_acf_prt_ref": format_float32(obj.z),
            "_v10_is_internal": str(obj.is_internal),
            "_v10_steers_with_gear": str(obj.steers_with_gear),
        }
        if obj.hide_dataref:
            props["_obj_hide_dataref"] = obj.hide_dataref
        return props


# ─── OBJ Editor ───────────────────────────────────────────────────────────────


class OBJEditor:
    """Neutralises stock ANIM_hide directives and applies Carda dataref fixes."""

    _PATTERN = re.compile(r"(ANIM_hide\s+[\d.]+\s+[\d.]+\s+)anim/(CFM|IAE)\b")

    # Matches the LEAP blade ANIM_rotate line whose Y-axis is -1 and that is
    # followed (on the next line, after leading whitespace) by another ANIM
    # directive (ANIM_begin or ANIM_rotate_end) - i.e. the N1-speed-dependent
    # spinner block, NOT the static-geometry blocks (which are followed by TRIS).
    _BLADE_ROTATION_FIX = re.compile(
        r"(ANIM_rotate[ \t]+0\.000000[ \t]+)-1"
        r"(\.000000[ \t]+0\.000000[ \t]+0\.000000[ \t]+1\.000000"
        r"[ \t]+0\.000000[ \t]+1\.000000[ \t]+anim/blade/[LR]/1/angle"
        r"[ \t]*\n[ \t]*)(?=ANIM)"
    )

    @classmethod
    def neutralise(cls, filepath: Path, dry_run: bool = False) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        new_content, count = cls._PATTERN.subn(r"\1none", content)

        if count > 0 and not dry_run:
            bak = filepath.with_suffix(filepath.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(filepath, bak)
            with open(filepath, "w", encoding="utf-8", newline="\n") as f:
                f.write(new_content)

        return count

    @classmethod
    def is_already_neutralised(cls, filepath: Path) -> bool:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return cls._PATTERN.search(content) is None

    @classmethod
    def apply_carda_fixes(
        cls, filepath: Path, rel_path: str, dry_run: bool = False
    ) -> int:
        """Apply Toliss Carda Fix dataref replacements to a Carda engine OBJ.

        Three fixes:
          1. N1 speed dataref → AirbusFBW/anim/ENGN1Speed  (all engine OBJs)
          2. Fan rotation dataref → AirbusFBW/EngineFanRotation_deg  (any file
             containing it - effectively LEAP/PW N1 files)
          3. LEAP blade rotation Y-axis direction  (LEAP L/R engine files only)
        """
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original = content
        count = 0

        # Fix 1: N1 speed dataref
        for n in ("0", "1"):
            old = f"sim/flightmodel/engine/ENGN_N1_[{n}]"
            new = f"AirbusFBW/anim/ENGN1Speed[{n}]"
            c = content.count(old)
            if c:
                content = content.replace(old, new)
                count += c

        # Fix 2: Fan rotation dataref
        for n in ("0", "1"):
            old = f"sim/flightmodel2/engines/engine_rotation_angle_deg[{n}]"
            new = f"AirbusFBW/EngineFanRotation_deg[{n}]"
            c = content.count(old)
            if c:
                content = content.replace(old, new)
                count += c

        # Fix 3: LEAP blade rotation axis direction
        if rel_path in _LEAP_BLADE_FIX_OBJS:
            content, c = cls._BLADE_ROTATION_FIX.subn(r"\g<1>1\2", content)
            count += c

        if content != original and not dry_run:
            bak = filepath.with_suffix(filepath.suffix + ".bak")
            if not bak.exists():
                shutil.copy2(filepath, bak)
            with open(filepath, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)

        return count

    @classmethod
    def needs_carda_fixes(cls, filepath: Path, rel_path: str) -> bool:
        """Check if a Carda engine OBJ still has stock datarefs."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if "sim/flightmodel/engine/ENGN_N1_[" in content:
            return True
        if "sim/flightmodel2/engines/engine_rotation_angle_deg[" in content:
            return True
        if rel_path in _LEAP_BLADE_FIX_OBJS and cls._BLADE_ROTATION_FIX.search(content):
            return True
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Carda ACF/OBJ editor - run from the ToLiss A321 folder"
    )
    parser.add_argument(
        "--aircraft-dir",
        type=Path,
        default=Path.cwd(),
        help="Path to the ToLiss A321 aircraft folder (default: current directory)",
    )
    parser.add_argument(
        "--engines",
        type=int,
        choices=[1, 2],
        default=None,
        help="Engine selection: 1=CFM+IAE only, 2=All (skips interactive prompt)",
    )
    args = parser.parse_args()
    aircraft_dir: Path = args.aircraft_dir.resolve()

    print("=" * 60)
    print(" Carda Engine Mod - ACF/OBJ Editor (A321) v1.1r1")
    print("=" * 60)

    # ── Engine family selection ──
    if args.engines is not None:
        selection = args.engines
    else:
        print("\nWhich engines do you want to install?")
        print("  1 - CFM56 + IAE only  (CEO)")
        print("  2 - All engines       (CEO + NEO)")
        while True:
            raw = input("\nEnter 1 or 2: ").strip()
            if raw in ("1", "2"):
                selection = int(raw)
                break
            print("  Invalid choice. Please enter 1 or 2.")

    if selection == 1:
        label = "CFM56 + IAE only (CEO)"
        active_engine_objs = [p for p in CARDA_ENGINE_OBJS if not p.startswith(("LEAP", "PW"))]
        active_carda_objects = [o for o in ALL_CARDA_OBJECTS if not o.file_stl.startswith(("LEAP", "PW"))]
    else:
        label = "All engines (CEO + NEO)"
        active_engine_objs = CARDA_ENGINE_OBJS
        active_carda_objects = ALL_CARDA_OBJECTS

    print(f"\nEngine selection: {label}")

    # Validate: must contain *.acf files
    acf_files = sorted(aircraft_dir.glob("*.acf"))
    if not acf_files:
        print(f"\nERROR: No .acf files found in {aircraft_dir}")
        print("Run this script from the ToLiss A321 aircraft folder,")
        print("or use --aircraft-dir to specify the path.")
        sys.exit(1)

    print(f"\nAircraft folder: {aircraft_dir}")
    print(f"Found {len(acf_files)} ACF file(s): {', '.join(f.name for f in acf_files)}")

    # ── Step 1: OBJ edits ──
    obj_dir = aircraft_dir / "objects"
    if obj_dir.is_dir():
        print("\n── OBJ File Editing ───────────────────────────────────────")
        for obj_name in ("engines.obj", "blades.obj"):
            obj_path = obj_dir / obj_name
            if not obj_path.exists():
                print(f"  {obj_name}: Not found (skipped)")
                continue
            count = OBJEditor.neutralise(obj_path)
            if count:
                print(f"  {obj_name}: Replaced {count} ANIM_hide dataref(s) → 'none'")
            else:
                print(f"  {obj_name}: OK (already neutralised)")

        # ── Step 2: Carda engine OBJ fixes ──
        print("\n── Carda Engine OBJ Fixes ─────────────────────────────────")
        for rel_path in active_engine_objs:
            obj_path = obj_dir / rel_path
            if not obj_path.exists():
                print(f"  {rel_path}: Not found (skipped)")
                continue
            count = OBJEditor.apply_carda_fixes(obj_path, rel_path)
            if count:
                print(f"  {rel_path}: Applied {count} dataref fix(es)")
            else:
                print(f"  {rel_path}: OK (already fixed)")
    else:
        print("\n  WARNING: objects/ folder not found - skipping OBJ edits")

    # ── Step 3: ACF edits ──
    print("\n── ACF File Editing ───────────────────────────────────────")

    # Always purge all known Carda filenames so switching between options
    # on a re-run doesn't leave stale objects from a previous install.
    all_carda_filenames = [obj.file_stl for obj in ALL_CARDA_OBJECTS]
    active_carda_filenames = {o.file_stl for o in active_carda_objects}

    for acf_path in acf_files:
        print(f"\n  {acf_path.name}:")
        editor = ACFEditor(acf_path)

        removed, _already = editor.remove_and_add_objects(
            filenames_to_remove=STOCK_OBJECTS_TO_REMOVE + all_carda_filenames,
            objects_to_add=active_carda_objects,
        )
        stock_removed = [n for n in removed if n in STOCK_OBJECTS_TO_REMOVE]
        carda_refreshed = [n for n in removed if n in active_carda_filenames]
        stale_removed = [n for n in removed if n in all_carda_filenames and n not in active_carda_filenames]
        if stock_removed:
            print(f"    Removed stock: {', '.join(stock_removed)}")
        if stale_removed:
            print(f"    Cleaned up {len(stale_removed)} stale object(s) from previous install")
        if carda_refreshed:
            print(f"    Refreshed {len(carda_refreshed)} existing Carda object(s)")
        else:
            print(f"    Added {len(active_carda_objects)} Carda object(s)")
        print(f"    Total object count: {editor.get_obja_count()}")
        editor.save(backup=True)
        print(f"    Saved (backup: {acf_path.name}.bak)")

    print("\n" + "=" * 60)
    print(" Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
