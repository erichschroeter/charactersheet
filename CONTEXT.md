# Character Sheet Context

A fast, automated form-filling tool to compile and style the official 3-page D&D 5e fillable character sheet PDF from YAML configuration.

## Language

**Character Configuration**:
A structured YAML file defining the character's properties, stats, traits, features, skills, and spells.
_Avoid_: character YAML, stats file

**Form-Fillable PDF**:
The official 3-page interactive PDF template containing form widgets.
_Avoid_: PDF template, sheet template

**Proficiency Checkbox**:
A form widget representing proficiency in a specific skill or saving throw on Page 1.
_Avoid_: skill bubble, save checkbox

**Spell Prep Checkbox**:
A checkbox next to a spell on Page 3 indicating whether the spell is prepared.
_Avoid_: spell bubble, prepared check

**Baking/Flattening**:
The process of rendering interactive form fields into static drawing content, preventing future edits and fixing custom font display.
_Avoid_: locking, printing, freezing

## Relationships

- A **Character Configuration** is merged into a **Form-Fillable PDF**
- A **Character Configuration** specifies **Proficiency Checkboxes** to check on Page 1
- A **Character Configuration** maps spells to specific slots and toggles **Spell Prep Checkboxes** on Page 3
- The process outputs a final filled PDF, which may undergo **Baking/Flattening**
