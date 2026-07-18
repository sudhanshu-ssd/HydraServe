import uuid
from io import BytesIO
from PIL import Image,ImageOps
from starlette.concurrency import run_in_threadpool
import boto3
from config import settings


def process_profile_pic(content:bytes) -> tuple[bytes,str]:
    with Image.open(BytesIO(content)) as org:
        img = ImageOps.exif_transpose(org)

        img = ImageOps.fit(img,size=(300,300),method=Image.Resampling.LANCZOS)

        if img.mode in ['RGBA',"LA","P"]:
            img  = img.convert('RGB')

        filename = f"{uuid.uuid4().hex}.jpg"

        output = BytesIO()
        
        img.save(output,'jpeg',quality = 85,optimize = True)
        output.seek(0)

        return output.read(),filename
    
def _get_s3():
    return boto3.client(
        's3',
        aws_access_key_id = (
            settings.s3_access_key.get_secret_value() if settings.s3_access_key else None
        ),
        aws_secret_access_key = (
            settings.s3_secret_access_key.get_secret_value() if settings.s3_secret_access_key else None
        ),
        endpoint_url = settings.s3_endpoint_url
        )

def upload_to_s3(raw_bytes: bytes,key : str):
    s3 = _get_s3()
    s3.upload_fileobj(
        BytesIO(raw_bytes),
        settings.s3_bucket_name,
        key,
        ExtraArgs = {"ContentType":"image/jpeg"}
    )

def delete_from_s3(key):
    s3 = _get_s3()
    s3.delete_object(Bucket = settings.s3_bucket_name,Key = key)


async def upload_profile_image(raw_bytes : bytes ,filename):
    key = f"profile_pics/{filename}"
    await run_in_threadpool(upload_to_s3,raw_bytes,key)

async def delete_profile_image(filename):
    key = f"profile_pics/{filename}"
    await run_in_threadpool(delete_from_s3,key)