"""Áp bản dịch tiếng Việt cho chuỗi tiếng Trung viết cứng trong bundle web (bỏ qua các mục locale "a.b":"…")."""
import json, glob, gzip, os, re, sys
d = sys.argv[1]
M = json.load(open(os.path.join(os.path.dirname(__file__), 'vi_map.json'), encoding='utf-8'))
total = 0
for f in glob.glob(os.path.join(d, 'js', '*.js')):
    s = open(f, encoding='utf-8').read(); n = 0
    for cn, vi in M.items():
        for q in ('"', '`'):
            pat = re.compile(r'(?<!"[\w.\-]{1,80}":)' if False else re.escape(q + cn + q))
            def rep(m):
                pre = s[max(0, m.start() - 90):m.start()]
                if re.search(r'"[a-zA-Z][\w]*\.[\w.\-]+":$', pre):  # locale entry -> keep
                    return m.group(0)
                return q + vi.replace('"', '\\"') + q
            s2, k = pat.subn(rep, s)
            n += sum(1 for _ in [0]) * 0 + (k if s2 != s else 0)
            s = s2
    if n:
        open(f, 'w', encoding='utf-8').write(s)
        gz = f + '.gz'
        if os.path.exists(gz):
            open(gz, 'wb').write(gzip.compress(s.encode('utf-8'), 9))
        total += n
print('replaced', total)
