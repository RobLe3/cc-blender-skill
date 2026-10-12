"""Compare candidate runs to a baseline and its repeatability control."""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def compare(root):
    baseline=json.loads((root/'legacy-baseline/core-tests.json').read_text())
    control=json.loads((root/'legacy-baseline-repeat/core-tests.json').read_text())
    expected={t['id']:t for t in baseline['tests']}
    result={'baseline_failures':[t for t in baseline['tests'] if t['status']=='FAIL'],
            'candidates':{},'runtime_regression_passed':True,
            'merge_ready':False,'blocking_gates':['Actual Codex and Claude Code skill-trigger and backend-routing evaluations are incomplete.']}
    for label in ['legacy-candidate','official-candidate']:
        current=json.loads((root/label/'core-tests.json').read_text())
        actual={t['id']:t for t in current['tests']}
        failures=[key for key,value in actual.items() if value['status']=='FAIL' and expected.get(key,{}).get('status')!='FAIL']
        images={}
        for name in baseline['fixtures']:
            read=lambda branch:np.asarray(Image.open(root/branch/(name+'.png')).convert('RGB'),dtype=np.float64)
            a,b,c=read('legacy-baseline'),read(label),read('legacy-baseline-repeat')
            candidate_rmse=float(np.sqrt(np.mean((a-b)**2)))
            control_rmse=float(np.sqrt(np.mean((a-c)**2)))
            images[name]={'rmse_vs_baseline':candidate_rmse,
                          'baseline_repeat_rmse':control_rmse,
                          'within_repeatability_envelope':bool(candidate_rmse <= control_rmse + 1e-12)}
        passed=(actual.keys()==expected.keys() and not failures
                and current['fixtures']==baseline['fixtures']==control['fixtures']
                and all(v['within_repeatability_envelope'] for v in images.values()))
        result['candidates'][label]={'tests':len(actual),'new_failures':failures,
                                    'fixture_stats_match':current['fixtures']==baseline['fixtures'],
                                    'images':images,'passed':passed}
        result['runtime_regression_passed'] &= passed
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=compare(args.runs)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if result['runtime_regression_passed'] else 1)
