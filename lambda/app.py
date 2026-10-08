"""Normalize raw CSV uploads to UTF-8. Tests replace the S3 transport."""
import csv
import io
import os
from urllib.parse import unquote_plus

import boto3

MAX_BYTES = int(os.environ.get('MAX_CSV_BYTES', '5000000'))

def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError('Unsupported CSV encoding')


def normalize_csv(data: bytes) -> tuple[bytes, int]:
    if len(data) > MAX_BYTES:
        raise ValueError('CSV exceeds configured size limit')
    reader = csv.DictReader(io.StringIO(_decode(data), newline=''), strict=True)
    fields = reader.fieldnames
    if not fields or any(not field.strip() for field in fields) or len(set(fields)) != len(fields):
        raise ValueError('CSV requires unique, non-empty column names')
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    count = 0
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError('CSV row does not match header width')
        writer.writerow(row)
        count += 1
    return out.getvalue().encode('utf-8'), count

def handler(event, context):
    s3 = boto3.client('s3')
    processed, skipped, count = [], 0, 0
    for record in event.get('Records', []):
        if record.get('eventSource') != 'aws:s3' or not record.get('eventName', '').startswith('ObjectCreated:'):
            skipped += 1
            continue
        rec = record['s3']
        bucket = rec['bucket']['name']
        key = unquote_plus(rec['object']['key'])
        if not key.startswith('raw/') or not key.lower().endswith('.csv'):
            skipped += 1
            continue
        if rec['object'].get('size', 0) > MAX_BYTES:
            raise ValueError('CSV exceeds configured size limit')
        obj = s3.get_object(Bucket=bucket, Key=key)
        body = obj['Body']
        try:
            output, rows = normalize_csv(body.read(MAX_BYTES + 1))
        finally:
            body.close()
        out_key = 'curated/' + key[len('raw/'):]
        s3.put_object(Bucket=bucket, Key=out_key, Body=output, ContentType='text/csv; charset=utf-8')
        processed.append({'key': out_key, 'count': rows})
        count += rows
    return {'ok': True, 'count': count, 'processed': processed, 'skipped': skipped}
