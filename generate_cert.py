#!/usr/bin/env python3
"""
Generate a self-signed SSL certificate so server.py can run over HTTPS.
HTTPS is required for the service worker (and offline caching) to work on iOS.

Usage:
    python generate_cert.py

Then restart server.py — it will automatically pick up cert.pem / key.pem.

iOS trust steps (one-time, per device):
  1. Open https://<your-PC-IP>:8765/cert.pem in Safari on your iPhone
  2. Tap "Allow" → download the profile
  3. Go to Settings → General → VPN & Device Management → tap the profile → Install
  4. Go to Settings → General → About → Certificate Trust Settings → enable the cert
  5. Open https://<your-PC-IP>:8765/News.html and add to Home Screen
"""
import socket, os, ipaddress, datetime

def get_local_ips():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = '127.0.0.1'
    return list({lan_ip, '127.0.0.1'})

def generate():
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        ips = get_local_ips()
        san = [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]
        san.append(x509.DNSName('localhost'))

        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'News Headlines Local')])
        now = datetime.datetime.utcnow()
        cert = (
            x509.CertificateBuilder()
            .subject_name(name).issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(san), critical=False)
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .sign(key, hashes.SHA256())
        )

        with open('key.pem', 'wb') as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))
        with open('cert.pem', 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        return True, ips

    except ImportError:
        print('cryptography package not found.')
        print('Install it with:  pip install cryptography')
        return False, []

os.chdir(os.path.dirname(os.path.abspath(__file__)))
ok, ips = generate()
if ok:
    lan = next((ip for ip in ips if ip != '127.0.0.1'), '127.0.0.1')
    print(f'cert.pem and key.pem created (valid 10 years)')
    print()
    print('iOS setup (one-time per device):')
    print(f'  1. Start server.py, then open https://{lan}:8765/cert.pem in Safari on your iPhone')
    print('  2. Tap Allow → Settings → General → VPN & Device Management → install the profile')
    print('  3. Settings → General → About → Certificate Trust Settings → enable the cert')
    print(f'  4. Open https://{lan}:8765/News.html → Share → Add to Home Screen')
