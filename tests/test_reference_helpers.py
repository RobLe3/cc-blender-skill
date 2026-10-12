"""Synthetic source fixtures exercise unchanged reference tooling, not visual taste."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = np = None

ROOT=Path(__file__).resolve().parents[1]
BASELINE=Path(os.environ['CC_BLENDER_BASELINE']) if os.environ.get('CC_BLENDER_BASELINE') else None


@unittest.skipUnless(cv2 is not None, 'Install image-processing requirements')
class ReferenceHelpers(unittest.TestCase):
    def test_wireframe_and_reference_pipeline(self):
        with tempfile.TemporaryDirectory() as directory:
            out=Path(directory)
            wire=np.full((128,128,3),255,dtype=np.uint8)
            cv2.rectangle(wire,(24,24),(104,104),(0,0,0),3)
            cv2.imwrite(str(out/'wire.png'),wire)
            mask=np.zeros((128,128,4),dtype=np.uint8)
            mask[24:104,24:104]=[255,255,255,255]
            for name in ['front','side','render']:
                cv2.imwrite(str(out/(name+'.png')),mask)
            shifted=np.roll(mask,40,axis=1);cv2.imwrite(str(out/'shifted.png'),shifted)
            roots=[('candidate',ROOT)] + ([('baseline',BASELINE)] if BASELINE else [])
            outputs={}
            for label,root in roots:
                target=out/label;target.mkdir()
                analyzer=runpy.run_path(str(root/'plugin/skills/wireframe-to-3d/scripts/wireframe_analyzer.py'))
                analysis=analyzer['WireframeAnalyzer'](str(out/'wire.png')).process()
                self.assertGreater(analysis['metadata']['num_contours'],0)
                def run(path,*args):
                    subprocess.run([sys.executable,str(root/'plugin/skills'/path),*map(str,args)],check=True,capture_output=True)
                run('reference-analysis-validator/scripts/reference_manifest_compiler.py',out/'front.png','--mode','alpha','--out',target/'manifest.json')
                run('orthographic-registration/scripts/register_views.py',out/'front.png',out/'side.png','--out',target/'registration.json')
                run('contour-to-mesh/scripts/mask_to_mesh_recipe.py','--image',out/'front.png','--mode','alpha','--name','GEO-reference','--out',target/'mesh.json','--blender-script',target/'mesh.py')
                reports=[]
                for image in ['render','shifted']:
                    run('reference-analysis-validator/scripts/render_overlay_validator.py','--reference',out/'front.png','--render',out/(image+'.png'),'--mode','alpha','--out',target/(image+'.json'))
                    reports.append(json.loads((target/(image+'.json')).read_text()))
                manifest=json.loads((target/'manifest.json').read_text())
                threshold=manifest['validation_thresholds']['front_mask_iou_min']
                self.assertEqual(manifest['source_files'][0]['component_count'],1)
                self.assertGreaterEqual(reports[0]['iou'],threshold)
                self.assertLess(reports[1]['iou'],threshold,'Mismatched source must fail the acceptance threshold')
                mesh=json.loads((target/'mesh.json').read_text());self.assertTrue(mesh['vertices'] and mesh['faces'])
                registration=json.loads((target/'registration.json').read_text())
                self.assertEqual(registration['coordinate_contract']['front'],'X/Z')
                outputs[label]={'wire':analysis,'manifest':manifest,'registration':registration,'mesh':mesh,'reports':reports}
            if BASELINE:
                normalized = {key: json.loads(json.dumps(value, default=lambda x: x.tolist()))
                              for key, value in outputs.items()}
                self.assertEqual(normalized['candidate'], normalized['baseline'])


if __name__=='__main__':unittest.main()
