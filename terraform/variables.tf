variable "region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "vector_bucket_name" {
  description = "Name of the S3 vector bucket that stores document embeddings"
  type        = string
  default     = "rag-app-vectors"
}

variable "index_name" {
  description = "Name of the vector index within the vector bucket"
  type        = string
  default     = "rag-app-index"
}

variable "embedding_dimension" {
  description = "Dimension of the embedding vectors (1536 for OpenAI text-embedding-3-small)"
  type        = number
  default     = 1536
}
