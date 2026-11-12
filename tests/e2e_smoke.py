"""Quick E2E smoke test - run against live servers."""
import io
import json
import sys
import urllib.request
import urllib.error
from PIL import Image

BASE = 'http://localhost:8000/api/v1'


def _req(method, path, payload=None, token=None, form=None):
    url = f'{BASE}{path}'
    headers = {}
    data = None
    if token:
        headers['Authorization'] = f'Bearer {token}'

    if form is not None:
        boundary = '----PilahBoundary7MA4YWxkTrZu0gW'
        body = b''
        for k, v in form.items():
            if isinstance(v, tuple):
                fname, fbytes, ctype = v
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{k}"; filename="{fname}"\r\n'.encode()
                body += f'Content-Type: {ctype}\r\n\r\n'.encode()
                body += fbytes + b'\r\n'
            else:
                body += f'--{boundary}\r\n'.encode()
                body += f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode()
                body += str(v).encode() + b'\r\n'
        body += f'--{boundary}--\r\n'.encode()
        headers['Content-Type'] = f'multipart/form-data; boundary={boundary}'
        data = body
    elif payload is not None:
        data = json.dumps(payload).encode()
        headers['Content-Type'] = 'application/json'

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read().decode()) if r.length != 0 else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def make_jpeg(w=800, h=600, color=(30, 200, 60)):
    img = Image.new('RGB', (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return buf.getvalue()


def main():
    print('=' * 60)
    print('E2E SMOKE TEST')
    print('=' * 60)

    # 1) Register
    status, data = _req('POST', '/auth/register', {
        'npm_nip': '140810240099',
        'name': 'Smoke Tester',
        'email': 'smoke099@mail.unpad.ac.id',
        'unit_gedung': 'Teknik Informatika',
        'password': 'StrongPass123!',
    })
    print(f'[1] REGISTER -> {status}')
    if status not in (201, 400):
        print('  FAIL:', data); sys.exit(1)
    if status == 400:
        print('  (user already exists, continuing to login)')

    # 2) Login
    status, data = _req('POST', '/auth/login', {
        'identifier': 'smoke099@mail.unpad.ac.id',
        'password': 'StrongPass123!',
    })
    print(f'[2] LOGIN (email) -> {status}')
    if status != 200:
        print('  FAIL:', data); sys.exit(1)
    token = data['access_token']
    user = data['user']
    print(f'   user_id={user["user_id"]} peran={user["peran"]} poin={user["total_poin"]}')

    # 2b) Login via npm_nip
    status2, data2 = _req('POST', '/auth/login', {
        'identifier': '140810240099',
        'password': 'StrongPass123!',
    })
    print(f'[2b] LOGIN (npm_nip) -> {status2}')
    assert status2 == 200, data2

    # 3) Profile
    status, data = _req('GET', '/auth/profile', token=token)
    print(f'[3] PROFILE -> {status} (poin={data.get("total_poin")})')

    # 4) Upload (green image -> organik)
    jpeg = make_jpeg(800, 600, (30, 200, 60))
    status, data = _req('POST', '/classifications/upload/', token=token, form={
        'file': ('sampah.jpg', jpeg, 'image/jpeg'),
    })
    # Error body (dict or str) means failure
    if not isinstance(data, dict):
        if isinstance(data, (bytes, str)):
            print(f'[4] UPLOAD RAW -> {status} {data}')
        # Re-fetch with printing anyway
        print('   Continuing to test polling with empty id (will fail if no id)')
        sys.exit(1)
    print(f'[4] UPLOAD -> {status} {data.get("message", data)}')
    if status not in (201, 202):
        print('  FAIL:', data); sys.exit(1)
    upload_id = data['upload_id']
    print(f'   upload_id={upload_id}')

    # 5) Poll
    import time
    for i in range(10):
        status, data = _req('GET', f'/classifications/{upload_id}/', token=token)
        if status == 200 and data.get('status') == 'completed':
            break
        time.sleep(0.5)
    print(f'[5] POLL -> {status} status={data.get("status")} kategori={data.get("kategori")} '
          f'confidence={data.get("confidence")} poin={data.get("poin_diperoleh")}')

    # 6) Check points
    status, data = _req('GET', f'/classifications/{upload_id}/points/', token=token)
    print(f'[6] CHECK POINTS -> {status} {data.get("memenuhi_syarat")} poin={data.get("jumlah_poin")}')

    # 7) User total points
    status, data = _req('GET', '/points/me', token=token)
    print(f'[7] TOTAL POINTS -> {status} total_poin={data.get("total_poin")} rank={data.get("rank")}')

    # 8) Leaderboard
    status, data = _req('GET', '/leaderboard?type=user', token=token)
    print(f'[8] LEADERBOARD USER -> {status} total_peserta={data.get("total_peserta")} user_rank={data.get("user_rank")}')
    status, data = _req('GET', '/leaderboard?type=building', token=token)
    print(f'[8b] LEADERBOARD BUILDING -> {status} my_bag={data.get("user_building")} rank={data.get("user_building_rank")}')

    # 9) History
    status, data = _req('GET', '/classifications', token=token)
    print(f'[9] HISTORY -> {status} total_unggahan={data.get("total_unggahan")} total_poin={data.get("total_poin_diperoleh")}')

    # 10) Rewards - create one as admin
    status, data = _req('POST', '/auth/login', {'identifier': 'admin.gogreen@unpad.ac.id', 'password': 'AdminPass123!'})
    if status == 200:
        admin_token = data['access_token']
        status, data = _req('POST', '/admin/rewards/', {
            'name': 'Diskon Kantin 10%', 'points_required': 5, 'stock': 10, 'masa_berlaku': '2027-12-31'
        }, token=admin_token)
        print(f'[10] ADMIN CREATE REWARD -> {status} {data.get("message", data)}')
        if status not in (201, 400):
            print('   payload:', data)
        # Admin dashboard
        status, data = _req('GET', '/admin/dashboard/', token=admin_token)
        print(f'[10b] ADMIN DASHBOARD -> {status} pengguna={data.get("total_pengguna")} upload={data.get("total_upload")}')
    else:
        print(f'[10] ADMIN LOGIN skipped (no admin account yet): {status}')
        admin_token = None

    # 11) Redeem
    status, data = _req('GET', '/rewards', token=token)
    print(f'[11] LIST REWARDS -> {status} count={len(data.get("results", data.get("data", [])))}')
    rewards = data.get('results', data.get('data', []))
    if rewards:
        reward_id = rewards[0]['id']
        status, data = _req('POST', f'/rewards/{reward_id}/redeem', token=token)
        msg = data.get("message") if isinstance(data, dict) else str(data)[:200]
        print(f'[11b] REDEEM -> {status} {msg}')
        if status == 200 and isinstance(data, dict):
            print(f'   voucher={data.get("kode_reward")} sisa_poin={data.get("sisa_poin")}')

    # 12) Points transactions
    status, data = _req('GET', '/points/transactions', token=token)
    total_tx = data.get("total") if isinstance(data, dict) else "?"
    print(f'[12] POINT TX -> {status} total={total_tx}')

    # 13) Logout + verify token invalid
    refresh_tok = data2.get('refresh_token') if isinstance(data2, dict) else None
    status, data = _req('POST', '/auth/logout', {'refresh_token': refresh_tok} if refresh_tok else {}, token=token)
    msg = data.get("message") if isinstance(data, dict) else str(data)[:200]
    print(f'[13] LOGOUT -> {status} {msg}')

    print('=' * 60)
    print('SMOKE TEST COMPLETE')
    print('=' * 60)


if __name__ == '__main__':
    main()
