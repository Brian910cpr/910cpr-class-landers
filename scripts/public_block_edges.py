"""Pure occupied-block geometry. No service access, booking writes or publication."""
from datetime import datetime, timedelta
import hashlib

VERSION = 'occupied-block-edges.v1'

def key(value):
    return ' '.join(str(value or '').lower().split())

def merged_blocks(occupancy):
    blocks = []
    classes = [x for x in occupancy if x.get('is_training') and x.get('start') and x.get('end') and x['end'] > x['start'] and key(x.get('instructor')) not in {'', 'unknown'}]
    for item in sorted(classes, key=lambda x: (key(x['instructor']), x['start'], key(x['location']))):
        source = {'source': item.get('source_file'), 'id': item.get('source_event_id'), 'courseId': item.get('course_id'), 'start': item['start'].isoformat(), 'end': item['end'].isoformat()}
        previous = blocks[-1] if blocks else None
        merge = previous and key(previous['instructor']) == key(item['instructor']) and key(previous['location']) == key(item['location']) and item['start'] <= previous['end']
        if merge:
            previous['end'] = max(previous['end'], item['end'])
            if source not in previous['sources']: previous['sources'].append(source)
        else:
            ident = hashlib.sha256((key(item['instructor'])+'|'+key(item['location'])+'|'+item['start'].isoformat()).encode()).hexdigest()[:16]
            blocks.append({'id': 'occupied-'+ident, 'start': item['start'], 'end': item['end'], 'instructor': item['instructor'], 'location': item['location'], 'sources': [source]})
    return blocks

def serialize_blocks(blocks):
    return [{**x, 'start': x['start'].isoformat(), 'end': x['end'].isoformat()} for x in blocks]

def plan_starts(ws, we, instructor, location, minutes, blocks, occupancy):
    """Identify both edges before downstream constraints; never scan planted days."""
    consume = timedelta(minutes=minutes)
    first, last = ws.date(), (we-timedelta(microseconds=1)).date()
    relevant = [b for b in blocks if key(b['instructor']) == key(instructor) and
                (b['start'].date() <= last and b['end'].date() >= first or
                 ws <= b['start']-consume < we or ws <= b['end'] < we)]
    if relevant:
        result = []
        for b in relevant:
            for side, instant in [('left', b['start']), ('right', b['end'])]:
                start = instant-consume if side == 'left' else instant
                result.append({'start': start, 'mode': 'barnacle', 'geometryReasons': [] if key(b['location']) == key(location) else ['OFFSITE_EDGE_LOCATION'],
                               'edge': {'blockId': b['id'], 'side': side, 'time': instant.isoformat()}})
        return result
    free = [(ws, we)]
    for busy in occupancy:
        if not (key(busy.get('instructor')) == key(instructor) or busy.get('instructor_unassigned') or key(busy.get('location')) == key(location)):
            continue
        left = busy.get('instructor_conflict_start') or busy.get('start')
        right = busy.get('instructor_conflict_end') or busy.get('end')
        if not left or not right: raise ValueError('Unresolved occupied interval')
        revised = []
        for a, z in free:
            if right <= a or left >= z: revised.append((a, z))
            else:
                if a < left: revised.append((a, left))
                if right < z: revised.append((right, z))
        free = revised
    result = []
    for a, z in free:
        step = timedelta(minutes=60 if z-a >= timedelta(minutes=180) else 30)
        cursor = a
        while cursor+consume <= z:
            result.append({'start': cursor, 'mode': 'free', 'geometryReasons': [], 'freeInterval': {'start': a.isoformat(), 'end': z.isoformat(), 'stepMinutes': int(step.total_seconds()/60)}})
            cursor += step
    return result

def valid_edge(offer, trace):
    edge = offer.get('blockEdge') or {}
    block = next((b for b in trace.get('blocks', []) if b['id'] == edge.get('blockId')), None)
    if not block or not block.get('sources'): return False
    if key(block['instructor']) != key(offer.get('instructor')) or key(block['location']) != key(offer.get('location')): return False
    start = datetime.fromisoformat(offer['date']+'T'+offer['startTime'])
    end = start+timedelta(minutes=int(offer['schedulerConsumptionMinutes']))
    side = edge.get('side'); instant = datetime.fromisoformat(block['start' if side == 'left' else 'end'])
    return edge.get('time') == instant.isoformat() and ((side == 'left' and end == instant) or (side == 'right' and start == instant))


def retain_validated_roles(payload, full_groups):
    """Classify traced, already hard-validated edges. Skills have no daily cap."""
    trace = payload['occupiedBlockEdges']; rows = []
    for day in payload.get('dates', []):
        for slot in day.get('startTimes', []):
            for offer in slot.get('courses', []):
                if offer.get('offerType') == 'seated_class' or offer.get('schedule_role') == 'free_day': rows.append(offer)
                elif valid_edge(offer, trace): rows.append({**offer, 'schedule_role': 'barnacle', 'scheduleRole': 'barnacle'})
    actual_full = set()
    for block in trace.get('blocks', []):
        for source in block['sources']:
            cid = str(source.get('courseId') or '')
            if cid in full_groups: actual_full.add((key(block['instructor']), datetime.fromisoformat(source['start']).date().isoformat(), full_groups[cid]))
    chosen = {}; retained = []
    for offer in sorted(rows, key=lambda x:(x.get('date',''), x.get('startTime',''), x.get('courseId',''))):
        if offer.get('offerType') == 'seated_class' or offer.get('schedule_role') != 'barnacle' or offer.get('offerKind') != 'full': retained.append(offer); continue
        group = (key(offer.get('instructor')), offer['date'], full_groups.get(str(offer['courseId']), str(offer['courseId'])))
        if group in actual_full: continue
        when = offer['startTime']
        if group not in chosen: chosen[group] = when
        if chosen[group] == when: retained.append(offer)
    return retained
