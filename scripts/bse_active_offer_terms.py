"""Replay the reviewed BSE DisplayIPO family without collecting or writing.

The current-issue table binds the board and the exact detail link. The detail
table supplies only its labelled price, market lot and minimum quantity. Its
share count does not establish the whole offer, composition or a rupee amount.
Standard library only: the deployed release verifier also replays these bytes.
"""
from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
import re
from urllib.parse import parse_qsl, urljoin, urlsplit

VERSION = 'bse-displayipo-active-terms-v1'
FIELDS = {'priceBand', 'marketLot', 'minimumBidQuantity'}
IDENTITY = ('id', 'company', 'board', 'openDate', 'closeDate')
HOSTS = {'www.bseindia.com', 'beta.bseindia.com'}


class Node:
    def __init__(self, tag, attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        return ' '.join(' '.join(child.text() if isinstance(child, Node) else child
                                 for child in self.children).split())

    def descendants(self, tag=None):
        for child in self.children:
            if isinstance(child, Node):
                if tag is None or child.tag == tag:
                    yield child
                yield from child.descendants(tag)


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node('document')
        self.stack = [self.root]
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                       'link', 'meta', 'param', 'source', 'track', 'wbr'}:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def _name(value):
    return re.sub('[^a-z0-9]', '', re.sub(r'\bltd\.?\b', 'limited', value.lower()))


def _url(url, path, keys):
    parsed = urlsplit(url)
    items = parse_qsl(parsed.query, keep_blank_values=True)
    if (parsed.scheme != 'https' or parsed.netloc not in HOSTS or parsed.fragment
            or parsed.path != path or len(items) != len(keys)
            or {key for key, _ in items} != keys):
        raise ValueError('Unsupported or ambiguous BSE source URL')
    return dict(items)


def detail_identity(url):
    query = _url(url, '/markets/publicIssues/DisplayIPO.aspx',
                 {'id', 'type', 'idtype', 'status', 'IPONo', 'startdt'})
    if (query['type'] != 'IPO' or query['idtype'] != '1' or query['status'] not in {'F', 'L'}
            or any(not re.fullmatch('[1-9][0-9]*', query[key]) for key in ('id', 'IPONo'))):
        raise ValueError('BSE source is not an identified active IPO')
    datetime.strptime(query['startdt'], '%d/%m/%Y')
    return query


def _one(nodes, message):
    nodes = list(nodes)
    if len(nodes) != 1:
        raise ValueError(message)
    return nodes[0]


def _by_id(root, identifier):
    return _one((node for node in root.descendants() if node.attrs.get('id') == identifier),
                'Missing or ambiguous BSE page marker: ' + identifier)


def _rows(table):
    # Never collapse a nested layout table into a fabricated issuer row.
    for child in table.children:
        if isinstance(child, Node):
            if child.tag == 'tr':
                yield child
            elif child.tag in {'tbody', 'thead', 'tfoot'}:
                yield from (row for row in child.children if isinstance(row, Node) and row.tag == 'tr')


def _cells(row):
    return [child for child in row.children if isinstance(child, Node) and child.tag in {'td', 'th'}]


def _band(text):
    match = re.fullmatch(r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)', text)
    if not match or not 0 < float(match[1]) <= float(match[2]) < 1_000_000:
        raise ValueError('Unsupported BSE price-band row')
    return {'min': float(match[1]), 'max': float(match[2])}


def parse_response(source, identity):
    """Require agreement between one current row and its own detail table."""
    query = detail_identity(source['url'])
    index = source['index']
    current_query = _url(index['url'], '/markets/PublicIssues/IPOIssues_new.aspx', {'id', 'Type'})
    if current_query != {'id': '1', 'Type': 'P'}:
        raise ValueError('BSE receipt needs the reviewed current-issue index')
    opened = datetime.strptime(query['startdt'], '%d/%m/%Y').date().isoformat()
    if opened != identity['openDate']:
        raise ValueError('BSE detail URL offer date differs from the issuer')
    matches = []
    index_doc = Document(index['responseText']).root
    for table_index, table in enumerate(index_doc.descendants('table')):
        for row_index, row in enumerate(_rows(table)):
            cells = _cells(row)
            if len(cells) != 8 or any(list(cell.descendants('table')) for cell in cells):
                continue
            links = list(cells[0].descendants('a'))
            same_name = _name(cells[0].text()) == _name(identity['company'])
            same_link = any(urljoin(index['url'], link.attrs.get('href', '')) == source['url'] for link in links)
            if not same_name and not same_link:
                continue
            if not same_name or len(links) != 1 or not same_link:
                raise ValueError('Conflicting BSE issuer/detail-link identity')
            values = [cell.text() for cell in cells]
            dates = [datetime.strptime(value, '%d-%m-%Y').date().isoformat() for value in values[2:4]]
            expected_status = 'Forthcoming' if query['status'] == 'F' else 'Live'
            if (values[1] != identity['board'] or values[6] != 'IPO' or values[7] != expected_status
                    or dates != [identity['openDate'], identity['closeDate']] or dates[0] > dates[1]):
                raise ValueError('Conflicting BSE board/category/offer window')
            matches.append((table_index, row_index, values))
    index_table, index_row, index_values = _one(matches, 'Missing or duplicate BSE current-issue identity')

    doc = Document(source['responseText']).root
    form = _by_id(doc, 'aspnetForm')
    if detail_identity(urljoin(source['url'], form.attrs.get('action', ''))) != query:
        raise ValueError('BSE response form belongs to another issue')
    expected_kind = 'Book Building - ' + ('Forthcoming' if query['status'] == 'F' else 'Live')
    if _by_id(doc, 'ctl00_ContentPlaceHolder1_lblIssuetype').text() != expected_kind:
        raise ValueError('Unsupported BSE offer type/status')
    if _by_id(doc, 'ctl00_ContentPlaceHolder1_lblupddate').text():
        raise ValueError('BSE source observation clock needs separate supported review')
    panel = _by_id(doc, 'ctl00_ContentPlaceHolder1_UpdatePanel1')
    tables = []
    for table in panel.descendants('table'):
        headers = [cell for row in _rows(table) for cell in _cells(row)
                   if 'TTHeader' in cell.attrs.get('class', '').split()]
        if headers:
            header = _one(headers, 'Ambiguous BSE issuer table headings')
            if _name(header.text()) != _name(identity['company']):
                raise ValueError('Conflicting BSE detail issuer')
            tables.append(table)
    table = _one(tables, 'Missing or duplicate BSE detail issuer table')
    table_index = list(doc.descendants('table')).index(table)
    labels = {}
    for row_index, row in enumerate(_rows(table)):
        cells = _cells(row)
        if len(cells) != 2 or 'TTRow_left' not in cells[0].attrs.get('class', '').split():
            continue
        if any(list(cell.descendants('table')) for cell in cells):
            raise ValueError('Unsupported nested BSE term row')
        title, raw = [cell.text() for cell in cells]
        if title in labels:
            raise ValueError('Duplicate BSE term label: ' + title)
        labels[title] = {'row': row_index, 'title': title, 'raw': raw, 'table': f'/html/tables/{table_index}'}
    if labels['Security Type']['raw'] != 'Equity':
        raise ValueError('BSE detail is not an equity IPO')
    symbol = labels['Symbol']['raw']
    if (not re.fullmatch('[A-Z][A-Z0-9]{0,19}', symbol)
            or identity.get('symbol') not in (None, '', symbol)):
        raise ValueError('Conflicting BSE source symbol')
    dates = [datetime.strptime(value, '%d %b %Y').date().isoformat()
             for value in labels['Issue Period']['raw'].split(' to ')]
    if dates != [identity['openDate'], identity['closeDate']]:
        raise ValueError('Conflicting BSE detail offer window')
    image = _by_id(doc, 'ctl00_ContentPlaceHolder1_Image1')
    currency = [node for node in doc.descendants('td')
                if image in list(node.descendants('img')) and node.text() == 'All Prices in']
    _one(currency, 'Missing BSE price currency heading')
    if image.attrs.get('src') != '../../../include/images/rs_b.gif':
        raise ValueError('Unreviewed BSE currency marker')
    price = _band(labels['Price Band']['raw'])
    if price != _band(index_values[4]):
        raise ValueError('BSE index and detail prices conflict')
    fields = {'priceBand': {**labels['Price Band'], 'value': price, 'unit': 'INR/share',
                           'currencyLocator': '#ctl00_ContentPlaceHolder1_Image1 (All Prices in)'}}
    unresolved = {'lotSize': 'parser-unsupported: Market Lot does not prove the bidding increment',
                  'issueSizeCr': 'source-evidence-required: no explicit whole-offer monetary amount',
                  'issueComposition': 'source-evidence-required: detail share count is not a fresh/OFS split',
                  'symbol': 'source-identity-only: canonical symbol is outside this terms transaction'}
    for field, label in [('marketLot', 'Market Lot'), ('minimumBidQuantity', 'Minimum Bid Quantity')]:
        item = labels.get(label)
        if item and re.fullmatch('[1-9][0-9]*', item['raw']) and int(item['raw']) <= 100_000:
            fields[field] = {**item, 'value': int(item['raw']), 'unit': 'shares'}
        else:
            unresolved[field] = 'disclosure-absent' if item is None else 'parser-unsupported'
    return {'fields': fields, 'unresolved': unresolved, 'sourceIdentity': {
        'issuer': identity['company'], 'symbol': symbol, 'securityType': 'Equity',
        'board': identity['board'], 'issueId': query['id'], 'ipoNumber': query['IPONo'],
        'openDate': dates[0], 'closeDate': dates[1], 'indexTable': f'/html/tables/{index_table}',
        'indexRow': index_row, 'indexCells': index_values}}
