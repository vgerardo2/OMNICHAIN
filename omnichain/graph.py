"""Reconstruct explicit invocation/data links, never timing-based causation.

Unrelated records remain visible. Missing or inconsistent references are unresolved.
These relations establish recorded calls/data use, not a model's hidden reasoning.
"""


def reconstruct(events):
    indexed = {e['id']:e for e in events}
    edges, nodes = [], []
    for event in events:
        payload = event['payload']
        nodes.append({'id':event['id'],'type':event['type'],'trial':payload.get('trial'),
                      'status':payload.get('status','recorded')})
        parent = indexed.get(event.get('parent'))
        if event.get('parent'):
            same_trial = parent and parent['payload'].get('trial') == payload.get('trial')
            prior = parent and parent['seq'] < event['seq'] and parent['run'] == event['run']
            edges.append({'from':event['parent'],'to':event['id'],'kind':'invocation',
                          'support':'confirmed' if same_trial and prior else 'unresolved'})
        if event['type'] != 'tool_observed' or payload.get('action',{}).get('tool') != 'send':
            continue
        action = payload['action']
        sources = payload.get('data_lineage',[])
        covered = set()
        for reference in sources:
            source = indexed.get(reference)
            read = source['payload'].get('action',{}) if source else {}
            valid = (source and source['type']=='tool_requested' and read.get('tool')=='read' and
                     source['payload'].get('trial') == payload.get('trial') and
                     source['run']==event['run'] and source['seq']<event['seq'] and read.get('field') in action['fields'])
            # A request alone is not evidence that the tool returned data.
            observed = valid and any(e['type']=='tool_observed' and e.get('parent')==reference and
                                      e['payload'].get('allowed') is True and e['seq']<event['seq'] for e in events)
            if observed:
                covered.add(read['field'])
            edges.append({'from':reference,'to':event['id'],'kind':'data-use',
                          'support':'confirmed' if observed else 'unresolved'})
        if set(action['fields'])-covered:
            edges.append({'from':None,'to':event['id'],'kind':'missing-data-source','support':'unresolved'})
    return {'nodes':nodes,'edges':edges,'rule_version':'explicit-invocation-data-v1',
            'limits':'No timing-only links or hidden-reasoning claims; unrelated events are retained.'}
