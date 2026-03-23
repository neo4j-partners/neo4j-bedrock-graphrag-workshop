#!/usr/bin/env bash
#
# Create an S3 bucket with CloudFront (OAC) for workshop seed data CSVs.
# The bucket stays private; only CloudFront can read from it.
#
# Usage:
#   ./setup_s3_seed_data.sh                    # defaults to us-east-1
#   ./setup_s3_seed_data.sh --region us-west-2
#   ./setup_s3_seed_data.sh --cleanup          # delete CloudFront, OAC, bucket

set -euo pipefail

BUCKET_NAME="neo4j-aws-workshop-data"
S3_PREFIX="sec-filings"
REGION="us-east-1"
CLEANUP=false
OAC_NAME="neo4j-workshop-oac"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SEED_DATA_DIR="${SCRIPT_DIR}/seed-data"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --cleanup)
            CLEANUP=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--region REGION] [--cleanup]"
            exit 1
            ;;
    esac
done

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# ── Helper: find existing CloudFront distribution for this bucket ─────────────

find_distribution_id() {
    aws cloudfront list-distributions \
        --query "DistributionList.Items[?Origins.Items[0].DomainName=='${BUCKET_NAME}.s3.${REGION}.amazonaws.com'].Id | [0]" \
        --output text 2>/dev/null || echo "None"
}

find_oac_id() {
    aws cloudfront list-origin-access-controls \
        --query "OriginAccessControlList.Items[?Name=='${OAC_NAME}'].Id | [0]" \
        --output text 2>/dev/null || echo "None"
}

# ── Cleanup mode ──────────────────────────────────────────────────────────────

if [ "$CLEANUP" = true ]; then
    DIST_ID=$(find_distribution_id)

    if [ "$DIST_ID" != "None" ] && [ -n "$DIST_ID" ]; then
        echo "Disabling CloudFront distribution ${DIST_ID} ..."
        ETAG=$(aws cloudfront get-distribution-config --id "$DIST_ID" --query "ETag" --output text)
        CONFIG=$(aws cloudfront get-distribution-config --id "$DIST_ID" --query "DistributionConfig" --output json)
        DISABLED_CONFIG=$(echo "$CONFIG" | python3 -c "import sys,json; c=json.load(sys.stdin); c['Enabled']=False; json.dump(c,sys.stdout)")
        aws cloudfront update-distribution --id "$DIST_ID" --if-match "$ETAG" \
            --distribution-config "$DISABLED_CONFIG" > /dev/null

        echo "Waiting for distribution to deploy (this takes a few minutes) ..."
        aws cloudfront wait distribution-deployed --id "$DIST_ID"

        echo "Deleting CloudFront distribution ${DIST_ID} ..."
        ETAG=$(aws cloudfront get-distribution-config --id "$DIST_ID" --query "ETag" --output text)
        aws cloudfront delete-distribution --id "$DIST_ID" --if-match "$ETAG"
    else
        echo "No CloudFront distribution found for this bucket."
    fi

    OAC_ID=$(find_oac_id)
    if [ "$OAC_ID" != "None" ] && [ -n "$OAC_ID" ]; then
        echo "Deleting OAC ${OAC_NAME} ..."
        OAC_ETAG=$(aws cloudfront get-origin-access-control --id "$OAC_ID" --query "ETag" --output text)
        aws cloudfront delete-origin-access-control --id "$OAC_ID" --if-match "$OAC_ETAG"
    fi

    echo "Deleting all objects in s3://${BUCKET_NAME}/ ..."
    aws s3 rm "s3://${BUCKET_NAME}/" --recursive --region "$REGION" 2>/dev/null || true

    echo "Deleting bucket s3://${BUCKET_NAME} ..."
    aws s3 rb "s3://${BUCKET_NAME}" --region "$REGION" 2>/dev/null || true

    echo "Cleanup complete."
    exit 0
fi

# ── Create bucket (private — no public access) ───────────────────────────────

echo "Creating S3 bucket: ${BUCKET_NAME} (region: ${REGION}) ..."

if aws s3api head-bucket --bucket "$BUCKET_NAME" --region "$REGION" 2>/dev/null; then
    echo "  Bucket already exists."
else
    if [ "$REGION" = "us-east-1" ]; then
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION"
    else
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
    fi
    echo "  Bucket created."
fi

# Ensure Block Public Access is ON (bucket stays private)
echo "Ensuring Block Public Access is enabled ..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
        "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# ── Upload CSVs ───────────────────────────────────────────────────────────────

echo "Uploading CSVs from ${SEED_DATA_DIR}/ to s3://${BUCKET_NAME}/${S3_PREFIX}/ ..."

csv_count=0
for csv_file in "${SEED_DATA_DIR}"/*.csv; do
    [ -f "$csv_file" ] || continue
    filename="$(basename "$csv_file")"
    aws s3 cp "$csv_file" "s3://${BUCKET_NAME}/${S3_PREFIX}/${filename}" \
        --region "$REGION" \
        --content-type "text/csv" \
        --quiet
    echo "  ${filename}"
    csv_count=$((csv_count + 1))
done
echo "  Uploaded ${csv_count} CSV files."

# ── Create Origin Access Control ──────────────────────────────────────────────

echo "Creating Origin Access Control ..."
OAC_ID=$(find_oac_id)

if [ "$OAC_ID" != "None" ] && [ -n "$OAC_ID" ]; then
    echo "  OAC already exists: ${OAC_ID}"
else
    OAC_ID=$(aws cloudfront create-origin-access-control \
        --origin-access-control-config "{
            \"Name\": \"${OAC_NAME}\",
            \"Description\": \"OAC for neo4j workshop seed data\",
            \"SigningProtocol\": \"sigv4\",
            \"SigningBehavior\": \"always\",
            \"OriginAccessControlOriginType\": \"s3\"
        }" \
        --query "OriginAccessControl.Id" --output text)
    echo "  Created OAC: ${OAC_ID}"
fi

# ── Create CloudFront distribution ────────────────────────────────────────────

echo "Creating CloudFront distribution ..."
DIST_ID=$(find_distribution_id)

if [ "$DIST_ID" != "None" ] && [ -n "$DIST_ID" ]; then
    echo "  Distribution already exists: ${DIST_ID}"
else
    DIST_CONFIG=$(cat <<DISTEOF
{
    "CallerReference": "neo4j-workshop-$(date +%s)",
    "Comment": "Neo4j workshop seed data CSVs",
    "Enabled": true,
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${BUCKET_NAME}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"]
        },
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        "Compress": true
    },
    "Origins": {
        "Quantity": 1,
        "Items": [
            {
                "Id": "S3-${BUCKET_NAME}",
                "DomainName": "${BUCKET_NAME}.s3.${REGION}.amazonaws.com",
                "OriginAccessControlId": "${OAC_ID}",
                "S3OriginConfig": {
                    "OriginAccessIdentity": ""
                }
            }
        ]
    },
    "DefaultRootObject": "",
    "PriceClass": "PriceClass_100"
}
DISTEOF
    )

    DIST_RESULT=$(aws cloudfront create-distribution --distribution-config "$DIST_CONFIG" --output json)
    DIST_ID=$(echo "$DIST_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['Distribution']['Id'])")
    DIST_DOMAIN=$(echo "$DIST_RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['Distribution']['DomainName'])")
    echo "  Created distribution: ${DIST_ID}"
    echo "  Domain: ${DIST_DOMAIN}"
fi

# ── Set bucket policy to allow CloudFront OAC ─────────────────────────────────

echo "Applying bucket policy for CloudFront OAC ..."
POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipalReadOnly",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::${BUCKET_NAME}/${S3_PREFIX}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::${ACCOUNT_ID}:distribution/${DIST_ID}"
                }
            }
        }
    ]
}
EOF
)
aws s3api put-bucket-policy --bucket "$BUCKET_NAME" --policy "$POLICY"

# ── Output ────────────────────────────────────────────────────────────────────

DIST_DOMAIN=$(aws cloudfront get-distribution --id "$DIST_ID" \
    --query "Distribution.DomainName" --output text)

echo ""
echo "Done."
echo "  S3 bucket:     s3://${BUCKET_NAME}/${S3_PREFIX}/"
echo "  CloudFront:    ${DIST_ID}"
echo "  Base URL:      https://${DIST_DOMAIN}/${S3_PREFIX}/"
echo ""
echo "  Example:       https://${DIST_DOMAIN}/${S3_PREFIX}/companies.csv"
echo ""
echo "Note: CloudFront may take a few minutes to fully deploy."
