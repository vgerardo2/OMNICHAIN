"""Reproducible approval context, excluding keys, host paths and secrets."""
import hashlib
import sys
from pathlib import Path
from .contracts import VERSION, ORACLE_VERSION, POLICY, CASES, VALIDATION_CASES, CONTROLS, digest


def execution_context(mode, model_status):
    """Any code, contract, runtime or configured model change requires new runs."""
    folder = Path(__file__).parent
    modules = ('contracts.py','engine.py','evidence.py','models.py','service.py','context.py','graph.py')
    return {'scenario':VERSION,'oracle':ORACLE_VERSION,'serializer':'canonical-json-v1',
            'policy':digest(POLICY),'cases':digest(CASES),'validation_cases':digest(VALIDATION_CASES),
            'controls':digest(CONTROLS),'python':list(sys.version_info[:3]),'mode':mode,
            'model':model_status['model'] if mode == 'LIVE_HOSTED_MODEL' else 'deterministic-fixture-v2',
            'proposal_protocol':'single-call-actions-and-summary-v2','temperature':0,'max_output_tokens':1024,
            'code':{n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in modules}}
