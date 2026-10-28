"""
Excel and CSV tabular file parsing utility with robust column normalization.
"""
from __future__ import annotations

import csv
import io
import re
from typing import Any


# Standard alias map for column normalization
COLUMN_ALIASES: dict[str, list[str]] = {
    "roll_number": [
        "registration number",
        "registration no",
        "registration_no",
        "registrationno",
        "reg number",
        "reg no",
        "reg_no",
        "regno",
        "register number",
        "register no",
        "register_no",
        "roll number",
        "roll no",
        "roll_no",
        "rollno",
        "htno",
        "hall ticket",
        "hall ticket number",
        "hall ticket no",
        "student id",
        "student registration number",
        "student roll number",
        "student roll no",
        "student reg no",
        "id number",
        "id no",
        "univ reg no",
        "university reg no",
        "university registration number",
    ],
    "full_name": [
        "student name",
        "name",
        "full name",
        "candidate name",
        "student_name",
        "fullname",
        "name of the student",
        "name of student",
        "name of the candidate",
    ],
    "branch_code": [
        "branch",
        "department",
        "dept",
        "branch code",
        "branch_code",
        "dept code",
        "program",
        "programme",
        "course",
        "stream",
        "specialization",
    ],
    "batch_year": [
        "batch",
        "batch year",
        "batch_year",
        "passout year",
        "pass out year",
        "passing year",
        "graduation year",
        "year of passing",
        "grad year",
        "year",
    ],
    "cgpa": [
        "cgpa",
        "gpa",
        "btech cgpa",
        "b.tech cgpa",
        "aggregate cgpa",
        "overall cgpa",
        "btech %",
        "percentage",
    ],
    "active_backlogs": [
        "active backlogs",
        "active_backlogs",
        "backlogs",
        "current backlogs",
        "standing backlogs",
        "arrears",
        "history of backlogs",
        "no of backlogs",
        "number of backlogs",
    ],
    "personal_email": [
        "email",
        "personal email",
        "email id",
        "email_id",
        "personal_email",
        "student email",
        "mail id",
    ],
    "phone_number": [
        "phone",
        "phone number",
        "phone_number",
        "mobile",
        "mobile number",
        "mobile_no",
        "contact",
        "contact number",
        "contact no",
    ],
    "gender": [
        "gender",
        "sex",
    ],
    "section": [
        "section",
        "sec",
    ],
}


BRANCH_SYNONYMS: dict[str, str] = {
    "COMPUTER SCIENCE": "CSE",
    "COMPUTER SCIENCE AND ENGINEERING": "CSE",
    "COMPUTER SCIENCE & ENGINEERING": "CSE",
    "COMP SCI": "CSE",
    "CS": "CSE",
    "ELECTRONICS AND COMMUNICATION": "ECE",
    "ELECTRONICS & COMMUNICATION": "ECE",
    "ELECTRONICS AND COMMUNICATION ENGINEERING": "ECE",
    "ELECTRONICS & COMMUNICATION ENGINEERING": "ECE",
    "EC": "ECE",
    "INFORMATION TECHNOLOGY": "IT",
    "INFO TECH": "IT",
    "MECHANICAL": "MECH",
    "MECHANICAL ENGINEERING": "MECH",
    "ME": "MECH",
    "CIVIL": "CIVIL",
    "CIVIL ENGINEERING": "CIVIL",
    "CE": "CIVIL",
    "ELECTRICAL AND ELECTRONICS": "EEE",
    "ELECTRICAL & ELECTRONICS": "EEE",
    "ELECTRICAL AND ELECTRONICS ENGINEERING": "EEE",
    "ELECTRICAL & ELECTRONICS ENGINEERING": "EEE",
    "EE": "EEE",
    "ARTIFICIAL INTELLIGENCE AND DATA SCIENCE": "AI&DS",
    "ARTIFICIAL INTELLIGENCE & DATA SCIENCE": "AI&DS",
    "AI AND DS": "AI&DS",
    "AI & DS": "AI&DS",
    "AIDS": "AI&DS",
    "ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING": "AI&ML",
    "ARTIFICIAL INTELLIGENCE & MACHINE LEARNING": "AI&ML",
    "AI AND ML": "AI&ML",
    "AI & ML": "AI&ML",
    "AIML": "AI&ML",
    "COMPUTER SCIENCE AND INFORMATION TECHNOLOGY": "CSIT",
    "CSIT": "CSIT",
    "ELECTRONICS AND COMPUTER ENGINEERING": "ECM",
    "ECM": "ECM",
    "BIOTECHNOLOGY": "BIOTECH",
    "BIO TECHNOLOGY": "BIOTECH",
    "BT": "BIOTECH",
}


def normalize_branch_code(val: Any) -> str:
    """Normalize branch string to a short uppercase standard code <= 20 chars."""
    if not val:
        return "CSE"
    s = normalize_cell_as_string(val).strip().upper()
    if not s:
        return "CSE"
    # Check exact synonym match
    if s in BRANCH_SYNONYMS:
        return BRANCH_SYNONYMS[s]
    # Check cleaned text
    cleaned = re.sub(r"[\s_\-\.]+", " ", s)
    if cleaned in BRANCH_SYNONYMS:
        return BRANCH_SYNONYMS[cleaned]
    # If contains known branch keywords
    for full_name, code in BRANCH_SYNONYMS.items():
        if len(full_name) > 3 and full_name in cleaned:
            return code
    # Clean non-alphanumeric chars and truncate to 20 chars
    clean_code = re.sub(r"[^\w\&\-]", "", s)[:20]
    return clean_code if clean_code else "CSE"


def normalize_batch_year(val: Any, default: int = 2027) -> int:
    """Extract 4-digit or 2-digit batch year safely."""
    if val is None:
        return default
    s = normalize_cell_as_string(val).strip()
    if not s:
        return default
    # Try finding 4-digit year like 2026 or 2025
    m4 = re.search(r"\b(20\d{2})\b", s)
    if m4:
        return int(m4.group(1))
    # Try finding 2-digit year like 26 in '22-26' or '26'
    m2 = re.search(r"\b(\d{2})\b", s)
    if m2:
        val2 = int(m2.group(1))
        if 20 <= val2 <= 35:
            return 2000 + val2
    try:
        fval = int(float(s))
        if 1900 <= fval <= 2100:
            return fval
        if 20 <= fval <= 35:
            return 2000 + fval
    except Exception:
        pass
    return default


def normalize_cgpa(val: Any, default: float = 0.0) -> float:
    """Safely parse CGPA or percentage (0.00 to 10.00)."""
    if val is None:
        return default
    s = normalize_cell_as_string(val).strip().replace("%", "").replace(",", ".")
    if not s or s.lower() in ("na", "n/a", "nil", "none", "null", "-"):
        return default
    try:
        cgpa = float(s)
        if cgpa > 10.0 and cgpa <= 100.0:
            cgpa = round(cgpa / 10.0, 2)
        elif cgpa > 100.0:
            cgpa = 10.0
        cgpa = max(0.0, min(10.0, round(cgpa, 2)))
        return cgpa
    except Exception:
        return default


def normalize_backlogs(val: Any, default: int = 0) -> int:
    """Safely parse integer backlogs count."""
    if val is None:
        return default
    s = normalize_cell_as_string(val).strip()
    if not s or s.lower() in ("no", "nil", "none", "na", "n/a", "-", "zero"):
        return 0
    try:
        b = int(float(s))
        return max(0, min(100, b))
    except Exception:
        return default


def normalize_phone_number(val: Any) -> str | None:
    """Extract phone number preserving leading + if present, up to 15 chars."""
    if val is None:
        return None
    s = normalize_cell_as_string(val).strip()
    if not s or s.lower() in ("na", "n/a", "nil", "none", "null", "-"):
        return None
    # If multiple phone numbers e.g. separated by slash or comma, take first
    first_part = re.split(r"[/,;\s]+", s)[0].strip()
    digits_only = re.sub(r"[^\d\+]", "", first_part)
    if len(digits_only) < 7:
        return None
    return digits_only[:15]


def normalize_personal_email(val: Any) -> str | None:
    """Clean and validate personal email address."""
    if val is None:
        return None
    s = normalize_cell_as_string(val).strip().replace(" ", "").lower()
    if not s or s in ("na", "n/a", "nil", "none", "null", "-"):
        return None
    if "@" in s and "." in s:
        return s[:255]
    return None


def normalize_gender(val: Any) -> str | None:
    """Normalize gender to MALE, FEMALE, OTHER, or None."""
    if val is None:
        return None
    s = normalize_cell_as_string(val).strip().upper()
    if not s or s in ("NA", "N/A", "NONE", "NULL", "-"):
        return None
    if s.startswith("M") or s in ("BOY", "MAN", "MALE"):
        return "MALE"
    if s.startswith("F") or s in ("GIRL", "WOMAN", "FEMALE"):
        return "FEMALE"
    return "OTHER"


def normalize_cell_as_string(val: Any) -> str:
    """
    Normalize a cell value to a clean string.
    Preserves leading zeroes.
    If openpyxl or Python parsed an integer as float (e.g. 99230041249.0), removes trailing .0.
    """
    if val is None:
        return ""
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return str(val).strip()
    if isinstance(val, int):
        return str(val)
    
    s = str(val).strip()
    # Check if string looks like a float representation of an integer (e.g. "99230041249.0")
    if re.match(r"^\d+\.0$", s):
        return s[:-2]
    return s


def clean_header_name(header: str) -> str:
    """Normalize header text for comparison."""
    h = str(header).lower().strip()
    h = re.sub(r"[\s_\-\.]+", " ", h)
    return h


def detect_column_mappings(headers: list[str]) -> dict[str, str]:
    """
    Given a list of raw headers from an Excel/CSV file, match each standard field to a header.
    Returns a dict mapping standard_field -> original_header_name.
    """
    mapping: dict[str, str] = {}
    cleaned_headers = [(clean_header_name(h), h) for h in headers if h]

    for field, aliases in COLUMN_ALIASES.items():
        # First try exact match with aliases
        matched_header: str | None = None
        for alias in aliases:
            for cleaned, original in cleaned_headers:
                if cleaned == alias:
                    matched_header = original
                    break
            if matched_header:
                break
        
        # If no exact match, try contains match for specific fields
        if not matched_header:
            for alias in aliases:
                for cleaned, original in cleaned_headers:
                    if alias in cleaned and original not in mapping.values():
                        matched_header = original
                        break
                if matched_header:
                    break

        if matched_header:
            mapping[field] = matched_header

    return mapping


def parse_tabular_file(file_bytes: bytes, filename: str) -> tuple[list[str], list[dict[str, Any]]]:
    """
    Parses an Excel (.xlsx, .xlsm) or CSV (.csv) file from bytes into headers and row dicts.
    Returns (headers, list_of_raw_row_dicts).
    """
    fname_lower = filename.lower()
    
    if fname_lower.endswith(".csv"):
        # Decode CSV
        text_content = ""
        for encoding in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
            try:
                text_content = file_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        
        if not text_content:
            raise ValueError("Unable to decode CSV file with supported encodings (UTF-8, Latin-1).")

        reader = csv.reader(io.StringIO(text_content))
        rows = list(reader)
        if not rows:
            return [], []

        headers = [normalize_cell_as_string(c) for c in rows[0] if c is not None]
        data_rows: list[dict[str, Any]] = []
        for row in rows[1:]:
            if not any(c.strip() for c in row if c):
                continue
            row_dict = {}
            for i, val in enumerate(row):
                if i < len(headers) and headers[i]:
                    row_dict[headers[i]] = normalize_cell_as_string(val)
            data_rows.append(row_dict)
        return headers, data_rows

    else:
        # Excel .xlsx parsing with openpyxl
        import openpyxl

        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True, read_only=True)
        sheet = wb.active
        if not sheet:
            return [], []

        rows_iter = sheet.iter_rows(values_only=True)
        first_row = next(rows_iter, None)
        if not first_row:
            return [], []

        raw_headers = [normalize_cell_as_string(c) for c in first_row]
        # Keep non-empty headers
        headers = [h for h in raw_headers if h]

        data_rows = []
        for row in rows_iter:
            if not any(c is not None and str(c).strip() for c in row):
                continue
            row_dict = {}
            for i, val in enumerate(row):
                if i < len(raw_headers) and raw_headers[i]:
                    row_dict[raw_headers[i]] = normalize_cell_as_string(val)
            data_rows.append(row_dict)

        wb.close()
        return headers, data_rows
