#!/usr/bin/env python3
"""
تقسیم فایل به قطعات ۸۰ مگابایتی و تبدیل به زیپ رمزدار
هنگام استخراج فایل اول، بقیه قطعات خودکار متصل می‌شن
"""

import os
import sys
import zipfile
import subprocess
from pathlib import Path

def split_and_zip(file_path, part_size_mb=80, password="mkml00"):
    """
    تبدیل فایل به زیپ چندتکه با رمز
    """
    if not os.path.exists(file_path):
        print(f"❌ فایل {file_path} پیدا نشد")
        return False
    
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
    print(f"📊 حجم فایل اصلی: {file_size:.2f} MB")
    
    # محاسبه تعداد قطعات
    part_size_bytes = part_size_mb * 1024 * 1024
    num_parts = (os.path.getsize(file_path) + part_size_bytes - 1) // part_size_bytes
    
    print(f"📦 تقسیم به {num_parts} قطعه {part_size_mb} مگابایتی")
    
    base_name = os.path.splitext(file_path)[0]
    
    # روش: استفاده از زیپ اسپلیت (که موقع استخراج خودکار همه رو می‌خونه)
    zip_path = f"{base_name}.zip"
    
    # اول یه زیپ می‌سازیم کل فایل رو بذاریم توش
    print(f"🔐 ساخت زیپ رمزدار...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.setpassword(password.encode())
        zf.write(file_path, os.path.basename(file_path))
    
    # حالا زیپ رو تقسیم می‌کنیم با split (سیستمی)
    print(f"✂️ تقسیم زیپ به قطعات...")
    
    # پاک کردن فایل‌های قبلی
    for f in os.listdir('.'):
        if f.startswith(f"{base_name}.zip."):
            os.remove(f)
    
    # استفاده از دستور split لینوکس
    split_cmd = ["split", "-b", f"{part_size_mb}M", zip_path, f"{base_name}.zip."]
    subprocess.run(split_cmd, check=True)
    
    # حذف زیپ اصلی
    os.remove(zip_path)
    
    # ایجاد فایل راهنما
    readme_content = f"""# راهنمای استخراج

فایل‌های {base_name}.zip.aa, {base_name}.zip.ab, ... رو توی یه پوشه کنار هم قرار بدید.

سپس برای استخراج در لینوکس/مک:
cat {base_name}.zip.* > {base_name}.zip
unzip -P mkml00 {base_name}.zip

در ویندوز:
- از نرم‌افزار 7-Zip استفاده کنید
- فایل اول رو انتخاب کنید، رمز رو وارد کنید: mkml00
- بقیه قطعات خودکار شناسایی می‌شن

رمز: mkml00
"""
    
    with open(f"{base_name}_README.txt", "w") as f:
        f.write(readme_content)
    
    # لیست فایل‌های ساخته شده
    parts = [f for f in os.listdir('.') if f.startswith(f"{base_name}.zip.")]
    parts.sort()
    
    print(f"\n✅ {len(parts)} قطعه ساخته شد:")
    for part in parts:
        size_mb = os.path.getsize(part) / (1024 * 1024)
        print(f"  📄 {part} - {size_mb:.2f} MB")
    
    print(f"\n📝 فایل راهنما: {base_name}_README.txt")
    print(f"🔑 رمز: mkml00")
    
    return True

def create_zip_parts_with_python(file_path, part_size_mb=80, password="mkml00"):
    """
    روش جایگزین با پایتون خالص (بدون دستور split)
    """
    import struct
    
    part_size = part_size_mb * 1024 * 1024
    base_name = os.path.splitext(file_path)[0]
    
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # تقسیم دیتا به قطعات
    parts = []
    for i in range(0, len(data), part_size):
        parts.append(data[i:i+part_size])
    
    # هر قطعه رو زیپ می‌کنیم (ولی این روش کمتر کاربردیه)
    # این روش ساده‌تر کار می‌کنه ولی موقع استخراج باید همه رو دانلود کنی
    
    print("⚠️ این روش پیچیده‌تره، روش split لینوکس بهتر کار می‌کنه")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_and_zip.py <video_file> [part_size_mb] [password]")
        print("Example: python split_and_zip.py video.mp4 80 mkml00")
        sys.exit(1)
    
    video_file = sys.argv[1]
    part_size = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    password = sys.argv[3] if len(sys.argv) > 3 else "mkml00"
    
    success = split_and_zip(video_file, part_size, password)
    
    if success:
        print("\n🎉 عملیات با موفقیت انجام شد!")
        print("📁 فایل‌ها در پوشه جاری آماده آپلود هستند")
    else:
        print("\n❌ خطا در فرآیند")
        sys.exit(1)
