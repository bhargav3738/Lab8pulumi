import pulumi
import pulumi_aws as aws

# Create an S3 bucket for the static website
site_bucket = aws.s3.Bucket('siteBucket',
    website=aws.s3.BucketWebsiteArgs(
        index_document="index.html",
    ))

# Upload a sample index.html file
index_content = pulumi.Output.all().apply(
    lambda _: "<html><body><h1>Hello from Pulumi!</h1></body></html>")
index_object = aws.s3.BucketObject("index.html",
    bucket=site_bucket.id,
    content=index_content,
    content_type="text/html")

# Create a CloudFront distribution pointing to the S3 website endpoint
cdn = aws.cloudfront.Distribution("cdnDistribution",
    origins=[aws.cloudfront.DistributionOriginArgs(
        domain_name=site_bucket.website_endpoint,
        origin_id=site_bucket.id,
        custom_origin_config=aws.cloudfront.DistributionOriginCustomOriginConfigArgs(
            http_port=80,
            https_port=443,
            origin_protocol_policy="http-only",
            origin_ssl_protocols=["TLSv1.2"],
        ),
    )],
    enabled=True,
    default_root_object="index.html",
    default_cache_behavior=aws.cloudfront.DistributionDefaultCacheBehaviorArgs(
        target_origin_id=site_bucket.id,
        viewer_protocol_policy="allow-all",
        allowed_methods=["GET", "HEAD"],
        cached_methods=["GET", "HEAD"],
        forwarded_values=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=aws.cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none",
            ),
        ),
    ),
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none",
            locations=[],
        ),
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True,
    ))

pulumi.export("bucketName", site_bucket.bucket)
pulumi.export("cloudfrontDomain", cdn.domain_name)
