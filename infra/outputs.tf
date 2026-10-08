output "data_bucket" {
  value       = aws_s3_bucket.data.id
  description = "Generated S3 bucket name after an approved deployment."
}

output "lambda_function" {
  value = aws_lambda_function.transform.function_name
}
