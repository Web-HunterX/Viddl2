#!/usr/bin/env python3
"""
دانلود ویدیو با بالاترین کیفیت ممکن
"""

import os
import sys
import subprocess

def download_video(url, output_name):
    """دانلود ویدیو با yt-dlp با بالاترین کیفیت"""
    
    if not output_name:
        output_name = "video_output"
    
    output_template = f"{output_name}.%(ext)s"
    
    # گزینه‌های yt-dlp برای بهترین کیفیت
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",  # بهترین ویدیو + بهترین صدا
        "--merge-output-format", "mp4",     # نهایی MP4
        "-o", output_template,
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://pimpbunny.com/",
    ]
    
    # Add cookies if provided
    cookies = os.environ.get('COOKIES')
    if cookies:
        with open('cookies.txt', 'w') as f:
            f.write(cookies)
        cmd.extend(["--cookies", "cookies.txt"])
    
    cmd.append(url)
    
    print(f"🚀 شروع دانلود از: {url}")
    print(f"📁 خروجی: {output_template}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # پیدا کردن فایل دانلود شده
            for file in os.listdir('.'):
                if file.startswith(output_name) and file.endswith('.mp4'):
                    print(f"✅ دانلود شد: {file}")
                    return file
        else:
            print(f"❌ خطا در دانلود: {result.stderr}")
            
            # روش دوم: تلاش با کیفیت پایین‌تر
            print("🔄 تلاش با کیفیت پایین‌تر...")
            cmd[2] = "best"  # فقط best به جای bestvideo+bestaudio
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                for file in os.listdir('.'):
                    if file.startswith(output_name) and file.endswith('.mp4'):
                        print(f"✅ دانلود شد: {file}")
                        return file
        
        return None
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <url> [output_name]")
        sys.exit(1)
    
    url = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "video_output"
    
    result = download_video(url, output_name)
    if result:
        print(f"🎉 دانلود نهایی: {result}")
    else:
        print("💀 دانلود ناموفق")
        sys.exit(1)
