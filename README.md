## Cómo probar (S3 → Lambda → S3 → Athena)
1. Subir CSV a `s3://daniel-pipeline-aws-2025/raw/ventas.csv`
2. Lambda genera `s3://daniel-pipeline-aws-2025/curated/ventas.csv`
3. Athena (us-east-1):
   ```sql
   CREATE DATABASE IF NOT EXISTS tienda;
   CREATE EXTERNAL TABLE IF NOT EXISTS tienda.ventas (
     fecha string, producto string, cantidad string, monto string
   )
   ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
   WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"")
   LOCATION 's3://daniel-pipeline-aws-2025/curated/'
   TBLPROPERTIES ('skip.header.line.count'='1');
