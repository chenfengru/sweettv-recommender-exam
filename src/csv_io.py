"""Strict CSV readers: preserve IDs as text and never guess numeric units."""

import codecs
import csv
import hashlib
from contextlib import contextmanager
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def open_csv(path, *, encoding=None, delimiter=None):
    """Yield (header, csv reader, format metadata); reject ambiguous schemas."""
    path = Path(path)
    with path.open("rb") as source:
        prefix = source.read(4)
    if encoding is None:
        encoding = "utf-16" if prefix.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) else "utf-8-sig"
        encoding_method = "BOM or strict UTF-8; legacy encodings require --encoding"
    else:
        encoding_method = "explicit override"
    try:
        with path.open(encoding=encoding, newline="") as source:
            sample = source.read(65536)
            source.seek(0)
            if delimiter is None:
                try:
                    delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
                except csv.Error as exc:
                    raise ValueError(f"{path.name}: cannot determine delimiter; provide --delimiter") from exc
                delimiter_method = "csv.Sniffer on first 65,536 characters"
            else:
                delimiter_method = "explicit override"
            if len(delimiter) != 1:
                raise ValueError("delimiter must be one character")
            reader = csv.reader(source, delimiter=delimiter, strict=True)
            header = next(reader, None)
            if not header or any(not h.strip() for h in header):
                raise ValueError(f"{path.name}: missing or empty header")
            if len(set(header)) != len(header):
                raise ValueError(f"{path.name}: duplicate column names")
            yield header, reader, {
                "encoding": encoding, "encoding_method": encoding_method,
                "delimiter": delimiter, "delimiter_method": delimiter_method,
            }
    except UnicodeError as exc:
        raise ValueError(f"{path.name}: encoding error; inspect bytes and supply --encoding") from exc
    except csv.Error as exc:
        raise ValueError(f"{path.name}: malformed CSV near physical line {getattr(locals().get('reader'), 'line_num', '?')}") from exc


def require_columns(header, required, filename):
    missing = sorted(set(required) - set(header))
    if missing:
        raise ValueError(f"{filename}: missing columns {missing}; actual header is {header}")


def checked_rows(reader, header, filename):
    for record_number, values in enumerate(reader, 2):
        if len(values) != len(header):
            raise ValueError(f"{filename}: record {record_number} has {len(values)} fields; expected {len(header)}")
        yield record_number, dict(zip(header, values))


def is_zero_id(value: str) -> bool:
    """Recognize numeric zero spellings without coercing any other identifier."""
    from decimal import Decimal, InvalidOperation
    try:
        return Decimal(value.strip()) == 0
    except (InvalidOperation, ValueError):
        return False
