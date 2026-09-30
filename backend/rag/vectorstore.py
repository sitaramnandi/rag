import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from langchain_aws.vectorstores.s3_vectors import AmazonS3Vectors
from langchain_openai import OpenAIEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)

# Defaults are 60s connect / 60s read with legacy retries, which lets one
# stalled connection block a request for minutes with no feedback. Fail fast
# instead so a bad connection surfaces as a quick, visible error.
_BOTO_CONFIG = Config(
    connect_timeout=5,
    read_timeout=15,
    retries={"max_attempts": 2, "mode": "standard"},
)

_client = boto3.client("s3vectors", region_name=settings.aws_region, config=_BOTO_CONFIG)


def verify_index_exists() -> None:
    """Fail fast with a clear message if the Terraform-managed bucket/index are missing."""
    try:
        _client.get_index(
            vectorBucketName=settings.s3_vector_bucket,
            indexName=settings.s3_vector_index,
        )
        logger.info(
            "S3 vector index verified (bucket=%s, index=%s, region=%s)",
            settings.s3_vector_bucket,
            settings.s3_vector_index,
            settings.aws_region,
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("NotFoundException", "ResourceNotFoundException"):
            logger.error(
                "S3 vector bucket/index not found (bucket=%s, index=%s, region=%s)",
                settings.s3_vector_bucket,
                settings.s3_vector_index,
                settings.aws_region,
            )
            raise RuntimeError(
                f"S3 vector bucket '{settings.s3_vector_bucket}' / index "
                f"'{settings.s3_vector_index}' not found in region "
                f"'{settings.aws_region}'. Run `terraform apply` in the "
                "terraform/ directory before starting the backend."
            ) from exc
        logger.exception("Unexpected error verifying S3 vector index")
        raise


vector_store = AmazonS3Vectors(
    vector_bucket_name=settings.s3_vector_bucket,
    index_name=settings.s3_vector_index,
    region_name=settings.aws_region,
    config=_BOTO_CONFIG,
    embedding=OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        timeout=15,
        max_retries=2,
    ),
    create_index_if_not_exist=False,
)


def delete_by_keys(keys: list[str]) -> None:
    if not keys:
        return
    vector_store.delete(ids=keys)
    logger.info("Deleted %d vectors from S3 Vectors", len(keys))
