import os
import shutil
import tempfile
from typing import List


IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


def create_temp_folder(prefix: str):
    return tempfile.mkdtemp(prefix=prefix)


def save_uploaded_files(uploaded_files: List, target_folder: str):
    os.makedirs(target_folder, exist_ok=True)

    for file in uploaded_files:
        file_path = os.path.join(target_folder, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

    return target_folder


def prepare_upload_folder(uploaded_files, prefix="uploaded_"):
    if not uploaded_files:
        return None

    temp_folder = create_temp_folder(prefix)
    save_uploaded_files(uploaded_files, temp_folder)
    return temp_folder


def clear_temp_folder(folder_path):
    if folder_path and os.path.exists(folder_path):
        shutil.rmtree(folder_path)


# ✅ NEW
def folder_has_images(folder_path):
    """
    Check if folder exists and contains image files
    """
    if not folder_path:
        return False

    if not os.path.exists(folder_path):
        return False

    for file in os.listdir(folder_path):
        if file.lower().endswith(IMAGE_EXTENSIONS):
            return True

    return False
