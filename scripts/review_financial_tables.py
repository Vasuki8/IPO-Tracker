"""Offline review of annotated, fixed-layout annual financial tables.

The reviewer selects physical table/header bounds, never expected values. Every
cell is read from the retained grid; date, unit, row and scope are replayed before
publication. This helper is deliberately not a general collector fallback.
"""
from __future__ import annotations

import math
import re
from datetime import date, datetime

PARSER_VERSION = 'reviewed-financial-grid-v1'
METRICS = {
    'revenueCr': r'Revenue from Operations?',
    'netWorthCr': r'Net Worth',
    'patCr': r'(?:Net )?Profit (?:for the (?:period/year|year)|after Tax)',
    'ebitdaCr': r'EBITDA',
    'ronwPct': r'Return on Net Worth',
    'eps': r'Basic Earnings per (?:equity )?share',
    'dilutedEps': r'Diluted Earnings per (?:equity )?share',
    'totalIncomeCr': r'Total Income',
}
_GROUPED = r'(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d+)?'
_NUMBER = re.compile(r'(?:(?:-?' + _GROUPED + r'|\(' + _GROUPED + r'\))%?|[-–—])')
_UNIT = re.compile(r'(?:₹\s*(?:in\s+)?|(?:Rs\.?|INR)\s*(?:in\s+)?)(millions?|crores?|lakhs?)', re.I)


def _space(text):
    return ' '.join(text.split())


def _lines(lines):
    if (not isinstance(lines, list) or not lines or any(not isinstance(x, str)
            or any(c in x for c in '\r\n\t\f') for x in lines)):
        raise ValueError('Exact physical source lines are required')
    return lines


def _page(page):
    if type(page) is not int or page < 1:
        raise ValueError('Positive physical PDF page required')


def _unit(text):
    if re.search(r'USD|US\s*\$|\bEUR\b|\bGBP\b|billion|thousand', text, re.I):
        raise ValueError('Unknown or mixed currency unit')
    units = {m[1].lower().rstrip('s') for m in _UNIT.finditer(text)}
    if len(units) != 1:
        raise ValueError('Currency unit is absent or contradictory')
    name = units.pop()
    return name, {'million': .1, 'crore': 1, 'lakh': .01}[name]


def extract_table(table):
    """Replay a reviewer-bounded grid, retaining nulls and excluding interim dates."""
    raw = _lines(table['rawLines'])
    _page(table['page'])
    scope = table['scopeEvidence']
    _page(scope['page'])
    scope_text = _space('\n'.join(_lines(scope['rawLines'])))
    if not re.search(r'Restated Consolidated (?:Financial|Statement)', scope_text, re.I):
        raise ValueError('Explicit consolidated source context required')
    if re.search(r'\bstandalone\b', scope_text, re.I):
        raise ValueError('Ambiguous financial scope')
    header = table['headerLines']
    bounds = table['columnBounds']
    if (not isinstance(header, list) or not header or header != sorted(set(header))
            or any(type(n) is not int or n < 0 or n >= len(raw) for n in header)
            or not isinstance(bounds, list) or not 3 <= len(bounds) <= 6
            or any(type(n) is not int or n < 1 for n in bounds)
            or bounds != sorted(set(bounds))):
        raise ValueError('Invalid physical grid/header bounds')
    if re.search(r'\bstandalone\b', '\n'.join(raw[:max(header) + 1]), re.I):
        raise ValueError('Table scope conflicts with reviewed consolidated context')
    # Never split a physical word at a column divider.
    for line in (raw[n] for n in header):
        for boundary in bounds:
            if len(line) > boundary and line[boundary - 1:boundary + 1].strip() == line[boundary - 1:boundary + 1]:
                raise ValueError('Grid cuts a source token')
    dates = []
    for left, right in zip(bounds, bounds[1:]):
        text = _space(' '.join(raw[n][left:right] for n in header))
        matches = re.findall(r'(March|December|September|June)\s+(31|30),?\s+(20\d{2})|Fiscal\s+(20\d{2})', text, re.I)
        if len(matches) != 1:
            raise ValueError('Each column needs one explicit reporting date')
        month, day, year, fiscal = matches[0]
        when = date(int(year or fiscal), {'march': 3, 'june': 6, 'september': 9, 'december': 12}.get(month.lower(), 3), int(day or 31))
        if (when.month, when.day) == (3, 31):
            if (re.search(r'months?|quarter|weeks?', text, re.I)
                    or not (re.search(r'year ended|Fiscal', text, re.I)
                            or re.search(r'financial years? ended', scope_text, re.I))):
                raise ValueError('March date does not establish an annual reporting period')
        dates.append((when, text))
    annual = [i for i, (when, _) in enumerate(dates) if (when.month, when.day) == (3, 31)]
    if len(annual) < 2 or len({dates[i][0] for i in annual}) != len(annual):
        raise ValueError('At least two distinct annual columns required')
    requested = table['metrics']
    if not isinstance(requested, list) or not requested or len(set(requested)) != len(requested) or set(requested) - METRICS.keys():
        raise ValueError('Unsupported or duplicate metric selection')
    stop = table['endLine']
    if type(stop) is not int or not max(header) < stop <= len(raw):
        raise ValueError('Invalid table end')
    rows = []
    for n in range(max(header) + 1, stop):
        cells = [raw[n][a:b].strip() for a, b in zip(bounds, bounds[1:])]
        if not any(cells):
            if rows and raw[n][:bounds[0]].strip():
                rows[-1]['label'] += ' ' + raw[n][:bounds[0]].strip()
            continue
        rows.append({'line': n, 'label': raw[n][:bounds[0]].strip(), 'tokens': cells})
    result = {}
    for row in rows:
        label = _space(row['label'])
        # Notes may be in a distinct declared column (never a guessed extra cell).
        note_bounds = table.get('noteColumn')
        if note_bounds:
            a, b = note_bounds
            if not (0 < a < b <= bounds[0]) or not re.search(r'\bNotes\b', ' '.join(raw[n][a:b] for n in header), re.I):
                raise ValueError('Note column lacks its explicit header')
            note = raw[row['line']][a:b].strip()
            if note and not re.fullmatch(r'\d{1,3}', note):
                raise ValueError('Unsupported note reference')
            label = _space(raw[row['line']][:a])
        metric = None
        for key, pattern in METRICS.items():
            match = re.match(pattern + r'\b', label, re.I)
            if not match:
                continue
            tail = label[match.end():]
            # Only balanced annotations may follow an exact metric name. Thus
            # EBITDA ratios/margins and share-count rows can never be currencies/EPS.
            annotations = re.findall(r'\(([^()]*)\)', tail)
            allowed = all(re.fullmatch(r'(?:[ivx]+|\d{1,2}|[A-Z](?:\s*[=+*/-]\s*[A-Z])+|[A-Z]|%|(?:in\s*)?(?:₹|Rs\.?)\s*(?:in\s*)?(?:millions?|crores?|lakhs?)?)', _space(a), re.I) for a in annotations)
            remainder = re.sub(r'\([^()]*\)', '', tail).strip(' #*')
            if not remainder and allowed:
                metric = key
                break
        if metric not in requested:
            continue
        if raw[row['line']][bounds[-1]:].strip():
            raise ValueError('Unaccounted source cells beyond the selected columns')
        for boundary in bounds:
            line = raw[row['line']]
            if len(line) > boundary and not any(c.isspace() for c in line[boundary - 1:boundary + 1]):
                raise ValueError('Grid cuts a financial source token')
        if any(not _NUMBER.fullmatch(token) for token in row['tokens']):
            raise ValueError('Incomplete or ambiguous financial row')
        if metric.endswith('Cr'):
            if '%' in label:
                raise ValueError('Percentage row cannot supply currency')
            row_units = list(_UNIT.finditer(label))
            unit, factor = _unit(label if row_units else '\n'.join(raw[:max(header) + 1]))
            header_units = list(_UNIT.finditer('\n'.join(raw[:max(header) + 1])))
            if row_units and header_units and _unit('\n'.join(raw[:max(header) + 1]))[0] != unit:
                raise ValueError('Row and table currency units conflict')
            if any('%' in token for token in row['tokens']):
                raise ValueError('Percentage cannot supply currency')
        else:
            unit, factor = ('percent', 1) if metric.endswith('Pct') else ('rupees per share', 1)
            nonnull = [t for t in row['tokens'] if t not in {'-', '–', '—'}]
            if metric.endswith('Pct') and not ('%' in label or (nonnull and all(t.endswith('%') for t in nonnull))):
                raise ValueError('Percentage unit is not explicit')
            if not metric.endswith('Pct') and not re.search(r'₹|\bRs\.?', label):
                raise ValueError('Per-share rupee unit is not explicit')
            if not metric.endswith('Pct') and any('%' in t for t in row['tokens']):
                raise ValueError('Percentage cannot supply per-share rupees')
            if not metric.endswith('Pct') and _UNIT.search(label):
                raise ValueError('Scaled currency cannot supply unscaled EPS')
        for i in annual:
            token = row['tokens'][i]
            value = None if token in {'-', '–', '—'} else round(float(token.strip('()%').replace(',', '')) * (-1 if token.startswith('(') else 1) * factor, 6)
            if value is not None and not math.isfinite(value):
                raise ValueError('Non-finite source cell')
            path = 'FY' + str(dates[i][0].year) + '.' + metric
            left, right = bounds[i:i + 2]
            line = raw[row['line']]
            start = left + len(line[left:right]) - len(line[left:right].lstrip())
            cell = {'page': table['page'], 'line': row['line'], 'start': start, 'end': start + len(token),
                    'token': token, 'row': label, 'reportingDate': dates[i][0].isoformat(),
                    'header': dates[i][1], 'sourceColumn': i, 'originalUnit': unit,
                    'normalizedValue': value, 'scope': 'consolidated'}
            if path in result and result[path]['normalizedValue'] != value:
                raise ValueError('Conflicting repeated source metric')
            result[path] = cell
    if {path.split('.')[1] for path in result} != set(requested):
        raise ValueError('Selected metric is absent or unsupported')
    return result


def build_evidence(tables):
    cells = {}
    for index, table in enumerate(tables):
        for path, cell in extract_table(table).items():
            if path in cells and cells[path]['normalizedValue'] != cell['normalizedValue']:
                raise ValueError('Reviewed source tables conflict')
            cells[path] = {**cell, 'table': index}
    return {'method': PARSER_VERSION, 'page': tables[0]['page'], 'tables': tables, 'cells': cells}


def validate_evidence(value, detail):
    if not isinstance(detail, dict) or detail.get('method') != PARSER_VERSION:
        raise ValueError('Reviewed financial method required')
    if build_evidence(detail['tables']) != detail:
        raise ValueError('Financial cells do not replay from source grids')
    if not isinstance(value, dict) or value.get('unit') != '₹ crore':
        raise ValueError('Canonical financial unit required')
    expected = {}
    for row in value.get('periods', []):
        for key, number in row.items():
            if key == 'period':
                continue
            path = row['period'] + '.' + key
            if path in expected:
                raise ValueError('Duplicate financial period/metric')
            expected[path] = number
    if not expected or expected != {p: cell['normalizedValue'] for p, cell in detail['cells'].items()}:
        raise ValueError('Every retained metric must have exactly matching source evidence')
    return True


def has_reviewed_financial_evidence(record):
    from final_prospectus_policy import is_final_prospectus
    from final_prospectus_identity import known_non_final_document_url
    proof = (record.get('staticFieldProvenance') or {}).get('financials')
    if (not isinstance(proof, dict) or proof.get('parserVersion') != PARSER_VERSION
            or proof.get('field') != 'financials' or proof.get('value') != record.get('financials')
            or not record.get('openDate') or proof.get('issueOpenDate') != record['openDate']
            or not str(proof.get('sourceUrl', '')).startswith('https://')
            or not re.fullmatch(r'[a-f0-9]{64}', str(proof.get('sha256') or ''))
            or not is_final_prospectus({'type': proof.get('documentType'), 'url': proof.get('sourceUrl')})
            or known_non_final_document_url(record, proof['sourceUrl'])):
        return False
    try:
        identity = proof['identity']
        if (set(identity) != {'id', 'company', 'symbol', 'openDate'}
                or any(not isinstance(v, str) or not v or record.get(k) != v for k, v in identity.items())):
            return False
        date.fromisoformat(proof['documentDate'])
        if datetime.fromisoformat(proof['checkedAt']).utcoffset() is None:
            return False
        return validate_evidence(record['financials'], proof['evidence'])
    except (ValueError, TypeError, KeyError, IndexError):
        return False
