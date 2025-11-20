import os
import subprocess
import boto3
import sys
import logging
from pathlib import Path
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()          
    ]
)
logger = logging.getLogger()

STACK_NAME = "assignment-4-sam"
REGION = "ap-south-1"
CODE_BUCKET = "assignment-4-sam-artifacts"
WEBSITE_BUCKET = "assignment-4-sam-website"

ROOT = Path(__file__).parent
DIST_ZIP = ROOT / "dist" / "mysql-layer.zip"
WEB_DIR = ROOT / "web"


def run(cmd, cwd=None):
    logger.info("Running: %s", cmd)
    subprocess.run(cmd, cwd=cwd, shell=True, check=True)


def ensure_bucket(bucket):
    s3 = boto3.client("s3", region_name=REGION)
    logger.info("Ensuring bucket exists: %s", bucket)

    try:
        s3.head_bucket(Bucket=bucket)
        logger.info("Bucket already exists: %s", bucket)
    except ClientError:
        logger.info("Bucket not found, creating: %s", bucket)
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": REGION},
        )
        logger.info("Bucket created: %s", bucket)



def build_layer():
    script = ROOT / "layer" / "mysql-layer" / "build.sh"
    logger.info("Build Lambda layer via %s", script)
    run(f"bash {script}")

def upload_layer():
    logger.info("Upload layer")
    if not DIST_ZIP.exists():
        logger.error("Layer zip not found")
        raise FileNotFoundError(f"Layer zip not found: {DIST_ZIP}")
    s3 = boto3.client("s3", region_name=REGION)
    s3.upload_file(str(DIST_ZIP), CODE_BUCKET, "mysql-layer.zip")
    logger.info("Layer uploaded")


def sam_build():
    logger.info("SAM build")
    run("sam build")
    logger.info("SAM build done")


def sam_deploy():
    logger.info("SAM deploy")
    cmd = (
        f"sam deploy "
        f"--stack-name {STACK_NAME} "
        f"--region {REGION} "
        f"--capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM "
        f"--s3-bucket {CODE_BUCKET} "
        f"--parameter-overrides CodeBucket={CODE_BUCKET} WebsiteBucketName={WEBSITE_BUCKET} "
        f"--no-confirm-changeset "
        f"--no-fail-on-empty-changeset"
    )
    run(cmd)
    logger.info("SAM deploy done")


def get_outputs():
    logger.info("Getting stack outputs")

    cfn = boto3.client("cloudformation", region_name=REGION)
    resp = cfn.describe_stacks(StackName=STACK_NAME)

    stack = resp["Stacks"][0]
    outputs = stack.get("Outputs", [])

    api_url = None
    website_url = None

    for item in outputs:
        key = item["OutputKey"]
        value = item["OutputValue"]

        if key == "DetailsEndpoint":
            api_url = value
        elif key == "WebsiteURL":
            website_url = value

    logger.info("API endpoint: %s", api_url)
    logger.info("Website URL: %s", website_url)

    return {
        "DetailsEndpoint": api_url,
        "WebsiteURL": website_url,
    }



def upload_website_files(bucket):
    logger.info("Uploading website files")

    s3 = boto3.client("s3", region_name=REGION)

    files = {
        "index.html": "text/html",
        "styles.css": "text/css",
        "app.js": "application/javascript",
    }
    for name, content_type in files.items():
        path = WEB_DIR / name
        s3.upload_file(
            str(path),
            bucket,
            name,
            ExtraArgs={"ContentType": content_type},
        )
        logger.info("Uploaded %s", name)

    logger.info("Website upload finished")


if __name__ == "__main__":
    logger.info("Starting deployment")
    try:
        build_layer()
        ensure_bucket(CODE_BUCKET)
        upload_layer()
        sam_build()
        sam_deploy()
        get_outputs()
        upload_website_files(WEBSITE_BUCKET)
        logger.info("Deployment finished OK")
    except Exception:
        logger.exception("Deployment failed")
        sys.exit(1)
