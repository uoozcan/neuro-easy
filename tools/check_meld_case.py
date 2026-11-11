"""Run inside the pinned MELD container; structural checks, not clinical QC."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, '/app')


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def image(path):
    import nibabel as nib
    import numpy as np
    value = nib.load(path)
    data = np.asarray(value.dataobj)
    if data.ndim == 4 and data.shape[-1] == 1:
        data = data[..., 0]
    if data.ndim != 3 or min(data.shape) < 2:
        raise ValueError('Expected a three-dimensional MRI: ' + str(path))
    if not np.isfinite(data).all() or not np.isfinite(value.affine).all():
        raise ValueError('Non-finite MRI values or geometry: ' + str(path))
    if abs(np.linalg.det(value.affine[:3, :3])) < 1e-10:
        raise ValueError('Singular MRI geometry: ' + str(path))
    return value, data


def check(stage, subject, image_digest):
    import numpy as np
    root = Path('/data')
    state = root / '.neuro-easy'
    state.mkdir(mode=0o700, exist_ok=True)
    record_path = state / (subject + '.json')
    if stage == 'pre':
        # Upstream uses shell commands without filename quoting.
        for candidate in (root / 'input' / subject).rglob('*.nii*'):
            if not re.fullmatch(r'[/A-Za-z0-9_.-]+', str(candidate)):
                raise ValueError('Use simple MRI filenames without spaces or shell characters.')
        from meld_graph.tools_pipeline import get_anat_files
        anatomy = get_anat_files(subject)
        if not anatomy or not anatomy.get('T1_path'):
            raise ValueError('Exactly one T1 MRI is required in the upstream MELD/BIDS layout.')
        inputs = {}
        for modality in ('T1', 'FLAIR'):
            if anatomy.get(modality + '_path') is None:
                continue
            path = Path(anatomy[modality + '_path']).resolve()
            path.relative_to((root / 'input').resolve())
            if not re.fullmatch(r'[/A-Za-z0-9_.-]+', str(path)):
                raise ValueError('Use simple MRI filenames without spaces or shell characters.')
            _, data = image(path)
            if float(np.max(data)) == float(np.min(data)):
                raise ValueError('Empty/constant ' + modality + ' MRI; the bundled example input is a placeholder.')
            inputs[modality] = {'path': str(path.relative_to(root)), 'sha256': digest(path)}
        previous = json.loads(record_path.read_text()) if record_path.exists() else None
        if previous and (previous['inputs'] != inputs or previous['image'] != image_digest):
            raise ValueError('Input/image differs from this subject provenance; use a new subject/data directory.')
        if not previous and (root / 'output/fs_outputs' / subject).exists():
            raise ValueError('Existing reconstruction has no launcher input provenance; use a fresh data directory.')
        record = {'inputs': inputs, 'image': image_digest, 'started_ns': time.time_ns(),
                  'status': 'RUNNING', 'scope': 'raw-MRI pipeline; structural checks only'}
    else:
        if not record_path.exists():
            raise ValueError('Missing preflight provenance.')
        record = json.loads(record_path.read_text())
        if record['image'] != image_digest or record['status'] != 'RUNNING':
            raise ValueError('No matching active preflight.')
        for item in record['inputs'].values():
            if digest(root / item['path']) != item['sha256']:
                raise ValueError('MRI changed during analysis.')
        prediction = root / 'output/predictions_reports' / subject / 'predictions/prediction.nii.gz'
        report = root / 'output/predictions_reports' / subject / 'reports' / ('MELD_report_' + subject + '.pdf')
        for output in (prediction, report):
            if not output.is_file() or output.stat().st_mtime_ns < record['started_ns']:
                raise ValueError('Missing or stale analysis output: ' + str(output))
        p, labels = image(prediction)
        native, _ = image(root / 'output/fs_outputs' / subject / 'mri/orig/001.mgz')
        if p.shape != native.shape or not np.allclose(p.affine, native.affine, atol=1e-4):
            raise ValueError('Prediction does not match FreeSurfer native geometry.')
        if not np.all(labels >= 0) or not np.allclose(labels, np.rint(labels)):
            raise ValueError('Invalid prediction labels.')
        pdf = report.read_bytes()
        if not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-1024:]:
            raise ValueError('Incomplete PDF report.')
        record.update(status='STRUCTURAL_OUTPUT_CHECKS_PASSED', finished_ns=time.time_ns(),
                      prediction_sha256=digest(prediction), report_sha256=digest(report),
                      visual_qc='REQUIRED_SEPARATELY')
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    record_path.chmod(0o600)
    print(record['status'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('pre', 'post'))
    parser.add_argument('subject')
    parser.add_argument('image_digest')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', args.subject):
        parser.error('Invalid subject identifier.')
    try:
        check(args.stage, args.subject, args.image_digest)
    except (ValueError, OSError, KeyError) as error:
        print('MELD validation failed: ' + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
