#!/usr/bin/env python3
"""
تبدیل فایل ویدیو به قطعات ۸۰ مگابایتی زیپ شده با رمز
هنگام استخراج فایل اول، بقیه خودکار متصل می‌شوند
"""

import os
import sys
import subprocess
from pathlib import Path

def split_and_zip(file_path, part_size_mb=80, password="mkml00"):
    """
    تقسیم فایل به قطعات زیپ رمزدار
    """
    if not os.path.exists(file_path):
        print(f"❌ فایل {file_path} پیدا نشد")
        return False
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"📊 حجم فایل: {file_size_mb:.2f} MB")
    
    base_name = os.path.splitext(file_path)[0]
    zip_file = f"{base_name}.zip"
    
    # مرحله 1: ساخت زیپ رمزدار
    print(f"🔐 ساخت زیپ با رمز {password}...")
    cmd_zip = [
        "zip",
        "-P", password,
        "-j",  # مسیرها را ذخیره نکن
        zip_file,
        file_path
    ]
    subprocess.run(cmd_zip, check=True)
    
    # مرحله 2: تقسیم زیپ به قطعات
    print(f"✂️ تقسیم به قطعات {part_size_mb} مگابایتی...")
    cmd_split = [
        "split",
        "-b", f"{part_size_mb}M",
        zip_file,
        f"{base_name}.zip.part-"
    ]
    subprocess.run(cmd_split, check=True)
    
    # مرحله 3: حذف زیپ اصلی
    os.remove(zip_file)
    
    # مرحله 4: شماره‌گذاری مجدد قطعات
    parts = sorted([f for f in os.listdir('.') if f.startswith(f"{base_name}.zip.part-")])
    
    # تغییر نام برای خوانایی بهتر
    for i, part in enumerate(parts, 1):
        new_name = f"{base_name}.zip.{(i-1):03d}"
        os.rename(part, new_name)
        size_mb = os.path.getsize(new_name) / (1024 * 1024)
        print(f"  📄 {new_name} - {size_mb:.2f} MB")
    
    # مرحله 5: فایل راهنما
    readme = f"""# راهنمای استخراج

رمز تمام فایل‌ها: {password}

روش استخراج در لینوکس/مک:
    cat {base_name}.zip.* > {base_name}.zip
    unzip -P {password} {base_name}.zip

روش استخراج در ویندوز (با 7-Zip):
    1. فایل {base_name}.zip.000 را انتخاب کنید
    2. راست کلیک → 7-Zip → Extract Here
    3. رمز {password} را وارد کنید

توجه: برای استخراج فقط به فایل اول نیاز دارید، بقیه قطعات خودکار شناسایی می‌شوند.
"""
    
    with open(f"{base_name}_README.txt", "w") as f:
        f.write(readme)
    
    print(f"\n✅ {len(parts)} قطعه ساخته شد")
    print(f"📝 فایل راهنما: {base_name}_README.txt")
    print(f"🔑 رمز: {password}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_and_zip.py <video_file> [part_size_mb] [password]")
        print("Example: python split_and_zip.py video.mp4 80 mkml00")
        sys.exit(1)
    
    video_file = sys.argv[1]
    part_size = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    password = sys.argv[3] if len(sys.argv) > 3 else "mkml00"
    
    if split_and_zip(video_file, part_size, password):
        print("\n🎉 عملیات موفق! فایل‌ها آماده آپلود هستند.")
    else:
        print("\n❌ خطا در فرآیند")
        sys.exit(1)
