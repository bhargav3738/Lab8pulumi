import pulumi
import pulumi_aws as aws
import json
import mimetypes
import os
from pulumi_aws import s3, cloudfront

# 1. Create an S3 bucket for the website with website hosting enabled.
website_bucket = s3.Bucket("website-bucket",
    website=s3.BucketWebsiteArgs(
        index_document="index.html",
        error_document="error.html",
    )
)

# 2. Configure ownership controls for the bucket.
#    Here we use "ObjectWriter" so that the uploader (or writer) remains the owner of the object.
ownership_controls = s3.BucketOwnershipControls("ownership-controls",
    bucket=website_bucket.id,
    rule=s3.BucketOwnershipControlsRuleArgs(
        object_ownership="ObjectWriter"
    )
)

# 3. Configure public access block settings.
#    Disabling the blocks on public ACLs and public policies lets you later set the bucket ACL and policy.
public_access_block = s3.BucketPublicAccessBlock("public-access-block",
    bucket=website_bucket.id,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False
)

# 4. Apply the public-read ACL separately.
#    The depends_on ensures that the ACL is applied only after the ownership and public access settings are configured.
bucket_acl = s3.BucketAcl("bucket-acl",
    bucket=website_bucket.id,
    acl="public-read",
    opts=pulumi.ResourceOptions(depends_on=[ownership_controls, public_access_block])
)

# 5. Define the bucket policy to allow public read access.
bucket_policy = s3.BucketPolicy("bucketPolicy",
    bucket=website_bucket.id,
    policy=website_bucket.id.apply(lambda id: json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{id}/*"]
        }]
    }))
)

# 6. Create an Origin Access Identity (OAI) for CloudFront.
origin_access_identity = cloudfront.OriginAccessIdentity("originAccessIdentity",
    comment="Static website OAI"
)

# 7. Create a CloudFront distribution for the website.
cdn = cloudfront.Distribution("cdn",
    origins=[cloudfront.DistributionOriginArgs(
        domain_name=website_bucket.bucket_regional_domain_name,
        origin_id=website_bucket.bucket,
        s3_origin_config=cloudfront.DistributionOriginS3OriginConfigArgs(
            origin_access_identity=origin_access_identity.cloudfront_access_identity_path
        )
    )],
    enabled=True,
    is_ipv6_enabled=True,
    default_root_object="index.html",
    default_cache_behavior=cloudfront.DistributionDefaultCacheBehaviorArgs(
        allowed_methods=["GET", "HEAD", "OPTIONS"],
        cached_methods=["GET", "HEAD"],
        target_origin_id=website_bucket.bucket,
        forwarded_values=cloudfront.DistributionDefaultCacheBehaviorForwardedValuesArgs(
            query_string=False,
            cookies=cloudfront.DistributionDefaultCacheBehaviorForwardedValuesCookiesArgs(
                forward="none"
            )
        ),
        viewer_protocol_policy="redirect-to-https",
        min_ttl=0,
        default_ttl=3600,
        max_ttl=86400
    ),
    price_class="PriceClass_100",
    restrictions=cloudfront.DistributionRestrictionsArgs(
        geo_restriction=cloudfront.DistributionRestrictionsGeoRestrictionArgs(
            restriction_type="none"
        )
    ),
    viewer_certificate=cloudfront.DistributionViewerCertificateArgs(
        cloudfront_default_certificate=True
    )
)

# 8. Function to upload files from a directory to the website bucket.
def upload_directory_to_s3(directory_path, bucket_name):
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, directory_path)
            
            # Guess the content type; default to binary if not found.
            content_type = mimetypes.guess_type(file_path)[0]
            if content_type is None:
                content_type = "application/octet-stream"
                
            s3.BucketObject(
                relative_path,
                bucket=bucket_name,
                source=pulumi.FileAsset(file_path),
                content_type=content_type
            )

# 9. Upload the website files from a local "website" directory.
website_directory = "./website"
upload_directory_to_s3(website_directory, website_bucket.id)

# 10. Export the website URLs.
pulumi.export("bucket_name", website_bucket.id)
pulumi.export("website_url", website_bucket.website_endpoint)
pulumi.export("cloudfront_domain", cdn.domain_name)
