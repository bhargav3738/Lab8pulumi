# S3 with CloudFront Pulumi Project

## Error Handling

### "Resource did not exist while updating" Error

If you encounter the following error:

```
error: Resource provider reported that the resource did not exist while updating urn:pulumi:dev::pulumi-s3-cloudfront::aws:s3/bucket:Bucket::website-bucket.
```

This typically happens when resources have been deleted outside of Pulumi's knowledge. To fix this:

1. Go to the GitHub repository
2. Navigate to the "Actions" tab
3. Select the "Refresh Pulumi State" workflow
4. Click "Run workflow"
5. Enter "yes" when prompted to confirm
6. Wait for the refresh operation to complete
7. Re-run the main deployment workflow

Alternatively, you can run the following command locally:

```bash
pulumi refresh --stack dev
```

After refreshing, Pulumi will know the current state of the resources and can properly recreate them during the next deployment.
