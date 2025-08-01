import logging
import random
import string
from datetime import datetime
from django.core.files.base import ContentFile
from import_export.resources import modelresource_factory
from django.core.files.storage import default_storage


def generate_random_id(length=8) -> str:
    """Generate a random alphanumeric ID of given length."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def get_export_filepath(model) -> str:
    """Generate timestamped file path with random ID for model export (JSON)."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    random_id = generate_random_id()
    return f"exports/{model.__name__.lower()}_{timestamp}_{random_id}.json"


def export_model_data(model):
    """Export model data as JSON dataset."""
    resource_cls = modelresource_factory(model=model)
    return resource_cls().export()


def save_export_to_storage(file_path: str, content: bytes) -> str:
    """Save export content to default storage and return file URL."""
    content_file = ContentFile(content)
    default_storage.save(file_path, content_file)
    return default_storage.url(file_path)


def export_model_to_s3(model) -> str:
    """Export all records of model as JSON to S3 with logging."""
    try:
        dataset = export_model_data(model)
        file_path = get_export_filepath(model)
        url = save_export_to_storage(file_path, dataset.json.encode("utf-8"))
        print(f"EXPORT SUCCESS for {model.__name__}: {file_path}")
        return url
    except Exception as e:
        print(f"EXPORT FAILED for {model.__name__}: {e}")
        raise
