#!/usr/bin/env python3
"""
اسکریپت دیباگ - تشخیص دقیق نوع ویدیو از سایت
"""

import os
import sys
import re
import json
import requests
from urllib.parse import urljoin, urlparse

def debug_video_page(url):
    """بررسی کامل صفحه ویدیو و گزارش تمام جزئیات"""
    
    print("=" * 70)
    print("🔍 اسکریپت دیباگ - تشخیص نوع ویدیو")
    print("=" * 70)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://pimpbunny.com/',
    }
    
    session = requests.Session()
    session.headers.update(headers)
    
    # اضافه کردن کوکی (اگر تنظیم شده باشد)
    cookies = os.environ.get('COOKIES')
    if cookies:
        print("🍪 کوکی پیدا شد - اضافه کردن...")
        for cookie in cookies.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                session.cookies.set(name, value)
    
    print(f"\n📄 دریافت صفحه: {url}")
    
    try:
        resp = session.get(url, timeout=30)
        html = resp.text
        print(f"✅ صفحه دریافت شد - طول: {len(html)} کاراکتر")
        
    except Exception as e:
        print(f"❌ خطا در دریافت صفحه: {e}")
        return
    
    # 1. بررسی وضعیت صفحه
    print("\n" + "=" * 70)
    print("📊 بخش 1: وضعیت صفحه")
    print("=" * 70)
    print(f"وضعیت HTTP: {resp.status_code}")
    print(f"نوع محتوا: {resp.headers.get('content-type', 'نامشخص')}")
    
    # 2. جستجوی انواع فرمت‌های ویدیو
    print("\n" + "=" * 70)
    print("🎬 بخش 2: جستجوی لینک‌های ویدیو")
    print("=" * 70)
    
    patterns = {
        'HLS (m3u8)': [
            r'https?://[^\s"\']+\.m3u8[^\s"\']*',
            r'"file"\s*:\s*"([^"]+\.m3u8[^"]*)"',
            r'source:\s*"([^"]+\.m3u8[^"]*)"',
            r'videoUrl:\s*"([^"]+\.m3u8[^"]*)"',
            r'data-video-url="([^"]+\.m3u8[^"]*)"',
            r'hlsUrl\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'playlist:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'src:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        ],
        'Direct MP4': [
            r'https?://[^\s"\']+\.mp4[^\s"\']*',
            r'"video"\s*:\s*"([^"]+\.mp4[^"]*)"',
            r'data-video="([^"]+\.mp4[^"]*)"',
        ],
        'DASH (mpd)': [
            r'https?://[^\s"\']+\.mpd[^\s"\']*',
            r'dashUrl\s*[:=]\s*["\']([^"\']+\.mpd[^"\']*)["\']',
        ],
        'TS Segments': [
            r'https?://[^\s"\']+\.ts[^\s"\']*',
        ],
        'M3U8 without extension': [
            r'["\'](https?://[^"\']+)[^"\']*?(?:hls|stream|video|playlist)[^"\']*["\']',
        ],
    }
    
    found_anything = False
    
    for format_name, pattern_list in patterns.items():
        found_urls = []
        for pattern in pattern_list:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                url_clean = match if isinstance(match, str) else match[0]
                # اصلاح URL
                if url_clean.startswith('//'):
                    url_clean = 'https:' + url_clean
                elif url_clean.startswith('/'):
                    url_clean = urljoin(url, url_clean)
                if url_clean not in found_urls:
                    found_urls.append(url_clean)
        
        if found_urls:
            found_anything = True
            print(f"\n✅ {format_name}: {len(found_urls)} لینک پیدا شد")
            for i, video_url in enumerate(found_urls[:5]):  # فقط 5 تای اول
                print(f"   {i+1}. {video_url[:120]}...")
    
    if not found_anything:
        print("\n❌ هیچ لینک ویدیویی با الگوهای معمول پیدا نشد!")
    
    # 3. بررسی جاوااسکریپت
    print("\n" + "=" * 70)
    print("📜 بخش 3: آنالیز جاوااسکریپت")
    print("=" * 70)
    
    # پیدا کردن تمام تگ‌های script
    script_tags = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.IGNORECASE)
    print(f"تعداد تگ‌های script: {len(script_tags)}")
    
    # جستجوی متغیرهای مرتبط با ویدیو
    video_keywords = ['video', 'hls', 'stream', 'player', 'source', 'src', 'file', 'url', 'playlist', 'manifest']
    found_vars = []
    
    for script in script_tags:
        for keyword in video_keywords:
            pattern = rf'(\w+)\s*[=:]\s*["\']([^"\']+\.(?:m3u8|mp4|mpd|ts)[^"\']*)["\']'
            matches = re.findall(pattern, script, re.IGNORECASE)
            for var_name, var_value in matches:
                if keyword.lower() in var_name.lower() or keyword.lower() in var_value.lower():
                    found_vars.append((var_name, var_value))
    
    if found_vars:
        print(f"\n🔧 متغیرهای پیدا شده در جاوااسکریپت:")
        for var_name, var_value in found_vars[:10]:
            print(f"   {var_name} = {var_value[:100]}")
    else:
        print("❌ هیچ متغیر مرتبطی پیدا نشد")
    
    # 4. بررسی iframe ها
    print("\n" + "=" * 70)
    print("🖼️ بخش 4: بررسی iframe ها")
    print("=" * 70)
    
    iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
    print(f"تعداد iframe: {len(iframes)}")
    for iframe_url in iframes:
        print(f"   🔗 {iframe_url}")
        
        # تلاش برای دریافت محتوای iframe
        try:
            iframe_full_url = urljoin(url, iframe_url)
            iframe_resp = session.get(iframe_full_url, timeout=10)
            iframe_html = iframe_resp.text
            
            # جستجوی m3u8 در iframe
            m3u8_in_iframe = re.findall(r'https?://[^\s"\']+\.m3u8', iframe_html, re.IGNORECASE)
            if m3u8_in_iframe:
                print(f"   ✅ m3u8 در iframe پیدا شد: {m3u8_in_iframe[0]}")
        except:
            pass
    
    # 5. بررسی هدرهای response
    print("\n" + "=" * 70)
    print("📡 بخش 5: هدرهای پاسخ")
    print("=" * 70)
    
    important_headers = ['content-type', 'x-frame-options', 'cf-ray', 'server', 'set-cookie']
    for header in important_headers:
        if header in resp.headers:
            value = resp.headers[header][:100]  # فقط 100 کاراکتر اول
            print(f"   {header}: {value}")
    
    # 6. بررسی API calls (XHR/Fetch)
    print("\n" + "=" * 70)
    print("🔄 بخش 6: جستجوی درخواست‌های API")
    print("=" * 70)
    
    # جستجوی الگوهای api در html
    api_patterns = [
        r'api\.\w+\.com/[^\s"\']+',
        r'/api/[^\s"\']+',
        r'fetch\s*\(\s*["\']([^"\']+)["\']',
        r'XMLHttpRequest.*\.open\(["\'][^"\']+["\'],\s*["\']([^"\']+)["\']',
    ]
    
    api_urls = []
    for pattern in api_patterns:
        matches = re.findall(pattern, html, re.IGNORECASE)
        api_urls.extend(matches)
    
    if api_urls:
        print(f"🔗 {len(set(api_urls))} لینک API احتمالی:")
        for api_url in list(set(api_urls))[:5]:
            print(f"   {api_url[:100]}")
    
    # 7. نتیجه‌گیری نهایی
    print("\n" + "=" * 70)
    print("🎯 بخش 7: نتیجه‌گیری")
    print("=" * 70)
    
    if not found_anything:
        print("""
⚠️ هیچ لینک مستقیم ویدیویی پیدا نشد!

احتمال‌ها:
1. سایت از WebRTC استفاده می‌کند (دانلود تقریباً غیرممکن)
2. ویدیو با JavaScript داینامیک لود می‌شود (نیاز به مرورگر واقعی)
3. سایت نیاز به احراز هویت (اشتراک فعال) دارد
4. ویدیو از CDN خاصی می‌آید که نیاز به referer و کوکی دارد

🔧 راه‌حل پیشنهادی:
1. حتماً کوکی حساب پرمیوم را به GitHub Secrets اضافه کنید
2. از ابزار yt-dlp با کیفیت پایین‌تر استفاده کنید:
   yt-dlp --no-check-certificate --referer "URL" "URL"
3. ویدیو را با OBS Studio ضبط کنید (آخرین راه)
""")
    else:
        print("""
✅ لینک ویدیو پیدا شد!

حالا می‌توانید یکی از این روش‌ها را استفاده کنید:
1. اگر m3u8 پیدا شده: از ffmpeg استفاده کنید
2. اگر mp4 پیدا شده: مستقیماً دانلود کنید
3. اگر چیزی پیدا نشد: از روش yt-dlp استفاده کنید

برای دانلود خودکار، مطمئن شوید کوکی در GitHub Secrets تنظیم شده است.
""")
    
    # ذخیره نتایج در فایل
    with open('debug_result.json', 'w') as f:
        json.dump({
            'url': url,
            'status_code': resp.status_code,
            'content_type': resp.headers.get('content-type', ''),
            'found_anything': found_anything
        }, f, indent=2)
    
    print("\n📁 نتایج دیباگ در فایل debug_result.json ذخیره شد")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_video.py <video_page_url>")
        print("Example: python debug_video.py 'https://pimpbunny.com/videos/...'")
        sys.exit(1)
    
    debug_video_page(sys.argv[1])
