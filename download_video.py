#!/usr/bin/env python3
"""
دانلود ویدیو با روش مستقیم - مخصوص سایت pimpbunny
"""

import os
import sys
import re
import json
import requests
import subprocess
from urllib.parse import urljoin, urlparse

def download_video_direct(url, output_name):
    """روش مستقیم برای دانلود از pimpbunny"""
    
    if not output_name:
        output_name = "video_output"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://pimpbunny.com/',
        'Origin': 'https://pimpbunny.com'
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # اضافه کردن کوکی از环境变量
    cookies = os.environ.get('COOKIES')
    if cookies:
        for cookie in cookies.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                session.cookies.set(name, value)
    
    print(f"🌐 دریافت صفحه: {url}")
    
    try:
        # دریافت صفحه اصلی
        resp = session.get(url, timeout=30)
        html = resp.text
        
        # روش 1: دنبال m3u8 بگرد
        m3u8_patterns = [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'"file"\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r'source:\s*"([^"]+\.m3u8[^"]*)"',
            r'videoUrl:\s*"([^"]+\.m3u8[^"]*)"',
            r'data-video-url="([^"]+\.m3u8[^"]*)"'
        ]
        
        m3u8_url = None
        for pattern in m3u8_patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                m3u8_url = match.group(1) if match.lastindex else match.group(0)
                # اطمینان از کامل بودن URL
                if m3u8_url.startswith('//'):
                    m3u8_url = 'https:' + m3u8_url
                elif m3u8_url.startswith('/'):
                    m3u8_url = urljoin(url, m3u8_url)
                print(f"✅ m3u8 پیدا شد: {m3u8_url}")
                break
        
        # روش 2: دنبال دیتا در جاوااسکریپت بگرد
        if not m3u8_url:
            # دنبال مقادیر در شی‌های جاوااسکریپت
            js_vars = re.findall(r'var\s+(\w+)\s*=\s*["\']([^"\']+\.m3u8[^"\']+)["\']', html)
            for var_name, var_url in js_vars:
                if '.m3u8' in var_url:
                    m3u8_url = var_url
                    print(f"✅ m3u8 در متغیر {var_name} پیدا شد")
                    break
        
        # روش 3: دنبال در iframe
        if not m3u8_url:
            iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            if iframe_match:
                iframe_url = urljoin(url, iframe_match.group(1))
                print(f"🔄 بررسی iframe: {iframe_url}")
                iframe_resp = session.get(iframe_url, timeout=30)
                m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8', iframe_resp.text, re.IGNORECASE)
                if m3u8_match:
                    m3u8_url = m3u8_match.group(0)
                    print(f"✅ m3u8 در iframe پیدا شد")
        
        if not m3u8_url:
            print("❌ هیچ m3u8 پیدا نشد")
            print("🔍 لطفاً دستی از Developer Tools لینک m3u8 رو پیدا کنید:")
            print("   1. F12 بزنید")
            print("   2. تب Network رو باز کنید")
            print("   3. فیلتر بگذارید روی 'm3u8'")
            print("   4. ویدیو رو پلی کنید")
            print("   5. لینک رو کپی کنید و به عنوان آرگومان دوم بدید")
            return None
        
        # دانلود با ffmpeg (بهترین روش برای m3u8)
        output_file = f"{output_name}.mp4"
        
        cmd = [
            "ffmpeg",
            "-i", m3u8_url,
            "-c", "copy",
            "-bsf:a", "aac_adtstoasc",
            "-user_agent", headers['User-Agent'],
            "-referer", url,
            output_file,
            "-y"  # overwrite
        ]
        
        print(f"🎬 شروع دانلود با ffmpeg...")
        print(f"📥 منبع: {m3u8_url}")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(output_file):
            # بررسی حجم فایل
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"✅ دانلود کامل شد: {output_file}")
            print(f"📊 حجم: {size_mb:.2f} MB")
            return output_file
        else:
            print(f"❌ خطا در ffmpeg: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ خطا: {e}")
        return None

def download_with_ytdlp_fallback(url, output_name):
    """روش دوم: استفاده از yt-dlp با تنظیمات خاص"""
    
    output_template = f"{output_name}.%(ext)s"
    
    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "--referer", "https://pimpbunny.com/",
        "--add-header", "Origin:https://pimpbunny.com",
        "-f", "best",
        "-o", output_template,
        "--ignore-errors",
        "--no-warnings",
        url
    ]
    
    print("🔄 تلاش با yt-dlp...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        for file in os.listdir('.'):
            if file.startswith(output_name) and file.endswith('.mp4'):
                return file
    
    print("❌ yt-dlp هم کار نکرد")
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <url> [output_name]")
        print("Example: python download_video.py 'https://pimpbunny.com/videos/...' video_output")
        sys.exit(1)
    
    url = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "video_output"
    
    # تصحیح لینک اگر اشتباه وارد شده
    if "pimbunny" in url:
        url = url.replace("pimbunny", "pimpbunny")
        print(f"🔧 لینک تصحیح شد: {url}")
    
    # روش اول: مستقیم
    result = download_video_direct(url, output_name)
    
    # روش دوم: fallback
    if not result:
        print("🔄 روش دوم...")
        result = download_with_ytdlp_fallback(url, output_name)
    
    if result:
        print(f"🎉 موفق: {result}")
        # ایجاد فایل marker برای مراحل بعدی
        with open("download_success.txt", "w") as f:
            f.write(result)
    else:
        print("💀 دانلود ناموفق")
        print("\nراهنمایی دستی:")
        print("1. مرورگر رو باز کنید و به صفحه ویدیو برید")
        print("2. F12 بزنید -> تب Network")
        print("3. فیلتر بگذارید 'm3u8'")
        print("4. صفحه رو رفرش کنید و ویدیو رو پلی کنید")
        print("5. روی فایل .m3u8 کلیک راست -> Copy -> Copy URL")
        print("6. لینک رو به عنوان آرگومان دوم به اسکریپت بدید:")
        print(f"   python download_video.py 'لینک_m3u8' {output_name}")
        sys.exit(1)
