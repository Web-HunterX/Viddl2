#!/usr/bin/env python3
"""
ویدیو دانلودر هوشمند - تشخیص خودکار نوع ویدیو و انتخاب بهترین روش دانلود
پشتیبانی از: HLS (m3u8), MP4 مستقیم, DASH (mpd), و سایت‌های محافظت شده
"""

import os
import sys
import re
import json
import requests
import subprocess
import mimetypes
from urllib.parse import urljoin, urlparse, unquote
import time

class SmartVideoDownloader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # اضافه کردن کوکی از محیط
        cookies = os.environ.get('COOKIES')
        if cookies:
            for cookie in cookies.split(';'):
                if '=' in cookie:
                    name, value = cookie.strip().split('=', 1)
                    self.session.cookies.set(name, value)
    
    def detect_video_urls_from_page(self, url):
        """استخراج تمام لینک‌های ویدیو از صفحه"""
        print(f"🔍 آنالیز صفحه: {url}")
        
        try:
            resp = self.session.get(url, timeout=30)
            html = resp.text
            
            found_urls = {
                'm3u8': [],
                'mp4': [],
                'mpd': [],
                'other': []
            }
            
            # الگوهای جستجو برای m3u8
            m3u8_patterns = [
                r'https?://[^\s"\']+\.m3u8[^\s"\']*',
                r'"file"\s*:\s*"([^"]+\.m3u8[^"]*)"',
                r'source:\s*"([^"]+\.m3u8[^"]*)"',
                r'videoUrl:\s*"([^"]+\.m3u8[^"]*)"',
                r'data-video-url="([^"]+\.m3u8[^"]*)"',
                r'hlsUrl\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'playlist:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'src:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            ]
            
            # الگوهای جستجو برای mp4
            mp4_patterns = [
                r'https?://[^\s"\']+\.mp4[^\s"\']*',
                r'"video"\s*:\s*"([^"]+\.mp4[^"]*)"',
                r'data-video="([^"]+\.mp4[^"]*)"',
            ]
            
            # الگوهای جستجو برای mpd (DASH)
            mpd_patterns = [
                r'https?://[^\s"\']+\.mpd[^\s"\']*',
                r'dashUrl\s*[:=]\s*["\']([^"\']+\.mpd[^"\']*)["\']',
            ]
            
            # جستجو در HTML
            for pattern in m3u8_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    url_clean = match if isinstance(match, str) else match[0]
                    if url_clean.startswith('//'):
                        url_clean = 'https:' + url_clean
                    elif url_clean.startswith('/'):
                        url_clean = urljoin(url, url_clean)
                    if url_clean not in found_urls['m3u8']:
                        found_urls['m3u8'].append(url_clean)
            
            for pattern in mp4_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    url_clean = match if isinstance(match, str) else match[0]
                    if url_clean.startswith('//'):
                        url_clean = 'https:' + url_clean
                    elif url_clean.startswith('/'):
                        url_clean = urljoin(url, url_clean)
                    if url_clean not in found_urls['mp4']:
                        found_urls['mp4'].append(url_clean)
            
            for pattern in mpd_patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                for match in matches:
                    url_clean = match if isinstance(match, str) else match[0]
                    if url_clean.startswith('//'):
                        url_clean = 'https:' + url_clean
                    elif url_clean.startswith('/'):
                        url_clean = urljoin(url, url_clean)
                    if url_clean not in found_urls['mpd']:
                        found_urls['mpd'].append(url_clean)
            
            # جستجو در جاوااسکریپت
            js_blocks = re.findall(r'<script[^>]*>([^<]+)</script>', html, re.IGNORECASE)
            for js in js_blocks:
                # دنبال variable assignments
                var_pattern = r'var\s+(\w+)\s*=\s*["\']([^"\']+\.(?:m3u8|mp4|mpd)[^"\']*)["\']'
                matches = re.findall(var_pattern, js, re.IGNORECASE)
                for var_name, var_url in matches:
                    if '.m3u8' in var_url and var_url not in found_urls['m3u8']:
                        found_urls['m3u8'].append(var_url)
                    elif '.mp4' in var_url and var_url not in found_urls['mp4']:
                        found_urls['mp4'].append(var_url)
                    elif '.mpd' in var_url and var_url not in found_urls['mpd']:
                        found_urls['mpd'].append(var_url)
            
            return found_urls
            
        except Exception as e:
            print(f"⚠️ خطا در آنالیز صفحه: {e}")
            return {'m3u8': [], 'mp4': [], 'mpd': [], 'other': []}
    
    def check_if_accessible(self, url, method='head'):
        """بررسی اینکه آیا یک URL قابل دسترسی است"""
        try:
            if method == 'head':
                resp = self.session.head(url, timeout=10, allow_redirects=True)
            else:
                resp = self.session.get(url, timeout=10, stream=True)
                resp.close()
            
            if resp.status_code == 200:
                return True
            elif resp.status_code == 403:
                # ممکنه نیاز به هدر خاص داشته باشه
                return 'maybe'
            return False
        except:
            return False
    
    def get_best_quality_m3u8(self, m3u8_url):
        """پیدا کردن بهترین کیفیت در m3u8"""
        try:
            resp = self.session.get(m3u8_url, timeout=15)
            content = resp.text
            
            # بررسی وجود کیفیت‌های مختلف
            variant_pattern = r'#EXT-X-STREAM-INF.*?RESOLUTION=\d+x(\d+).*?\n(.*?\.m3u8)'
            variants = re.findall(variant_pattern, content, re.DOTALL)
            
            if variants:
                # پیدا کردن بهترین کیفیت (بزرگترین ارتفاع)
                best_quality = max(variants, key=lambda x: int(x[0]))
                best_url = urljoin(m3u8_url, best_quality[1])
                print(f"🎯 بهترین کیفیت پیدا شد: {best_quality[0]}p")
                return best_url
            
            # اگر کیفیت‌های مختلف نبود، خود m3u8 رو برمیگردونیم
            return m3u8_url
            
        except Exception as e:
            print(f"⚠️ خطا در آنالیز کیفیت: {e}")
            return m3u8_url
    
    def download_with_ffmpeg(self, video_url, output_file, referer=None):
        """روش اصلی: دانلود با ffmpeg (بهترین روش برای m3u8)"""
        
        headers = []
        if referer:
            headers.extend(['-headers', f'Referer: {referer}\r\nUser-Agent: {self.session.headers["User-Agent"]}\r\n'])
        
        cmd = [
            'ffmpeg',
            '-i', video_url,
            '-c', 'copy',
            '-bsf:a', 'aac_adtstoasc',
            '-user_agent', self.session.headers['User-Agent'],
        ]
        
        if referer:
            cmd.extend(['-referer', referer])
        
        cmd.extend([output_file, '-y'])
        
        print(f"🎬 شروع دانلود با ffmpeg...")
        print(f"📥 منبع: {video_url[:100]}...")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                size_mb = os.path.getsize(output_file) / (1024 * 1024)
                print(f"✅ دانلود موفق: {output_file} ({size_mb:.2f} MB)")
                return True
            else:
                if result.stderr:
                    print(f"⚠️ خطای ffmpeg: {result.stderr[:500]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ زمان دانلود به پایان رسید (10 دقیقه)")
            return False
        except Exception as e:
            print(f"❌ خطا: {e}")
            return False
    
    def download_direct_mp4(self, mp4_url, output_file, referer=None):
        """دانلود مستقیم MP4 با resume capability"""
        print(f"⬇ دانلود MP4 مستقیم...")
        
        headers = {}
        if referer:
            headers['Referer'] = referer
        
        try:
            resp = self.session.get(mp4_url, stream=True, headers=headers)
            total_size = int(resp.headers.get('content-length', 0))
            
            with open(output_file, 'wb') as f:
                downloaded = 0
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"\rپیشرفت: {percent:.1f}% - {downloaded/(1024*1024):.1f} MB", end='')
            
            print(f"\n✅ دانلود موفق: {output_file}")
            return True
            
        except Exception as e:
            print(f"\n❌ خطا: {e}")
            return False
    
    def download_with_ytdlp(self, url, output_file):
        """روش کمکی: استفاده از yt-dlp"""
        print("🔄 تلاش با yt-dlp...")
        
        cmd = [
            'yt-dlp',
            '-f', 'bestvideo+bestaudio/best',
            '--merge-output-format', 'mp4',
            '-o', output_file,
            '--user-agent', self.session.headers['User-Agent'],
            '--referer', url,
            '--no-check-certificate',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ دانلود موفق با yt-dlp")
                return True
            else:
                print(f"⚠️ yt-dlp خطا: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ خطای yt-dlp: {e}")
            return False
    
    def smart_download(self, page_url, output_name):
        """عملکرد اصلی: تشخیص هوشمند و دانلود"""
        
        print("=" * 60)
        print("🎬 ویدیو دانلودر هوشمند")
        print("=" * 60)
        
        output_file = f"{output_name}.mp4"
        
        # STEP 1: تشخیص نوع لینک
        if page_url.endswith('.m3u8'):
            print("📋 نوع: لینک مستقیم HLS")
            video_url = self.get_best_quality_m3u8(page_url)
            success = self.download_with_ffmpeg(video_url, output_file, referer=page_url)
            
        elif page_url.endswith('.mp4'):
            print("📋 نوع: لینک مستقیم MP4")
            success = self.download_direct_mp4(page_url, output_file)
            
        elif page_url.endswith('.mpd'):
            print("📋 نوع: لینک مستقیم DASH")
            success = self.download_with_ffmpeg(page_url, output_file)
            
        else:
            # STEP 2: استخراج از صفحه HTML
            print("📋 نوع: صفحه HTML - در حال استخراج لینک‌ها...")
            found_urls = self.detect_video_urls_from_page(page_url)
            
            print(f"\n📊 نتایج جستجو:")
            print(f"   🎬 m3u8 پیدا شده: {len(found_urls['m3u8'])}")
            print(f"   📹 MP4 پیدا شده: {len(found_urls['mp4'])}")
            print(f"   📡 MPD پیدا شده: {len(found_urls['mpd'])}")
            
            all_videos = []
            for vtype, urls in found_urls.items():
                for url in urls:
                    all_videos.append((vtype, url))
            
            if not all_videos:
                print("❌ هیچ لینک ویدیویی پیدا نشد!")
                print("\n🔍 راهنمایی دستی:")
                print("1. F12 بزنید → تب Network")
                print("2. فیلتر بگذارید 'm3u8' یا 'mp4'")
                print("3. صفحه رو رفرش کنید و ویدیو رو پلی کنید")
                print("4. روی فایل کلیک راست → Copy URL")
                print(f"5. دوباره اجرا کنید با لینک مستقیم")
                return False
            
            # اولویت: m3u8 (کیفیت بالا) > mp4 > mpd
            priority_order = ['m3u8', 'mp4', 'mpd']
            
            success = False
            for vtype in priority_order:
                for url in found_urls[vtype]:
                    print(f"\n🎯 امتحان روش {vtype.upper()}: {url[:80]}...")
                    
                    if vtype == 'm3u8':
                        video_url = self.get_best_quality_m3u8(url)
                        if self.download_with_ffmpeg(video_url, output_file, referer=page_url):
                            success = True
                            break
                    elif vtype == 'mp4':
                        if self.download_direct_mp4(url, output_file, referer=page_url):
                            success = True
                            break
                    elif vtype == 'mpd':
                        if self.download_with_ffmpeg(url, output_file, referer=page_url):
                            success = True
                            break
                
                if success:
                    break
            
            # STEP 3: روش آخر - yt-dlp
            if not success:
                print("\n🔄 روش آخر: تلاش با yt-dlp...")
                success = self.download_with_ytdlp(page_url, output_file)
        
        # نتیجه نهایی
        if success and os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print("\n" + "=" * 60)
            print(f"✨ دانلود با موفقیت کامل شد!")
            print(f"📁 فایل: {output_file}")
            print(f"💾 حجم: {size_mb:.2f} MB")
            print("=" * 60)
            
            # ذخیره نام فایل برای مرحله بعد
            with open("download_success.txt", "w") as f:
                f.write(output_file)
            
            return True
        
        print("\n❌ دانلود ناموفق بود")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_video.py <url> [output_name]")
        print("\nمثال‌ها:")
        print("  python download_video.py 'https://pimpbunny.com/videos/...' video_output")
        print("  python download_video.py 'https://example.com/video.m3u8' my_video")
        print("  python download_video.py 'https://example.com/video.mp4' my_video")
        sys.exit(1)
    
    url = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "video_output"
    
    # تصحیح خودکار لینک
    if "pimbunny" in url:
        url = url.replace("pimbunny", "pimpbunny")
        print(f"🔧 لینک تصحیح شد: {url}")
    
    downloader = SmartVideoDownloader()
    success = downloader.smart_download(url, output_name)
    
    sys.exit(0 if success else 1)
