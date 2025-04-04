import os
import pulumi
import pulumi_aws as aws

# Create the S3 bucket with website hosting enabled
bucket = aws.s3.Bucket("bucket",
    website=aws.s3.BucketWebsiteArgs(
        index_document="index.html",
        error_document="404.html",
    )
)

# Set ownership controls on the bucket
ownership_controls = aws.s3.BucketOwnershipControls(
    "ownership-controls",
    bucket=bucket.bucket,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership="BucketOwnerPreferred"
    )
)

# Configure public access block (customize as needed)
public_access_block = aws.s3.BucketPublicAccessBlock(
    "public-access-block",
    bucket=bucket.bucket,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False
)

# Function to sync local folder content to the S3 bucket
def sync_folder_to_s3(local_path, bucket_name, depends_on):
    for root, dirs, files in os.walk(local_path):
        for file in files:
            local_file_path = os.path.join(root, file)
            s3_key = os.path.relpath(local_file_path, local_path)
            aws.s3.BucketObject(
                s3_key,
                bucket=bucket_name,
                key=s3_key,
                source=pulumi.FileAsset(local_file_path),
                acl="public-read",
                opts=pulumi.ResourceOptions(depends_on=depends_on)
            )

# Specify your local folder to sync
path = "./index.html"  # Replace with your actual folder path

# Sync the folder to the S3 bucket
sync_folder_to_s3(path, bucket.bucket, [ownership_controls, public_access_block])

# Create a CloudFront distribution to serve the static website
cdn = aws.cloudfront.Distribution("cdn",
    origins=[aws.cloudfront.DistributionOriginArgs(
        # Use the S3 website endpoint as the custom origin domain name
        domain_name=bucket.website_endpoint,
        origin_id=bucket.bucket,
        custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
            http_port=80,
            https_port=443,
            # S3 website endpoints only support HTTP
            origin_protocol_policy="http-only",
            origin_ssl_protocols=["TLSv1.2"],
        ),
    )],
    enabled=True,
    is_ipv6_enabled=True,
    default_root_object="index.html",
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id=bucket.bucket,
        viewer_protocol_policy="redirect-to-https",
        allowed_methods=["GET", "HEAD"],
        cached_methods=["GET", "HEAD"],
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none"
            )
        )
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True
    )
)

# Export useful outputs
pulumi.export("bucket_name", bucket.bucket)
pulumi.export("website_url", bucket.website_endpoint)
pulumi.export("cdn_url", cdn.domain_name)
