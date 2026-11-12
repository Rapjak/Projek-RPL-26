"""Manual check: verify upload response shape (API-005) and poll shape (API-006)."""
import io
import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000/api/v1'


def req(method, path, payload=None, token=None, files=None):
    headers = {}
    data = None
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if files is not None:
        boundary = '----PilahBoundary7MA4YWxkTrZu0gW'
        body = io.BytesIO()
        for name, (filename, content, content_type) in files.items():
            body.write(f'--{boundary}\r\n'.encode())
            body.write(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode())
            body.write(f'Content-Type: {content_type}\r\n\r\n'.encode())
            body.write(content)
            body.write(b'\r\n')
        body.write(f'--{boundary}--\r\n'.encode())
        data = body.getvalue()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
    elif payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'
    r = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


# Build a valid small PNG (1x1) using Pillow if available
try:
    from PIL import Image
    buf = io.BytesIO()
    Image.new('RGB', (60, 60), (30, 200, 60)).save(buf, format='PNG')
    png_bytes = buf.getvalue()
    print(f'PNG bytes: {len(png_bytes)}')
except Exception as ex:
    print('Pillow missing:', ex)
    raise

s, d = req('POST', '/auth/login', {'identifier': 'smoke099@mail.unpad.ac.id', 'password': 'StrongPass123!'})
print('login:', s)
tok = d['access_token']

print('\n--- UPLOAD (API-005) ---')
s, d = req('POST', '/classifications/upload/', token=tok,
           files={'file': ('test.png', png_bytes, 'image/png')})
print('status:', s)
print('response:', json.dumps(d, indent=2) if isinstance(d, dict) else d)

if isinstance(d, dict) and 'upload_id' in d:
    uid = d['upload_id']
    print('\n--- POLL (API-006) ---')
    import time
    for i in range(10):
        time.sleep(0.5)
        s2, d2 = req('GET', f'/classifications/{uid}/', token=tok)
        print(f'  poll {i}: {s2} status={d2.get("status") if isinstance(d2, dict) else d2}')
        if isinstance(d2, dict) and d2.get('status') in ('completed', 'failed'):
            print('  full:', json.dumps(d2, indent=2))
            break
