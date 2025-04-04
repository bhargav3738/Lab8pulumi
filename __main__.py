import pulumi_aws as aws
import os

# Read the OIDC token from the file path provided by GitHub Actions
with open(os.environ["AWS_WEB_IDENTITY_TOKEN_FILE"], "r") as token_file:
    web_identity_token = token_file.read()

# Create an AWS provider with OIDC authentication
provider = aws.Provider("aws",
    region="us-west-2",
    assume_role_with_web_identity={
        "role_arn": "arn:aws:iam::913524946449:role/PulumiRole",
        "web_identity_token": web_identity_token,
    }
)

# Define an S3 bucket for the static website
bucket = aws.s3.Bucket("my-bucket",
    website=aws.s3.BucketWebsiteArgs(index_document="index.html"),
    opts=pulumi.ResourceOptions(provider=provider)
)

# Upload an index.html file to the bucket
bucket_object = aws.s3.BucketObject("index.html",
    bucket=bucket.id,
    content="<html><body>Hello, World!</body></html>",
    content_type="text/html",
    opts=pulumi.ResourceOptions(provider=provider)
)

# Create a CloudFront distribution
distribution = aws.cloudfront.Distribution("my-distribution",
    enabled=True,
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=bucket.bucket_regional_domain_name,
        origin_id=bucket.arn,
    )],
    default_root_object="index.html",
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id=bucket.arn,
        viewer_protocol_policy="redirect-to-https",
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        cached_methods=["GET", "HEAD"],
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none"
            ),
        ),
    ),
    price_class="PriceClass_100",
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ),
    opts=pulumi.ResourceOptions(provider=provider)
)

# Export the distribution URL
pulumi.export("distribution_url", distribution.domain_name)