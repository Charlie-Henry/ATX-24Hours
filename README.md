# ATX-24Hours
Gifs made of screenshots from Austin's public CCTV cameras.

## Environment

`conda create --name cctv_images --file requirements.txt`

Also uses https://github.com/shawnrivers/gif-compressor for gif compression.

Secrets:
- `AWS_ACCESS_ID` and `AWS_PASS` are credentials for AWS Boto3 client.
- `BUCKET_NAME` is the name of the S3 bucket for storing the gifs.
