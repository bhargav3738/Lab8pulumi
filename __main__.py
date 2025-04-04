import pulumi
import pulumi_aws as aws

# Create an S3 bucket for the static website
bucket = aws.s3.Bucket("my-bucket",
    website=aws.s3.BucketWebsiteArgs(
        index_document="index.html",
    )
)

# Upload a sample index.html file to the bucket
bucket_object = aws.s3.BucketObject("index.html",
    bucket=bucket.id,
    content="<html><body>Hello, World!</body></html>",
    content_type="text/html",
)

# Create a CloudFront distribution to serve the S3 content
distribution = aws.cloudfront.Distribution("my-distribution",
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=bucket.bucket_regional_domain_name,
        origin_id=bucket.arn,
    )],
    enabled=True,
    default_root_object="index.html",
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=["GET", "HEAD"],
        cached_methods=["GET", "HEAD"],
        target_origin_id=bucket.arn,
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
        viewer_protocol_policy="redirect-to-https",
    ),
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ),
)

# Export the URLs for easy access
pulumi.export("bucket_url", bucket.website_endpoint)
pulumi.export("cdn_url", distribution.domain_name)