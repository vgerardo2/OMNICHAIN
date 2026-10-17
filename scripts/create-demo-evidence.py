"""Create a real scripted assessment export, without network/model credentials.

Usage: python scripts/create-demo-evidence.py --output examples/scripted-validation.json
Existing output is never overwritten; runtime files live only in a temporary directory.
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from omnichain.service import Service
from omnichain.evidence import verify_export


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Choose a new output path; existing evidence is not overwritten.')
    with tempfile.TemporaryDirectory(prefix='omnichain-example-') as directory:
        service=Service(directory)
        service.attack('DETERMINISTIC_FIXTURE')
        result=service.compare()['candidates']['PUB-SCOPED-TOOLS']
        service.select('PUB-SCOPED-TOOLS',result['config_hash'],
                       'Scripted example: required checks passed for both attacks and ordinary tasks.',
                       'small',[40,30,20,10])
        result=service.validate()
        bundle=service.export(result['run'])
        check=verify_export(bundle)
        if result['verdict']!='PASS' or not check['integrity'] or not check['complete']:
            raise SystemExit('Example did not pass verification; no output written.')
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with args.output.open('x',encoding='utf-8') as output:
            json.dump(bundle,output,indent=2,ensure_ascii=False)
            output.write('\n')
        print(json.dumps({'mode':'DETERMINISTIC_FIXTURE','verdict':result['verdict'],
                          'verification':check,'linked_runs':len(bundle['linked_runs'])}))


if __name__=='__main__':
    main()
