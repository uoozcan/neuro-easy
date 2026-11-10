"""Fetch one explicitly licensed public real T1 DICOM QA series; keep it local."""
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1] / 'local/public-t1'
COMMIT = 'ffc4fd6edc37cac769d69740185bdb1306b5a3fb'
BASE = 'https://raw.githubusercontent.com/neurolabusc/dcm_qa_mprage/' + COMMIT + '/'
SHA256 = '558335329ca94dd5d2e85d1c3d4c9ef2682f2acf8a92bba81a60e50999f7402e'


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / 'T1-series.zip'
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        urllib.request.urlretrieve(BASE + 'In/6_T1_mprage_ns_sag_p2.zip', archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest() != SHA256:
        raise RuntimeError('Public dataset checksum mismatch.')
    for name in ('LICENSE', 'README.md'):
        with urllib.request.urlopen(BASE + name, timeout=60) as response:
            (ROOT / name).write_bytes(response.read())
    destination = ROOT / 'dicom'
    with zipfile.ZipFile(archive) as data:
        for entry in data.infolist():
            if not (destination / entry.filename).resolve().is_relative_to(destination.resolve()):
                raise RuntimeError('Unsafe archive member.')
        data.extractall(destination)
    provenance = {'repository': 'https://github.com/neurolabusc/dcm_qa_mprage',
                  'commit': COMMIT, 'series': '6_T1_mprage_ns_sag_p2',
                  'licence': 'BSD-2-Clause', 'archive_sha256': SHA256,
                  'modality': 'real 1 mm T1w MPRAGE, Siemens Prisma 3T VE11',
                  'scope': 'SWANe T1 reference subworkflow only'}
    (ROOT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
    print(destination / '6_T1_mprage_ns_sag_p2')


if __name__ == '__main__':
    main()
