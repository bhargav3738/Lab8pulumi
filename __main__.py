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
    restrictions=aws.cloudfront.DistributionRestrictionsArgs(
        geo_restriction=aws.cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none"
        )
    ),
    viewer_certificate=aws.cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True
    )
)
