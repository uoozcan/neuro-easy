"""Run SWANe 0.2.1.1's real DICOM-to-T1-reference subworkflow and write local QC."""
import argparse
import datetime as dt
from importlib.metadata import version
import json
import os
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import neuro_easy as launcher


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dicom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    dicom = args.dicom.expanduser().resolve()
    if not dicom.is_dir():
        parser.error('DICOM series directory does not exist.')
    if version('swane') != '0.2.1.1':
        parser.error('This validation harness is specific to SWANe 0.2.1.1.')
    output.mkdir(parents=True, exist_ok=True)
    launcher.require_space(output, 5)
    launcher.runtime_environment(launcher.load(required=False))
    os.environ['ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS'] = '2'
    os.environ['OMP_NUM_THREADS'] = '2'
    os.environ['NIPYPE_NO_ET'] = '1'
    report = {'status': 'RUNNING', 'utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'scope': 'SWANe T1 reference subworkflow only; no registration, cortical reconstruction or Slicer export',
              'swane': version('swane'), 'python': sys.version.split()[0],
              'settings': {'bet_thr': 0.3, 'bet_robust': True, 'bet_bias_correction': False,
                           'synth_strip': False, 'threads': 2}}
    launcher.save(output / 'validation.json', report)
    start = time.monotonic()
    try:
        import numpy as np
        import nibabel as nib
        import SimpleITK as sitk
        sitk.ProcessObject.SetGlobalDefaultNumberOfThreads(2)
        from swane.config.ConfigManager import ConfigManager
        from swane.config.config_enums import GlobalPrefCategoryList
        from swane.utils.DataInputList import DataInputList
        from swane.nipype_pipeline.workflows.ref_workflow import ref_workflow
        from nipype import Node
        from nipype.interfaces.io import DataSink
        config = ConfigManager(global_base_folder=str(output))
        config[DataInputList.T13D]['bet_thr'] = '0.3'
        config[DataInputList.T13D]['bet_bias_correction'] = 'false'
        config[GlobalPrefCategoryList.SYNTH]['strip'] = 'false'
        workflow = ref_workflow('t1_reference', str(dicom), config[DataInputList.T13D],
                                config[GlobalPrefCategoryList.SYNTH], str(output / 'work'))
        fields = ('reference', 'reference_brain', 'ref_mask',
                  'uncorrected_reference', 'uncorrected_reference_brain')
        sink = Node(DataSink(base_directory=str(output / 'outputs')), name='export')
        for field in fields:
            workflow.connect(workflow.get_node('outputnode'), field, sink, field)
        workflow.config['execution']['crashdump_dir'] = str(output)
        workflow.config['execution']['stop_on_first_crash'] = True
        workflow.run(plugin='Linear')
        images, arrays, files = {}, {}, {}
        for field in fields:
            matches = list((output / 'outputs' / field).rglob('*.nii.gz'))
            if len(matches) != 1 or matches[0].stat().st_size == 0:
                raise RuntimeError('Expected one nonempty output for ' + field)
            files[field] = str(matches[0])
            images[field] = nib.load(matches[0])
            arrays[field] = images[field].get_fdata()
            if not np.isfinite(arrays[field]).all():
                raise RuntimeError('Nonfinite image data: ' + field)
        reference = images['reference']
        for field in fields:
            if images[field].shape != reference.shape or not np.allclose(images[field].affine, reference.affine):
                raise RuntimeError('Output geometry differs: ' + field)
        mask = arrays['ref_mask']
        if not set(np.unique(mask)).issubset({0.0, 1.0}) or mask.sum() == 0:
            raise RuntimeError('Mask is empty or not binary.')
        if not np.allclose(arrays['reference_brain'], arrays['reference'] * mask, rtol=1e-5, atol=1e-4):
            raise RuntimeError('Brain image does not match masked reference.')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(3, 5, figsize=(15, 9))
        for axis in range(3):
            for col, fraction in enumerate((0.3, 0.4, 0.5, 0.6, 0.7)):
                index = int(reference.shape[axis] * fraction)
                values = np.rot90(np.take(arrays['reference'], index, axis=axis))
                outline = np.rot90(np.take(mask, index, axis=axis))
                axes[axis, col].imshow(values, cmap='gray', vmin=0,
                                      vmax=np.percentile(arrays['reference'][mask > 0], 99))
                axes[axis, col].contour(outline, levels=[0.5], colors=['red'], linewidths=0.5)
                axes[axis, col].set_title(f'axis {axis}, slice {index}')
                axes[axis, col].axis('off')
        fig.suptitle('Public T1 reference and BET mask — visual QC required')
        fig.tight_layout()
        fig.savefig(output / 'mask-qc.png', dpi=120)
        plt.close(fig)
        report.update({'status': 'PASSED_AUTOMATED_CHECKS', 'outputs': files,
                       'shape': list(reference.shape), 'zooms_mm': list(map(float, reference.header.get_zooms())),
                       'orientation': list(nib.aff2axcodes(reference.affine)),
                       'affine': reference.affine.tolist(),
                       'brain_volume_ml': float(mask.sum() * np.prod(reference.header.get_zooms()) / 1000),
                       'visual_qc': 'PENDING: inspect mask-qc.png; automated checks do not assess scientific accuracy'})
    except BaseException as error:
        report.update({'status': 'INTERRUPTED' if isinstance(error, KeyboardInterrupt) else 'FAILED',
                       'error': str(error)})
        raise
    finally:
        report.update({'elapsed_seconds': round(time.monotonic() - start, 2),
                       'peak_self_rss_mib': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                       'peak_child_rss_mib': round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1)})
        launcher.save(output / 'validation.json', report)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
