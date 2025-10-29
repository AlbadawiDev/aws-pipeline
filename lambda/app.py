import csv, io, boto3

def _decode(data: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "ignore")

def handler(event, context):
    s3 = boto3.client('s3')
    rec = event['Records'][0]['s3']
    bucket = rec['bucket']['name']
    key = rec['object']['key']  # p.ej. raw/ventas.csv
    obj = s3.get_object(Bucket=bucket, Key=key)
    text = _decode(obj['Body'].read())
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return {"ok": True, "count": 0}
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
    out_key = key.replace('raw/', 'curated/')
    s3.put_object(Bucket=bucket, Key=out_key, Body=out.getvalue().encode('utf-8'))
    return {"ok": True, "count": len(rows)}
