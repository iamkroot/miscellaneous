from PIL import Image
from pathlib import Path
from datetime import datetime


def get_dt(img_path: Path) -> datetime:
    img = Image.open(img_path)
    exif_data = img._getexif()
    try:
        date_time = exif_data[36867]  # Date taken
    except KeyError:
        date_time = exif_data[306]  # Date created
    return datetime.strptime(date_time, "%Y:%m:%d %H:%M:%S")


fold = Path("D:/pics")
pics = fold.glob("*.jpg")

for i, pic_path in enumerate(sorted(pics, key=get_dt), 1):
    pic_path.rename(pic_path.with_name(f"{i:03}.jpg"))
