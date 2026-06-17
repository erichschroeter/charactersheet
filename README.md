# D&D 5E Styled Character Sheet Generator

A fast, automated form-filling tool to compile and style the official 3-page D&D 5e fillable character sheet PDF using Python and `uv`.

## Quick Start

You do not need to manually install Python packages. Simply run the generator with `uv`:

```bash
uv run --with pymupdf --with pyyaml fill_sheet.py
```

This compiles `character.yaml` into **`filled_character_sheet.pdf`**.

---

## Configuration (`character.yaml`)

Edit your character details directly in `character.yaml`. It supports several automated layout and typography features:

### 1. Global Typography
Set your theme fonts, sizes, and colors globally in the `styling` block:
```yaml
styling:
  font: "HeBo"                # Helv (Helvetica), HeBo (Bold), TiRo (Times), Cour (Courier)
  font_size: 10
  text_color: [0.0, 0.0, 0.0] # RGB values [0.0 to 1.0]
  fill_checkbox_style: "circle" # "circle" (filled bubbles) or "checkmark" (default)
```

### 2. Custom Per-Field Overrides
To make text fit better in small fields or header names pop, structure any field as an object instead of a string:
```yaml
Feat+Traits:
  value: "Compact feature details..."
  font: "HeBo"
  font_size: 7.5  # Keeps long blocks from overflowing
```

### 3. Automatic Saving Throw & Skill Proficiencies
Simply tag any saving throw or skill with `proficient: true`. The script automatically checks/fills the correct bubble next to that modifier on Page 1:
```yaml
skills:
  Arcana:
    value: "+3"
    proficient: true # Automatically checks the Arcana bubble
```

### 4. Automated Spell & Cantrip Mapping (Page 3)
Add your spellbook naturally under spell levels `0` through `9`. The script automatically places them in sequential slots on Page 3 and checks the "Prepared" bubble if specified:
```yaml
spells:
  0: # Cantrips
    - "Fire Bolt"
    - "Guidance"
  1: # Level 1
    - name: "Cure Wounds"
      prepared: true # Automatically checks the "Prepared" bubble next to it
    - name: "Identify"
      prepared: false
```

---

## Technical Features

* **Pristine Vector Fills:** When `fill_checkbox_style: "circle"` is active, the script draws mathematically perfect solid circles directly onto the PDF canvas, ensuring crisp prints across all PDF readers.
* **Layout Agnostic:** Custom fields like Page 2 physical details (`Age`, `Height`, `Weight`) or Page 1 weapons (`Wpn Name`, etc.) are mapped dynamically. Adding new keys to the YAML automatically matches them to their respective PDF form fields.
