output "vector_bucket_name" {
  description = "Name of the S3 vector bucket — set as S3_VECTOR_BUCKET in backend/.env"
  value       = aws_s3vectors_vector_bucket.main.vector_bucket_name
}

output "vector_bucket_arn" {
  value = aws_s3vectors_vector_bucket.main.vector_bucket_arn
}

output "index_name" {
  description = "Name of the vector index — set as S3_VECTOR_INDEX in backend/.env"
  value       = aws_s3vectors_index.main.index_name
}

output "index_arn" {
  value = aws_s3vectors_index.main.index_arn
}

output "region" {
  value = var.region
}
