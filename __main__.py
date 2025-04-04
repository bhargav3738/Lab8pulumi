import pulumi
import pulumi_aws as aws
from pulumi_synced_folder import S3BucketFolder

# Import the program's configuration settings.
config = pulumi.Config()
path = config.get("path") or "./website"
index_document = config.get("indexDocument") or "index.html"
error_document = config.get("errorDocument") or "error.html"

# Create an S3 bucket and configure it as a website.
bucket = aws.s3.BucketV2("bucket")

bucket_website = aws.s3.BucketWebsiteConfigurationV2("bucketWebsite",
    bucket=bucket.bucket,
    index_document=aws.s3.BucketWebsiteConfigurationV2IndexDocumentArgs(suffix=index_document),
    error_document=aws.s3.BucketWebsiteConfigurationV2ErrorDocumentArgs(key=error_document),
)

# Configure ownership controls for the new S3 bucket.
ownership_controls = aws.s3.BucketOwnershipControls("ownership-controls",
    bucket=bucket.bucket,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership="ObjectWriter"
    )
)

# Configure public ACL block on the new S3 bucket.
public_access_block = aws.s3.BucketPublicAccessBlock("public-access-block",
    bucket=bucket.bucket,
    block_public_acls=False
)

# Use a synced folder to manage the files of the website.
bucket_folder = S3BucketFolder("bucket-folder",
    path=path,
    bucket_name=bucket.bucket,
    acl="public-read",
    opts=pulumi.ResourceOptions(depends_on=[ownership_controls, public_access_block])
)

# Create a CloudFront CDN to distribute and cache the website.
cdn = aws.cloudfront.Distribution("cdn",
    enabled=True,
    origins=[aws.cloudfront.DistributionOriginArgs(
        origin_id=bucket.arn,
        domain_name=bucket_website.website_endpoint,
        custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
            origin_protocol_policy="http-only",
            http_port=80,
            https_port=443,
            origin_ssl_protocols=["TLSv1.2"]
        )
    )],
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id=bucket.arn,
        viewer_protocol_policy="redirect-to-https",
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        cached_methods=["GET", "HEAD", "OPTIONS"],
        default_ttl=600,
        max_ttl=600,
        min_ttl=600,
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=True,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="all"
            )
        )
    ),
    price_class="PriceClass_100",
    custom_error_responses=[aws.cloudfront.DistributionCustomErrorResponseArgs(
        error_code=404,
        response_code=404,
        response_page_path=f"/{error_document}"
    )],
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none"
        )
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True
    )
)

# Export the URLs and hostnames of the bucket and distribution.
pulumi.export("originURL", pulumi.Output.concat("http://", bucket_website.website_endpoint))
pulumi.export("originHostname", bucket_website.website_endpoint)
pulumi.export("cdnURL", pulumi.Output.concat("https://", cdn.domain_name))
pulumi.export("cdnHostname", cdn.domain_name)