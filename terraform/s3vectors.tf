resource "aws_s3vectors_vector_bucket" "main" {
  vector_bucket_name = var.vector_bucket_name
  force_destroy      = true
}

resource "aws_s3vectors_index" "main" {
  vector_bucket_name = aws_s3vectors_vector_bucket.main.vector_bucket_name
  index_name         = var.index_name
  data_type          = "float32"
  dimension          = var.embedding_dimension
  distance_metric    = "cosine"

  # Full chunk text is stored as metadata but excluded from the filterable
  # index so it doesn't count against per-vector metadata size limits used
  # in filter queries.
  metadata_configuration {
    non_filterable_metadata_keys = [
      "text",
    ]
  }
}
