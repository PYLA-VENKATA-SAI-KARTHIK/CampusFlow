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
