import pulumi
import pulumi_aws as aws

# Create the S3 bucket with website hosting enabled
bucket = aws.s3.Bucket("bucket-new",
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

# Use the local index.html file from the root folder for the website's main page
index_file = aws.s3.BucketObject("index-file",
    bucket=bucket.bucket,
    key="index.html",
    source=pulumi.FileAsset("index.html"),  # Points to the index.html file in your root folder
    content_type="text/html",
    acl="public-read",
    opts=pulumi.ResourceOptions(depends_on=[ownership_controls, public_access_block])
)

# Optionally, if you also have a 404.html in the root folder, use it for the error page
error_file = aws.s3.BucketObject("error-file",
    bucket=bucket.bucket,
    key="404.html",
    source=pulumi.FileAsset("404.html"),  # Points to the 404.html file in your root folder
    content_type="text/html",
    acl="public-read",
    opts=pulumi.ResourceOptions(depends_on=[ownership_controls, public_access_block])
)

# Create a CloudFront distribution to serve the static website
cdn = aws.cloudfront.Distribution("cdn",
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=bucket.website_endpoint,
        origin_id=bucket.bucket,
        custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
            http_port=80,
            https_port=443,
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
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none"
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
