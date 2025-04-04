import os
import pulumi
import pulumi_aws as aws

# Create the S3 bucket
bucket = aws.s3.Bucket("bucket")

# Set ownership controls
ownership_controls = aws.s3.BucketOwnershipControls(
    "ownership-controls",
    bucket=bucket.bucket,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership="BucketOwnerPreferred"
    )
)

# Configure public access block
public_access_block = aws.s3.BucketPublicAccessBlock(
    "public-access-block",
    bucket=bucket.bucket,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False
)

# Function to sync local folder to S3
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

# Specify the local folder path to sync
path = "./path-to-your-folder"  # Replace with your actual folder path

# Sync the folder to the S3 bucket
sync_folder_to_s3(path, bucket.bucket, [ownership_controls, public_access_block])

# Export the bucket name (optional)
pulumi.export("bucket_name", bucket.bucket)