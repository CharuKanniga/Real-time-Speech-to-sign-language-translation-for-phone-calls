import os, re

def process_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Replace specific full lines for theme settings
    content = content.replace(
        '[data-theme="dark"]{--bg:#060d1a;--s:#0d1929;--c:#0f1e31;--c2:#111f33;--b:#1a2d44;--b2:#1e3048;--a:#00c896;--a2:#3b82f6;--t:#e2eaf4;--m:#5a7a9a;--m2:#7a9ab8;--err:#f87171;--sw:230px}',
        '[data-theme="dark"]{--bg:#1e1e24;--s:#2b2b36;--c:#2b2b36;--c2:#32323e;--b:rgba(255,255,255,0.1);--b2:rgba(255,255,255,0.15);--a:#4a90e2;--a2:#357abd;--t:#e0e0e0;--m:#a0a0a0;--m2:#b0b0b0;--err:#f87171;--sw:230px}'
    )
    content = content.replace(
        '[data-theme="light"]{--bg:#f0f4f8;--s:#ffffff;--c:#ffffff;--c2:#f8fafc;--b:#d1dce8;--b2:#c5d4e2;--a:#00a97a;--a2:#2563eb;--t:#1e293b;--m:#64748b;--m2:#475569;--err:#dc2626;--sw:230px}',
        '[data-theme="light"]{--bg:#f5f5f5;--s:#ffffff;--c:#ffffff;--c2:#eff1f3;--b:#e0e0e0;--b2:#cccccc;--a:#005A9C;--a2:#004B87;--t:#333333;--m:#777777;--m2:#555555;--err:#dc2626;--sw:230px}'
    )

    content = content.replace(
        '[data-theme="dark"]{--bg:#0a0f1e;--surface:#111827;--card:#1a2235;--accent:#00d4aa;--accent2:#4f8ef7;--text:#e8edf5;--muted:#6b7a99;--error:#ff6b6b;--border:rgba(255,255,255,0.08);--warn:#fbbf24}',
        '[data-theme="dark"]{--bg:#1e1e24;--surface:#2b2b36;--card:#2b2b36;--accent:#4a90e2;--accent2:#357abd;--text:#e0e0e0;--muted:#a0a0a0;--error:#f87171;--border:rgba(255,255,255,0.1);--warn:#fbbf24}'
    )
    content = content.replace(
        '[data-theme="light"]{--bg:#f0f4f8;--surface:#ffffff;--card:#ffffff;--accent:#00a97a;--accent2:#2563eb;--text:#1e293b;--muted:#64748b;--error:#dc2626;--border:rgba(0,0,0,0.1);--warn:#d97706}',
        '[data-theme="light"]{--bg:#f5f5f5;--surface:#ffffff;--card:#ffffff;--accent:#005A9C;--accent2:#004B87;--text:#333333;--muted:#777777;--error:#dc2626;--border:rgba(0,0,0,0.1);--warn:#d97706}'
    )
    
    # Generic replacements for standard dark mode themes (login, signup, etc.)
    content = re.sub(r'--bg:\s*#060d1a;', '--bg:#1e1e24;', content)
    content = re.sub(r'--bg:\s*#0a0f1e;', '--bg:#1e1e24;', content)
    content = re.sub(r'--surface:\s*#0d1929;', '--surface:#2b2b36;', content)
    content = re.sub(r'--surface:\s*#111827;', '--surface:#2b2b36;', content)
    content = re.sub(r'--card:\s*#111f33;', '--card:#2b2b36;', content)
    content = re.sub(r'--card:\s*#0f1e31;', '--card:#2b2b36;', content)
    content = re.sub(r'--card:\s*#1a2235;', '--card:#2b2b36;', content)
    content = re.sub(r'--card2:\s*#111f33;', '--card2:#32323e;', content)
    content = re.sub(r'--border:\s*#1e3048;', '--border:rgba(255,255,255,0.1);', content)
    content = re.sub(r'--accent:\s*#00c896;', '--accent:#4a90e2;', content)
    content = re.sub(r'--accent:\s*#00d4aa;', '--accent:#4a90e2;', content)
    content = re.sub(r'--accent2:\s*#3b82f6;', '--accent2:#357abd;', content)
    content = re.sub(r'--accent2:\s*#4f8ef7;', '--accent2:#357abd;', content)
    content = re.sub(r'--text:\s*#e2eaf4;', '--text:#e0e0e0;', content)
    content = re.sub(r'--muted:\s*#5a7a9a;', '--muted:#a0a0a0;', content)

    if original != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")

for root, _, files in os.walk('templates'):
    for file in files:
        if file.endswith('.html'):
            process_file(os.path.join(root, file))

