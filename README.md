cd ~/Portafolio/aws-pipeline || cd /c/Users/Usuario/Portafolio/aws-pipeline

cat > README.md <<'EOF'
![CI](https://github.com/AlbadawiDev/aws-pipeline/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-informational)
![AWS](https://img.shields.io/badge/AWS-Serverless-orange)

# aws-pipeline
Pipeline serverless: S3 (raw) → Lambda (transform) → S3 (curated) → Athena (Terraform + Python).

## Cómo probar (S3 → Lambda → S3 → Athena)
1. Subir CSV a `s3://daniel-pipeline-aws-2025/raw/ventas.csv`
2. Lambda genera `s3://daniel-pipeline-aws-2025/curated/ventas.csv`
3. Athena (us-east-1):

```sql
CREATE DATABASE IF NOT EXISTS tienda;

CREATE EXTERNAL TABLE IF NOT EXISTS tienda.ventas (
  fecha string,
  producto string,
  cantidad string,
  monto string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"")
LOCATION 's3://daniel-pipeline-aws-2025/curated/'
TBLPROPERTIES ('skip.header.line.count'='1');
