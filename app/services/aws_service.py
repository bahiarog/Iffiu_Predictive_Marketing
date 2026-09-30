# AWS SERVICE DISABLED - all integrations removed
# Original file backed up as aws_service.py.bak

import logging
logger = logging.getLogger(__name__)

def upload_to_s3(*args, **kwargs):
    logger.warning("AWS disabled - upload_to_s3 called but no-op")
    return None

def get_presigned_url(*args, **kwargs):
    logger.warning("AWS disabled")
    return None

def trigger_analysis(*args, **kwargs):
    logger.warning("AWS disabled - trigger_analysis no-op")
    return {"execution_arn": None, "execution_name": None}

def poll_sqs_messages(*args, **kwargs):
    logger.warning("AWS disabled")
    return []

def run_rekognition_image(*args, **kwargs):
    logger.warning("AWS disabled")
    return {}
