# Carda Engine Mod Installer for ToLiss A319 / A321 v1.1r1

Installer script for the [Carda engine mods](https://forum.thresholdx.net/profile/3927-cardajowol/) on the ToLiss A319 and A321 (CEO and NEO) in X-Plane. Handles all `.acf` and `.obj` edits so you don't have to do them by hand.

## What the installer does

**TL;DR: Everything. You only need to download the engine objects, copy them in, and run this script.** Specifically though, it:

1. **Neutralises stock engine ANIM_hide directives** in `objects/engines.obj` and `objects/blades.obj` (replaces `anim/CFM` / `anim/IAE` with `none`).
2. **Patches Carda engine OBJ datarefs** ([@Chris E](https://forums.x-plane.org/profile/640915-chris-e/)'s fixes):
   - Rewrites N1 speed datarefs from `sim/flightmodel/engine/ENGN_N1_` to `AirbusFBW/anim/ENGN1Speed`.
   - Rewrites fan rotation datarefs from `sim/flightmodel2/engines/engine_rotation_angle_deg` to `AirbusFBW/EngineFanRotation_deg` (LEAP & PW engines).
   - Corrects the LEAP blade rotation Y-axis direction (flips `-1` → `1`).
3. **Edits all `.acf` files** - removes the stock engine objects and adds the 17 Carda replacement objects with the correct positions, shadow modes, and kill datarefs.

Backups (`.bak`) are created automatically before any file is modified.

## Step 1 - Download the Carda engine mods

Download the engine mods from the Threshold Forums:

| Engine | Link |
| ------ | ---- |
| CFM LEAP-1A | https://forum.thresholdx.net/files/file/620-cfm-leap-1a-engine-mod/ |
| PW1100G | https://forum.thresholdx.net/files/file/652-pratt-whitney-1100-g-engine-mod/ |
| CFM56-5B/5A | https://forum.thresholdx.net/files/file/1827-cfm56-5b5a-engine-mod-for-ff320-toliss-a319a321/ |
| IAE V2500 | https://forum.thresholdx.net/files/file/1194-iae-v2500-engine-mod-for-ff320-toliss-a319a321/ |

Extract each zip. You'll get a folder per mod with a structure like:

```txt
IAE-V2500-Toliss321-1.1/
├── A321 Base Folder/
│   └── objects/          ← you need this
│       ├── particles/
│       └── V2500/
├── Liveries/
│   ├── American/objects/
│   ├── BA/objects/
│   └── …
└── MANUAL.pdf
```

## Step 2 - Copy engine files into the aircraft folder

For each of the extracted mods:

1. Open the mod's **base folder** (e.g. `A321 Base Folder/` or `A319 Base Folder/`).
2. Copy (merge) the `objects/` folder inside it into your ToLiss aircraft directory so the engine subfolders end up at:

   ```txt
   Airbus A321 (ToLiss)/objects/CFM56/
   Airbus A321 (ToLiss)/objects/V2500/
   Airbus A321 (ToLiss)/objects/LEAP Engines/
   Airbus A321 (ToLiss)/objects/PW Engines/
   ```

3. *(Optional)* If you want livery-specific engine textures, copy each livery's `objects/` folder into the matching livery folder under the aircraft directory.

Repeat for all four engine packs (LEAP-1A, PW1100G, CFM56, V2500).

## Step 3 - Run the installer

### Option A: Pre-built binary (no Python needed)

Download the binary for your OS from the [Releases](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/) page:

| Platform | A319 | A321 |
| -------- | ---- | ---- |
| Windows x64 | [`install-carda-a319-windows-x64.exe`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-windows-x64.exe) | [`install-carda-a321-windows-x64.exe`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-windows-x64.exe) |
| Windows ARM64 | [`install-carda-a319-windows-arm64.exe`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-windows-arm64.exe) | [`install-carda-a321-windows-arm64.exe`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-windows-arm64.exe) |
| macOS Apple Silicon | [`install-carda-a319-macos-arm64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-macos-arm64) | [`install-carda-a321-macos-arm64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-macos-arm64) |
| macOS Intel | [`install-carda-a319-macos-x64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-macos-x64) | [`install-carda-a321-macos-x64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-macos-x64) |
| Linux x64 | [`install-carda-a319-linux-x64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-linux-x64) | [`install-carda-a321-linux-x64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-linux-x64) |
| Linux ARM64 | [`install-carda-a319-linux-arm64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a319-linux-arm64) | [`install-carda-a321-linux-arm64`](https://github.com/iy4vet/xplane-toliss-carda-installer/releases/latest/download/install-carda-a321-linux-arm64) |

Place the binary inside your aircraft folder. On Windows, just double-click the `.exe`. On macOS/Linux you may need to make it executable first:

```bash
# Example (A321, Linux):
cd "/path/to/Airbus A321 (ToLiss)"
chmod +x install-carda-a321-linux-x64
./install-carda-a321-linux-x64
```

### Option B: Run with Python

Requires Python 3.10+. No external dependencies.

Place the appropriate `.py` script in your aircraft folder and run:

```bash
cd "/path/to/Airbus A321 (ToLiss)"
python install_carda_a321.py
```

Or point to the aircraft folder from anywhere:

```bash
python install_carda_a321.py --aircraft-dir "/path/to/Airbus A321 (ToLiss)"
```

Use `install_carda_a319.py` for the A319 and `install_carda_a321.py` for the A321.

## Credits and Licensing

This project is licensed under the GNU GPL v2.

Any contributions (features or bugfixes) are very welcome :grin:. [Here's the project GitHub](https://github.com/iy4vet/xplane-toliss-carda-installer).

Feel free to message me on Discord - my username is `iy4vet`. I'm also present in the X-Plane Community and Official servers.

A huge thank-you to these awesome people:

- [Carda (Threshold Forums)](https://forum.thresholdx.net/profile/3927-cardajowol/) - original engine mod models and textures.
- [@Chris E](https://forums.x-plane.org/profile/640915-chris-e/) - dataref fixes for ToLiss compatibility (original [A321 fix](https://forums.x-plane.org/files/file/89257-carda-engines-mod-fix-for-toliss-a321/) and [A319 fix](https://forums.x-plane.org/files/file/93205-carda-engines-mod-fix-for-toliss-a319/)). With their permission, I've included their fixes in this script. They were: correcting N1 speed and fan rotation datarefs from stock X-Plane paths to the AirbusFBW equivalents used by ToLiss, and fixing the LEAP blade rotation axis direction.
- [alexvor20](https://github.com/alexvor20) - CEO-only install option.

## Changelog

- **1.1r1** - Add: CEO-only install option
- **1.0r1** - Initial release

## What's Planned

The most obvious one - the [A320neo](https://toliss.com/pages/a320-neo) and [A320ceo](https://toliss.com/pages/a320-ceo). There's a good chance the A319 version works for the A320, but I can't test it myself.

I'd like to also develop scripts for the [A340-600](https://toliss.com/pages/a340-600) and [A330-900 neo](https://toliss.com/pages/a330-900) in the future.

Doing non-ToLiss Aircraft is also in the cards! :grin:

If there's anything you'd like to see added, send me a message or create a pull request on GitHub!
