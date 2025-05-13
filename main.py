import requests
import time
import threading
import hashlib
import base64
import urllib.parse
import random

# URL GitHub untuk mengambil cookies secara langsung
URL_GITHUB_COOKIES = "https://raw.githubusercontent.com/ImanaTahira/my-cookies/main/cookies.txt"

class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate  # Permintaan per detik
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens=1):
        with self.lock:
            current_time = time.time()
            elapsed = current_time - self.last_refill
            self.tokens += elapsed * self.rate
            self.tokens = min(self.tokens, self.capacity)
            self.last_refill = current_time

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

bucket = TokenBucket(rate=1, capacity=5)  # Maksimal 5 request per detik

def generate_device_id(seed="random_seed"):
    """
    Menghasilkan device_id yang mirip dengan format yang diberikan menggunakan hashing SHA-256 dan base64 encoding.
    """
    hash_object = hashlib.sha256(seed.encode('utf-8'))
    hash_digest = hash_object.digest()
    base64_encoded = base64.b64encode(hash_digest).decode('utf-8')
    device_id = urllib.parse.quote(base64_encoded)
    return f"device_id={device_id}"

def load_cookies_from_github(url):
    cookies_list = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        for line in response.text.splitlines():
            cookies = {}
            line = line.strip()
            for cookie in line.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
            cookies_list.append(cookies)
        print("✅ Cookies berhasil diambil dari GitHub!")
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil cookies dari GitHub: {e}")
        exit(1)
    return cookies_list

def send_request_with_retry(url, cookies, headers, json_data=None, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = requests.post(url, cookies=cookies, headers=headers, json=json_data, timeout=10)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Percobaan {attempt + 1} gagal: {e}")
            if attempt < retries - 1:
                time.sleep(float(delay))
            else:
                raise

def send_message(session_id, cookies, uuid, usersig, content, delay_between_cookies):
    if not content:
        print("❌ Konten pesan tidak boleh kosong!")
        return
    url = f"https://live.shopee.co.id/api/v1/session/{session_id}/message"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US,en;q=0.9',
        'af-ac-enc-dat': '001ed94da16d0da5',
        'client-info': 'platform=9;device_id=9WKYLbnCkcojeuzaOGw7bKz1BScokjgs',
        'content-type': 'application/json',
        'origin': f'https://live.shopee.co.id',
        'priority': 'u=1, i',
        'referer': f'https://live.shopee.co.id/pc/live?session={session_id}',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'x-sz-sdk-version': '1.10.7',
    }
    json_data = {
        'uuid': uuid,
        'usersig': usersig,
        'content': f'{{"type":100,"content":"{content}"}}'
    }
    try:
        response = send_request_with_retry(url, cookies, headers, json_data)
        print(f"[Session {session_id} - message] Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error saat mengirim pesan: {e}")
    time.sleep(delay_between_cookies)

def send_buy(session_id, cookies, delay_between_cookies):
    url = f"https://live.shopee.co.id/api/v1/session/{session_id}/msg/buy"
    headers = {
        'Host': 'live.shopee.co.id',
        'content-type': 'application/json',
        'af-ac-enc-sz-token': 'W/7cnpqnzoCyF+lhzNaGww==|e0Or76J++iAwKEY5D7jdnvVa3x4+YA79WFbS1nwRpZptc1yEbiUWDQypIzNy8DbcJrfXgEJEBDL08786VaCBYTrm|qZwGsqPlceTcfYQx|08|2',
        'client-info': 'device_id=340F15B9537241468F99AB600714F518;device_model=iPhone15%2C3;os=1;os_version=18.1;client_version=33830;platform=4;app_type=1;language=id',
        '7c9338be': 's4/LUfo1PYNo8qRlNsmWQfn1Wg8=',
        'x-sap-ri': '60d13d67bfa1a46029de4d2701f1efe283d90687a9d6aa85029e',
        'x-sap-type': '2',
        'x-livestreaming-auth': 'ls_ios_v1_20001_1732104544_340F15B9537241468F99AB600714F518-1732104544973-648015|b6nhvOV9vpGJtmlJPX0ESaP4LEUvG/TmbeNcI6mbqgg=',
        'x-ls-sz-token': 'W/7cnpqnzoCyF+lhzNaGww==|e0Or76J++iAwKEY5D7jdnvVa3x4+YA79WFbS1nwRpZptc1yEbiUWDQypIzNy8DbcJrfXgEJEBDL08786VaCBYTrm|qZwGsqPlceTcfYQx|08|2',
        'bc059e12': 'kAU/ZzTwm1jBXip83UC3rcFGa7Q=',
        'client-request-id': '8dddae0f-a4fc-4361-a777-5545f1a4c6f1.1052',
        'x-livestreaming-source': 'shopee',
        'user-agent': 'language=id app_type=1 platform=native_ios appver=33830 os_ver=18.1.0 Cronet/102.0.5005.61',
        'x-shopee-client-timezone': 'Asia/Jakarta',
        '4454a6b9': 'PXzpMwmVvOzbw3mCPkiciaSN2bo7CnQwGQ0GcE83NNCjJy46LHsJ2gaqhKxEto2oAsgXCtorsB21o/ie8N/36koOXd/LXSfUF5wj6wEFxqeVEnQk54Gm4Nl5QN8xUNXu4u296hWJtca1KLeYgEdVaI8LlpAc8gYN3D+4eo5TCstusNndJdhaKkcMvxeh+Cr4oT/vhxCdgK7CpSM0XTibR0/mJ60ukMdFWnZFOfr4UWvZKejI7ykwInk/jt1hkCT06VTtGxcSaWpB0xuW5/RNp+yccK8PY2yw/hJcwRn4G3kpf6fGjTk8mODIKUU5dTXAih4VVOX7k3Ufqh5x7PRrPBrH5wXYn8nUYw3PQnOcosjrfOPu54v8Eq/gwI46MkTksjOBb4e8Tm4BIf+MoBWMEl7r+UVfmlA/sb0xqwxmtlSPEnDX/tYGXdv+60BnC2bJz/URYZhPBajUiokis7/YLtJ6wW4DFM+tZn1qrPhnck+pZ/N9rSEsYXWg9NCJINYaqfT2QTgCjsOOyMH+ZfdaJIxTaVaCTv9RPFtqNRm5pC2QWt+kizp2f+RbaymsXGl6Tp27rft7ZUYeKqwXwLEJ37r7tViZsnyu+wnjRGDcuvu/pVAYv+gyq4x4NccmTwCk+CUcZq1P8I5M0bd3',
        '3a8c8bea': 'H7rteXDINqwIloRo704U+ACIqmj=',
        'accept': '/',
        'accept-language': 'en-US,en',
    }
    json_data = {}
    try:
        response = send_request_with_retry(url, cookies, headers, json_data)
        print(f"[Session {session_id} - buy] Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error saat mengirim aksi beli: {e}")
    time.sleep(delay_between_cookies)

def send_follow(session_id, shop_id, cookies, delay_between_cookies):
    if not shop_id:
        print("❌ Shop ID tidak boleh kosong untuk aksi follow!")
        return
    url = f"https://live.shopee.co.id/api/v1/session/{session_id}/follow/{shop_id}"
    headers = {
        'Host': 'live.shopee.co.id',
        'content-type': 'application/json',
        'client-info': 'device_model=iPhone%2014%20Pro%20Max;device_id=340F15B9537241468F99AB600714F518;client_version=33646;language=id;os=1;os_version=18.0;network=1;platform=2;cpu_model=ARM64E;longitude=109.019581;latitude=-7.711184',
        'af-ac-enc-sz-token': 'LQUT64h84cV2ihDhMJBPwg==|KEOr76J++iAwKEY5D7jdnvVa3x4+YA79WFbS1jRpTNNtc1yEbjPQmh0Xnp6p3CEf5H/R2DtEBDL08746VaCBYTrm|qZwGsqPlceTcfYQx|08|2',
        '37c48230': '563gLwlK9Z5hq5BF0icbk/63Abs=',
        'x-sap-type': '2',
        'x-livestreaming-auth': 'ls_ios_v1_20001_1730887251_30E00CFE-F722-431E-A378-CAB78FFDB3E5|BW7Gs+y22wAdYYAe3lcxbfjUGitE+RKUbYp+tqt1jsw=',
        'x-ls-sz-token': 'LQUT64h84cV2ihDhMJBPwg==|KEOr76J++iAwKEY5D7jdnvVa3x4+YA79WFbS1jRpTNNtc1yEbjPQmh0Xnp6p3CEf5H/R2DtEBDL08746VaCBYTrm|qZwGsqPlceTcfYQx|08|2',
        'client-request-id': '7de794f8-f65e-4292-a8de-ba1a6df77065.370',
        'user-agent': 'ShopeeID/3.36.46 (com.beeasy.shopee.id; build:3.36.46; iOS 18.0.0) Alamofire/5.0.5 appver=33646 language=id app_type=1 platform=native_ios os_ver=18.0.0 Cronet/102.0.5005.61',
        '46ccdf05': '6AfoKOgIThcaCDiBetIdwD7En+w=',
        'x-livestreaming-source': 'shopee',
        'x-shopee-client-timezone': 'Asia/Jakarta',
        'x-sap-ri': '533e2b677a8c51f8a3b7f32d01acddb397f268d2235b10260760',
        'c265504e': 'YL/Rs6dRa/t4YZ6A0hZSRYHosZbwyocJ2gmKyWxVVIxn057UiShwFaSVm0iBPQVbc1ZdfHAV2jDXqJvFkmBipwTGlV1/MIaRmtyPhejaa4393YLtUhkKtPQHV3p0hyElHIeKbp0eJeDNg/1d/vOgRNnpUkYgqIXH4SP5mV4At7yn1OeXVOYy2jyUTS2fbHzEFIjXcIXI8RqbEgnI8vVSZC3KRCB1yLm/h9RjuT8NJiUgSnaM1UBrctdc7cWPrnrJLeaOCE3ZisgXOaE0qz90mmnCPt7pAZ+pM5SbyzansL+35fDV1ZkIZJilk3Uwuj3g1xtpNPA1VI3c5n9O8s5nc3iwvAM9I+XbDVRJ8IuxQ4xnYv4397i0TuzlQBujgju2S32i9GFhHFQEsNuL+UE+ZRjH+1SF4y5MKNm9AGO28mHSJaQB2jE1XZ8Kh2nIm8YZCHs7202vNwWBXO1hcsDjz5zkee59J5lskO6HEQwJOYiRa1MBmdzFemr4NmcS6Xvxzx6tWHUZocjZZoLjjpS5GQUscfoXVJGQ3MQVeuxC/KGXush1xYAVzZwfUkI8H4GH6O09pjoUS3Sy4ZRfD8nlgiv7iJCAdO2o+zTdH6yWVa16XsEr2RmoYHExOSVac1PlPMeySUFy0nxg8EUN',
        'accept': '*/*',
        'accept-language': 'en-US,en',
    }
    json_data = {}
    try:
        response = send_request_with_retry(url, cookies, headers, json_data)
        print(f"[Session {session_id} - follow] Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error saat mengirim aksi follow: {e}")
    time.sleep(delay_between_cookies)


def send_like(session_id, cookies, delay_between_cookies, like_cnt):
    """
    Mengirimkan like ke sesi live Shopee.
    """
    url = f"https://live.shopee.co.id/api/v1/session/{session_id}/like"
    device_id = generate_device_id("unique_seed_value")

    headers = {
        "shopee_http_dns_mode": "1",
        "x-shopee-client-timezone": "Asia/Jakarta",
        "client-info": f"{device_id};device_model=I0vyOal;os=0;os_version=30;client_version=30009;network=1;platform=1;language=id",
        "x-livestreaming-source": "",
        "x-ls-sz-token": "sUBkHHFf+iqPeSH4PwKYbg==|x8sXdLoys1Y0GxSqQOnjf4Xf6bMTouLyxeDHLFvDXg/xfKcxh02OCXJeKCAiQGy9feopy4eySnvvmHJIwVlsxl2TleaIWCzSXA==|X3e/kV9eBXuxLNvf|08|1",
        "content-type": "application/json;charset=UTF-8",
        "accept-encoding": "gzip",
        "user-agent": "okhttp/3.12.4 app_type=1"
    }

    json_data = {
        "like_cnt": like_cnt
    }

    try:
        response = send_request_with_retry(url, cookies, headers, json_data)
        if response.status_code == 200:
            print(f"[Session {session_id} - like] Status: {response.status_code}")
        else:
            print(f"❌ Gagal mengirim like ke sesi {session_id}, kode error: {response.status_code}")
    except Exception as e:
        print(f"❌ Error saat mengirim like: {e}")
    time.sleep(delay_between_cookies)


def main():
    print("\nPilih yang ingin dijalankan (pisahkan dengan koma, contoh: 1,2 atau 1,2,3,4,5):")
    print("1: Kirim Pesan")
    print("2: Kirim Beli")
    print("3: Kirim Follow")
    print("4: Kirim Like")
    print("5: Jalankan Semua Aksi (1,2,3,4)")
    choices = input("Masukkan nomor aksi: ").strip().split(',')

    cookies_list = load_cookies_from_github(URL_GITHUB_COOKIES)
    session_id = input("Masukkan session ID: ").strip()
    delay_between_cookies = float(input("Masukkan jeda (dalam detik): ").strip())

    # Tambah opsi untuk pengulangan tak terbatas
    loop_type = input("Pilih tipe pengulangan (1: Terbatas, 2: Tak Terbatas): ").strip()
    loop_count = None
    if loop_type == "1":
        loop_count = int(input("Masukkan jumlah pengulangan: ").strip())
    
    uuid = usersig = content = shop_id = like_cnt = None
    messages = []

    if '1' in choices or '5' in choices:
        uuid = input("Masukkan UUID: ").strip()
        usersig = input("Masukkan UserSig: ").strip()
        print("Masukkan pesan (ketik 'selesai' di baris baru untuk mengakhiri):")
        while True:
            msg = input().strip()
            if msg.lower() == 'selesai':
                break
            messages.append(msg)
        if not messages:
            messages.append(input("Masukkan minimal satu pesan: ").strip())

    if '3' in choices or '5' in choices:
        shop_id = input("Masukkan Shop ID untuk follow: ").strip()

    if '4' in choices or '5' in choices:
        like_cnt = int(input("Masukkan jumlah like per aksi: ").strip())

    iteration = 0
    print("\n🚀 Memulai eksekusi...")
    try:
        while True:
            if loop_type == "1" and iteration >= loop_count:
                print(f"\n✅ Selesai melakukan {loop_count} pengulangan!")
                break

            print(f"\n📍 Pengulangan ke-{iteration + 1}")
            for cookies in cookies_list:
                if not bucket.consume():
                    print("⚠️ Rate limit tercapai. Menunggu token...")
                    time.sleep(1)
                    continue

                if '1' in choices or '5' in choices:
                    # Pilih pesan secara acak dari daftar pesan
                    content = random.choice(messages)
                    send_message(session_id, cookies, uuid, usersig, content, delay_between_cookies)
                if '2' in choices or '5' in choices:
                    send_buy(session_id, cookies, delay_between_cookies)
                if '3' in choices or '5' in choices:
                    send_follow(session_id, shop_id, cookies, delay_between_cookies)
                if '4' in choices or '5' in choices:
                    send_like(session_id, cookies, delay_between_cookies, like_cnt)

            iteration += 1
            print(f"💤 Menunggu {delay_between_cookies} detik sebelum pengulangan berikutnya...")
            time.sleep(delay_between_cookies)

    except KeyboardInterrupt:
        print("\n🔴 Program dihentikan oleh pengguna.")
    except Exception as e:
        print(f"❌ Error tidak terduga: {e}")
    finally:
        print("\n📊 Statistik:")
        print(f"Total pengulangan: {iteration}")
        print(f"Total cookies digunakan: {len(cookies_list) * iteration}")
        if '1' in choices or '5' in choices:
            print(f"Total pesan dikirim: {len(cookies_list) * iteration}")

if __name__ == "__main__":
    main()
