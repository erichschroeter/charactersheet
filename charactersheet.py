#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pymupdf>=1.22.0",
#     "pyyaml>=6.0",
# ]
# ///

"""
D&D 5E Character Sheet CLI Tool.
Compiles and styles the official fillable PDF sheet from a YAML configuration or
lists its interactive form fields.
"""

import argparse
import datetime
import logging
import os
import sys
from typing import Any, Dict, List
import yaml

try:
    import pymupdf as fitz  # type: ignore
except ImportError:
    import fitz  # type: ignore


# ------------------------------------------------------------------------------
# Monkey-Patch: Override PyMuPDF's hardcoded font filter to allow custom fonts
# ------------------------------------------------------------------------------
def custom_adjust_font(self: Any) -> None:
    """
    Overrides PyMuPDF's hardcoded font filter.
    Maps common aliases to PDF base-14 names and permits custom embedded fonts
    to pass through without being silently reset to 'Helv'.
    """
    if not self.text_font:
        self.text_font = "Helv"
        return

    aliases = {
        "courier": "Cour",
        "courier new": "Cour",
        "courier-bold": "CoBo",
        "courier bold": "CoBo",
        "helvetica": "Helv",
        "helvetica-bold": "HeBo",
        "times": "TiRo",
        "times roman": "TiRo",
        "times-roman": "TiRo",
    }

    lowered = str(self.text_font).lower().strip()
    if lowered in aliases:
        self.text_font = aliases[lowered]
        return

    # For custom embedded fonts (like CascadiaMonoNF), allow them to pass through!
    return


# Apply the patch globally
fitz.Widget._adjust_font = custom_adjust_font


# ------------------------------------------------------------------------------
# Mappings & Configurations
# ------------------------------------------------------------------------------

# Map saving throw and skill field names to their corresponding PDF proficiency checkbox names
PROFICIENCY_CHECKBOXES: Dict[str, str] = {
    "ST Strength": "Check Box 11",
    "ST Dexterity": "Check Box 18",
    "ST Constitution": "Check Box 19",
    "ST Intelligence": "Check Box 20",
    "ST Wisdom": "Check Box 21",
    "ST Charisma": "Check Box 22",
    "Acrobatics": "Check Box 23",
    "Animal": "Check Box 24",
    "Arcana": "Check Box 25",
    "Athletics": "Check Box 26",
    "Deception": "Check Box 27",
    "History": "Check Box 28",
    "Insight": "Check Box 29",
    "Intimidation": "Check Box 30",
    "Investigation": "Check Box 31",
    "Medicine": "Check Box 32",
    "Nature": "Check Box 33",
    "Perception": "Check Box 34",
    "Performance": "Check Box 35",
    "Persuasion": "Check Box 36",
    "Religion": "Check Box 37",
    "SleightofHand": "Check Box 38",
    "Stealth": "Check Box 39",
    "Survival": "Check Box 40",
}

# Sequential list of text field names per spell level on page 3
SPELL_FIELDS_BY_LEVEL: Dict[int, List[str]] = {
    0: [
        "Spells 1014",
        "Spells 1016",
        "Spells 1017",
        "Spells 1018",
        "Spells 1019",
        "Spells 1020",
        "Spells 1021",
        "Spells 1022",
    ],
    1: [
        "Spells 1015",
        "Spells 1023",
        "Spells 1024",
        "Spells 1025",
        "Spells 1026",
        "Spells 1027",
        "Spells 1028",
        "Spells 1029",
        "Spells 1030",
        "Spells 1031",
        "Spells 1032",
        "Spells 1033",
    ],
    2: [
        "Spells 1046",
        "Spells 1034",
        "Spells 1035",
        "Spells 1036",
        "Spells 1037",
        "Spells 1038",
        "Spells 1039",
        "Spells 1040",
        "Spells 1041",
        "Spells 1042",
        "Spells 1043",
        "Spells 1044",
        "Spells 1045",
    ],
    3: [
        "Spells 1048",
        "Spells 1047",
        "Spells 1049",
        "Spells 1050",
        "Spells 1051",
        "Spells 1052",
        "Spells 1053",
        "Spells 1054",
        "Spells 1055",
        "Spells 1056",
        "Spells 1057",
        "Spells 1058",
        "Spells 1059",
    ],
    4: [
        "Spells 1061",
        "Spells 1060",
        "Spells 1062",
        "Spells 1063",
        "Spells 1064",
        "Spells 1065",
        "Spells 1066",
        "Spells 1067",
        "Spells 1068",
        "Spells 1069",
        "Spells 1070",
        "Spells 1071",
        "Spells 1072",
    ],
    5: [
        "Spells 1074",
        "Spells 1073",
        "Spells 1075",
        "Spells 1076",
        "Spells 1077",
        "Spells 1078",
        "Spells 1079",
        "Spells 1080",
        "Spells 1081",
    ],
    6: [
        "Spells 1083",
        "Spells 1082",
        "Spells 1084",
        "Spells 1085",
        "Spells 1086",
        "Spells 1087",
        "Spells 1088",
        "Spells 1089",
        "Spells 1090",
    ],
    7: [
        "Spells 1092",
        "Spells 1091",
        "Spells 1093",
        "Spells 1094",
        "Spells 1095",
        "Spells 1096",
        "Spells 1097",
        "Spells 1098",
        "Spells 1099",
    ],
    8: [
        "Spells 10101",
        "Spells 10100",
        "Spells 10102",
        "Spells 10103",
        "Spells 10104",
        "Spells 10105",
        "Spells 10106",
    ],
    9: [
        "Spells 10108",
        "Spells 10107",
        "Spells 10109",
        "Spells 101010",
        "Spells 101011",
        "Spells 101012",
        "Spells 101013",
    ],
}

# Map spell text field name to its corresponding preparation checkbox name on page 3
SPELL_PREP_CHECKBOXES: Dict[str, str] = {
    "Spells 1015": "Check Box 251",
    "Spells 1023": "Check Box 309",
    "Spells 1024": "Check Box 3010",
    "Spells 1025": "Check Box 3011",
    "Spells 1026": "Check Box 3012",
    "Spells 1027": "Check Box 3013",
    "Spells 1028": "Check Box 3014",
    "Spells 1029": "Check Box 3015",
    "Spells 1030": "Check Box 3016",
    "Spells 1031": "Check Box 3017",
    "Spells 1032": "Check Box 3018",
    "Spells 1033": "Check Box 3019",
    "Spells 1034": "Check Box 310",
    "Spells 1035": "Check Box 3020",
    "Spells 1036": "Check Box 3021",
    "Spells 1037": "Check Box 3022",
    "Spells 1038": "Check Box 3023",
    "Spells 1039": "Check Box 3024",
    "Spells 1040": "Check Box 3025",
    "Spells 1041": "Check Box 3026",
    "Spells 1042": "Check Box 3027",
    "Spells 1043": "Check Box 3028",
    "Spells 1044": "Check Box 3029",
    "Spells 1045": "Check Box 3030",
    "Spells 1046": "Check Box 313",
    "Spells 1047": "Check Box 314",
    "Spells 1048": "Check Box 315",
    "Spells 1049": "Check Box 3031",
    "Spells 1050": "Check Box 3032",
    "Spells 1051": "Check Box 3033",
    "Spells 1052": "Check Box 3034",
    "Spells 1053": "Check Box 3035",
    "Spells 1054": "Check Box 3036",
    "Spells 1055": "Check Box 3037",
    "Spells 1056": "Check Box 3038",
    "Spells 1057": "Check Box 3039",
    "Spells 1058": "Check Box 3040",
    "Spells 1059": "Check Box 3041",
    "Spells 1060": "Check Box 316",
    "Spells 1061": "Check Box 317",
    "Spells 1062": "Check Box 3042",
    "Spells 1063": "Check Box 3043",
    "Spells 1064": "Check Box 3044",
    "Spells 1065": "Check Box 3045",
    "Spells 1066": "Check Box 3046",
    "Spells 1067": "Check Box 3047",
    "Spells 1068": "Check Box 3048",
    "Spells 1069": "Check Box 3049",
    "Spells 1070": "Check Box 3050",
    "Spells 1071": "Check Box 3051",
    "Spells 1072": "Check Box 3052",
    "Spells 1073": "Check Box 318",
    "Spells 1074": "Check Box 319",
    "Spells 1075": "Check Box 3053",
    "Spells 1076": "Check Box 3054",
    "Spells 1077": "Check Box 3055",
    "Spells 1078": "Check Box 3056",
    "Spells 1079": "Check Box 3057",
    "Spells 1080": "Check Box 3058",
    "Spells 1081": "Check Box 3059",
    "Spells 1082": "Check Box 320",
    "Spells 1083": "Check Box 321",
    "Spells 1084": "Check Box 3060",
    "Spells 1085": "Check Box 3061",
    "Spells 1086": "Check Box 3062",
    "Spells 1087": "Check Box 3063",
    "Spells 1088": "Check Box 3064",
    "Spells 1089": "Check Box 3065",
    "Spells 1090": "Check Box 3066",
    "Spells 1091": "Check Box 322",
    "Spells 1092": "Check Box 323",
    "Spells 1093": "Check Box 3067",
    "Spells 1094": "Check Box 3068",
    "Spells 1095": "Check Box 3069",
    "Spells 1096": "Check Box 3070",
    "Spells 1097": "Check Box 3071",
    "Spells 1098": "Check Box 3072",
    "Spells 1099": "Check Box 3073",
    "Spells 10100": "Check Box 324",
    "Spells 10101": "Check Box 325",
    "Spells 10102": "Check Box 3074",
    "Spells 10103": "Check Box 3075",
    "Spells 10104": "Check Box 3076",
    "Spells 10105": "Check Box 3077",
    "Spells 10106": "Check Box 3078",
    "Spells 10107": "Check Box 326",
    "Spells 10108": "Check Box 327",
    "Spells 10109": "Check Box 3079",
    "Spells 101010": "Check Box 3080",
    "Spells 101011": "Check Box 3081",
    "Spells 101012": "Check Box 3082",
    "Spells 101013": "Check Box 3083",
}


# ------------------------------------------------------------------------------
# Logging & Custom Formatters
# ------------------------------------------------------------------------------


class CustomFormatter(logging.Formatter):
    """
    Custom logging formatter producing strictly:
    [YYYY-MM-DDTHH:MM:SS LEVEL] message
    Colorizes only the LEVEL text using ANSI escape sequences.
    """

    COLORS: Dict[int, str] = {
        logging.DEBUG: "\033[94m",  # light blue
        logging.INFO: "\033[92m",  # light green
        logging.WARNING: "\033[93m",  # yellow
        logging.ERROR: "\033[91m",  # red
        logging.CRITICAL: "\033[91m",  # red
    }
    RESET: str = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        dt = datetime.datetime.fromtimestamp(record.created)
        time_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

        level_name = record.levelname
        if level_name == "WARNING":
            level_name = "WARN"

        color = self.COLORS.get(record.levelno, "")

        # Colorize only the LEVEL name
        formatted_level = f"{color}{level_name}{self.RESET}"

        log_msg = f"[{time_str} {formatted_level}] {record.getMessage()}"
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)
        return log_msg


class LevelRangeFilter(logging.Filter):
    """Filters log records within a specific level range (inclusive)."""

    def __init__(self, low: int, high: int) -> None:
        super().__init__()
        self.low = low
        self.high = high

    def filter(self, record: logging.LogRecord) -> bool:
        return self.low <= record.levelno <= self.high


def setup_logging(verbosity: str) -> None:
    """Configures handlers to direct level-restricted outputs to stdout and stderr."""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARNING,
        "error": logging.ERROR,
    }
    target_level = level_map.get(verbosity.lower(), logging.INFO)

    logger = logging.getLogger("charactersheet")
    logger.setLevel(target_level)
    logger.handlers.clear()

    formatter = CustomFormatter()

    # stdout: DEBUG through INFO
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(LevelRangeFilter(logging.DEBUG, logging.INFO))
    stdout_handler.setFormatter(formatter)

    # stderr: WARNING through CRITICAL
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(LevelRangeFilter(logging.WARNING, logging.CRITICAL))
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)


# ------------------------------------------------------------------------------
# Core Application Functions
# ------------------------------------------------------------------------------


def load_yaml_config(yaml_path: str) -> Dict[str, Any]:
    """Loads and returns the YAML character sheet configuration."""
    logger = logging.getLogger("charactersheet")
    logger.info(f"Loading character configuration from: {yaml_path}")
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("Root configuration must be a dictionary.")
        return config
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {yaml_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"YAML parsing error in '{yaml_path}': {e}")


def merge_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flattens all sections (except 'styling') into a single dictionary
    mapping field names to their configured value / styling data.
    Automatically injects corresponding checkbox fields when 'proficient: true' is specified,
    and maps structured list-based spells to their correct PDF field numbers.
    """
    logger = logging.getLogger("charactersheet")
    merged: Dict[str, Any] = {}

    for section_name, section_data in config.items():
        if section_name == "styling":
            continue

        # Process the structured spells section
        if section_name == "spells":
            if isinstance(section_data, dict):
                for level_key, spell_list in section_data.items():
                    try:
                        level = int(level_key)
                    except ValueError:
                        logger.warning(
                            f"Non-integer spell level key found: '{level_key}'"
                        )
                        continue

                    if level in SPELL_FIELDS_BY_LEVEL and isinstance(spell_list, list):
                        field_names = SPELL_FIELDS_BY_LEVEL[level]
                        for idx, spell_entry in enumerate(spell_list):
                            if idx >= len(field_names):
                                logger.warning(
                                    f"Too many spells for Level {level}! "
                                    f"Maximum allowed is {len(field_names)}."
                                )
                                break

                            field_name = field_names[idx]

                            if isinstance(spell_entry, dict):
                                spell_name = spell_entry.get("name", "")
                                prepared = spell_entry.get("prepared", False)

                                # Extract custom styling overrides for individual spells if present
                                font = spell_entry.get("font")
                                font_size = spell_entry.get("font_size")
                                text_color = spell_entry.get("text_color")

                                if font or font_size or text_color:
                                    merged[field_name] = {
                                        "value": spell_name,
                                        "font": font,
                                        "font_size": font_size,
                                        "text_color": text_color,
                                    }
                                else:
                                    merged[field_name] = spell_name
                            else:
                                spell_name = str(spell_entry)
                                merged[field_name] = spell_name
                                prepared = False

                            if prepared:
                                cb_name = SPELL_PREP_CHECKBOXES.get(field_name)
                                if cb_name:
                                    merged[cb_name] = True
            continue

        # Process normal key-value sections
        if isinstance(section_data, dict):
            for field_name, field_val in section_data.items():
                merged[field_name] = field_val

                # If a saving throw or skill is marked as proficient, also inject the checkbox
                if isinstance(field_val, dict) and field_val.get("proficient") is True:
                    cb_name = PROFICIENCY_CHECKBOXES.get(field_name)
                    if cb_name:
                        merged[cb_name] = True

    return merged


def fill_pdf(
    pdf_template_path: str, output_pdf_path: str, config: Dict[str, Any]
) -> None:
    """Opens a form-fillable PDF template, populates the widgets, and writes output."""
    logger = logging.getLogger("charactersheet")
    logger.info(f"Opening PDF template: {pdf_template_path}")

    try:
        doc = fitz.open(pdf_template_path)
    except Exception as e:
        raise FileNotFoundError(
            f"Failed to open PDF template '{pdf_template_path}': {e}"
        )

    # Extract global styles with safe fallbacks
    global_style = config.get("styling", {})
    default_font = global_style.get("font", "HeBo")
    default_fontsize = global_style.get("font_size", 10)
    default_color = global_style.get("text_color", [0.0, 0.0, 0.0])

    # Globally register/embed custom font file in AcroForm resources if specified
    custom_font_file = global_style.get("font_file")
    if custom_font_file:
        logger.info(f"Embedding custom font locally and globally: {custom_font_file}")
        try:
            # 1. Embed on first page to compile the TrueType font stream and obtain its object ID (xref)
            first_page = doc[0]
            xref = first_page.insert_font(
                fontname=default_font, fontfile=custom_font_file, set_simple=True
            )

            # 2. Link this exact same embedded object ID globally in the document's AcroForm FormFonts
            doc._addFormFont(default_font, f"{xref} 0 R")
            logger.info(
                f"Successfully registered global AcroForm font '{default_font}' (xref {xref})!"
            )
        except Exception as e:
            logger.warning(
                f"Failed to globally register custom font '{custom_font_file}': {e}"
            )

    fields_to_fill = merge_fields(config)
    # Standardize YAML keys: strip leading/trailing whitespace
    normalized_fields = {str(k).strip(): v for k, v in fields_to_fill.items()}

    filled_count = 0

    # Iterate through pages and fields
    for page_idx, page in enumerate(doc):
        # We must insert/embed the font on every page level so standard PDF renderers can find the data.
        # We force 'set_simple=True' to register the TrueType/OpenType font as a 1-byte WinAnsi Type1 font.
        # This is mandatory for PDF widgets to recognize and draw the monospaced glyph metrics!
        if custom_font_file:
            try:
                page.insert_font(
                    fontname=default_font, fontfile=custom_font_file, set_simple=True
                )
            except Exception as e:
                logger.debug(f"Could not insert font on page {page_idx + 1}: {e}")

        for field in page.widgets():
            # Standardize PDF field name
            name = str(field.field_name).strip()

            if name in normalized_fields:
                field_entry = normalized_fields[name]

                # Check if it's a simple value or a dictionary with style overrides
                if isinstance(field_entry, dict) and "value" in field_entry:
                    val = field_entry["value"]
                    font = field_entry.get("font") or default_font
                    font_size = field_entry.get("font_size") or default_fontsize
                    color = field_entry.get("text_color") or default_color
                else:
                    val = field_entry
                    font = default_font
                    font_size = default_fontsize
                    color = default_color

                # Format value safely
                if val is None:
                    val = ""

                # Handle Checkboxes
                if field.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                    # Parse boolean truthiness
                    is_checked = val is True or str(val).lower() in [
                        "true",
                        "yes",
                        "on",
                        "1",
                        "checked",
                        "/on",
                    ]

                    fill_style = global_style.get("fill_checkbox_style", "checkmark")
                    if is_checked:
                        if fill_style == "circle":
                            # Calculate the bounding box center of the checkbox
                            rect = field.rect
                            center = (
                                rect.x0 + rect.width / 2,
                                rect.y0 + rect.height / 2,
                            )
                            # Slightly smaller radius than half width to leave a neat border gap
                            radius = min(rect.width, rect.height) / 2 - 1.2

                            # Draw a solid vector circle on top of the page canvas
                            color_tuple = tuple(color)
                            page.draw_circle(
                                center,
                                radius,
                                color=color_tuple,
                                fill=color_tuple,
                                overlay=True,
                            )
                        else:
                            field.field_value = True
                    else:
                        if fill_style != "circle":
                            field.field_value = False
                else:
                    # Text field or other
                    field.field_value = str(val)
                    field.text_font = font
                    field.text_fontsize = float(font_size)
                    field.text_color = color

                # Commit changes for this widget
                field.update()
                filled_count += 1

    # Flatten (bake) fields if configured in the YAML to ensure custom fonts render on all readers
    flatten = global_style.get("flatten_pdf", False)
    if flatten:
        logger.info(
            "Flattening PDF (baking interactive fields into static page content)..."
        )
        try:
            doc.bake()
            logger.info("Flattened successfully!")
        except Exception as e:
            logger.warning(f"Failed to flatten PDF: {e}")

    logger.info(f"Successfully filled {filled_count} fields across {len(doc)} page(s).")
    logger.info(f"Saving output to: {output_pdf_path}")
    try:
        doc.save(output_pdf_path)
        logger.info("Saved successfully!")
    except Exception as e:
        raise IOError(f"Failed to save output PDF to '{output_pdf_path}': {e}")


def list_pdf_fields(pdf_path: str) -> None:
    """Reads all interactive form fields from the given PDF path using PyMuPDF and prints them."""
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found for field listing: {pdf_path}")

    print(f"Reading fields from: {pdf_path}")
    doc = fitz.open(pdf_path)

    fields: List[Any] = []
    for page in doc:
        for field in page.widgets():
            fields.append(field)

    if not fields:
        print("No interactive form fields found in this PDF.")
        return

    print(f"\nFound {len(fields)} fields:\n")
    print(f"{'Field Name':<45} | {'Field Type':<15} | {'Current Value'}")
    print("-" * 80)

    type_map = {
        fitz.PDF_WIDGET_TYPE_BUTTON: "Button/Checkbox",
        fitz.PDF_WIDGET_TYPE_CHECKBOX: "Button/Checkbox",
        fitz.PDF_WIDGET_TYPE_TEXT: "Text Field",
        fitz.PDF_WIDGET_TYPE_LISTBOX: "Choice/Dropdown",
        fitz.PDF_WIDGET_TYPE_COMBOBOX: "Choice/Dropdown",
        fitz.PDF_WIDGET_TYPE_SIGNATURE: "Signature",
    }

    for field in fields:
        readable_type = type_map.get(field.field_type, f"Unknown ({field.field_type})")
        val = field.field_value
        current_value = str(val) if val is not None else ""
        print(f"{field.field_name:<45} | {readable_type:<15} | {current_value}")


# ------------------------------------------------------------------------------
# CLI Main Entrance
# ------------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="D&D 5E Character Sheet CLI Tool. "
        "Compiles and styles the official fillable PDF sheet from a "
        "YAML configuration or lists its interactive form fields.",
        add_help=True,
    )

    parser.add_argument(
        "character_yaml",
        nargs="?",
        help="Path to the character configuration YAML file (required unless --ls-fields is specified).",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="charactersheet.py 1.0.0",
        help="Show program's version number and exit.",
    )
    parser.add_argument(
        "-V",
        "--verbosity",
        choices=["debug", "info", "warn", "error"],
        default="info",
        help="Set logging verbosity level (default: info).",
    )
    parser.add_argument(
        "-t",
        "--template",
        default="5E_CharacterSheet_Fillable.pdf",
        help="Path to the form-fillable PDF template (default: 5E_CharacterSheet_Fillable.pdf).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Explicit destination path for the filled PDF. "
        "If omitted, derives the path from the input YAML file name (e.g., character.yaml -> character.pdf).",
    )
    parser.add_argument(
        "--ls-fields",
        action="store_true",
        help="List all interactive form fields found in the PDF template and exit.",
    )

    args = parser.parse_args()

    # Configure logging level and destinations
    setup_logging(args.verbosity)
    logger = logging.getLogger("charactersheet")

    # 1. Action: List fields
    if args.ls_fields:
        try:
            list_pdf_fields(args.template)
            sys.exit(0)
        except Exception as e:
            logger.error(
                f"Failed to list PDF fields: {e}",
                exc_info=logger.isEnabledFor(logging.DEBUG),
            )
            sys.exit(1)

    # 2. Action: Fill Character Sheet
    if not args.character_yaml:
        parser.error(
            "the following arguments are required: character_yaml (unless --ls-fields is specified)"
        )
        sys.exit(2)

    # Derive output file path if not provided
    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(args.character_yaml)
        output_path = f"{base}.pdf"

    try:
        config = load_yaml_config(args.character_yaml)
        fill_pdf(args.template, output_path, config)
        sys.exit(0)
    except Exception as e:
        logger.error(
            f"Error during PDF generation: {e}",
            exc_info=logger.isEnabledFor(logging.DEBUG),
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
