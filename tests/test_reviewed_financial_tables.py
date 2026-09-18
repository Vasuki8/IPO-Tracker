import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from review_financial_tables import build_evidence, extract_table, validate_evidence


def fixture(issuer):
    return json.loads((ROOT / 'tests/fixtures' / f'reviewed-financial-{issuer}.json').read_text(encoding='utf-8'))


def financial_value(evidence):
    periods = {}
    for path, cell in evidence['cells'].items():
        period, key = path.split('.')
        periods.setdefault(period, {'period': period})[key] = cell['normalizedValue']
    return {'unit': '₹ crore', 'periods': [periods[p] for p in sorted(periods, reverse=True)]}


def simple(label='EBITDA (₹ in million)', tokens=('10.00', '20.00', '30.00'), metric='ebitdaCr'):
    lines = ['Restated Consolidated Financial Information (₹ in million)',
             ' '*60 + 'Fiscal 2026'.ljust(24) + 'Fiscal 2025'.ljust(24) + 'Fiscal 2024',
             label.ljust(60) + ''.join(t.rjust(24) for t in tokens)]
    return {'page': 1, 'rawLines': lines, 'headerLines': [1], 'columnBounds': [60,84,108,132],
            'endLine': 3, 'metrics': [metric], 'scopeEvidence': {'page': 1, 'rawLines': lines[:1]}}


class FinancialGridTests(unittest.TestCase):
    def test_two_real_documents_all_annual_cells_and_exact_source_spans(self):
        expected = {
            'htel': {'FY2026': [189.404,41.686,22.592,122.017,20.24,2.70],
                     'FY2025': [161.382,35.788,19.619,101.251,21.39,2.35],
                     'FY2024': [137.708,22.551,11.596,82.216,15.11,1.39]},
            'kissht': {'FY2025': [1337.465,403.368,160.621,1005.994,15.97,33.09],
                       'FY2024': [1674.446,358.958,197.29,804.569,24.52,41.27],
                       'FY2023': [984.457,97.711,27.667,566.234,4.89,6.26]}}
        keys = ['revenueCr','ebitdaCr','patCr','netWorthCr','ronwPct','eps']
        for issuer, years in expected.items():
            evidence = fixture(issuer)
            self.assertEqual(build_evidence(evidence['tables']), evidence)
            self.assertTrue(validate_evidence(financial_value(evidence), evidence))
            self.assertEqual(len(evidence['cells']), 18)
            for year, values in years.items():
                for key, value in zip(keys, values):
                    cell = evidence['cells'][year+'.'+key]
                    self.assertEqual(cell['normalizedValue'], value)
                    line = evidence['tables'][cell['table']]['rawLines'][cell['line']]
                    self.assertEqual(line[cell['start']:cell['end']], cell['token'])
        self.assertEqual(fixture('kissht')['cells']['FY2025.eps']['sourceColumn'], 1)

    def test_integer_negative_and_null_are_preserved(self):
        cells = extract_table(simple(tokens=('10','(20.00)','—')))
        self.assertEqual([c['normalizedValue'] for c in cells.values()], [1,-2,None])
        for token in ('1,234.00','1,23,456.00'):
            self.assertEqual(extract_table(simple(tokens=(token,token,token)))['FY2026.ebitdaCr']['normalizedValue'], round(float(token.replace(',',''))*.1,6))

    def test_ambiguous_units_labels_and_malformed_cells_fail_closed(self):
        cases = [('EBITDA (%)','ebitdaCr'), ('EBITDA (Margin) (₹ in million)','ebitdaCr'),
                 ('EBITDA to Total Income','ebitdaCr'), ('Net Worth (per share)','netWorthCr'),
                 ('EBITDA (₹ in billion)','ebitdaCr'), ('Basic Earnings per share (in ₹ million)','eps')]
        for label, metric in cases:
            with self.subTest(label=label), self.assertRaises(ValueError):
                extract_table(simple(label=label,metric=metric))
        for token in ('1,,0.00','2,0.00','30,.00','(10.00','(-10.00)','NaN','1e6',''):
            with self.subTest(token=token), self.assertRaises(ValueError):
                extract_table(simple(tokens=(token,'20.00','30.00')))
        with self.assertRaises(ValueError):
            extract_table(simple(label='Basic Earnings per share (₹)',metric='eps',tokens=('10%','20%','30%')))
        with self.assertRaises(ValueError):
            extract_table(simple(label='Return on Net Worth',metric='ronwPct',tokens=('—','—','—')))

    def test_scope_period_and_currency_conflicts_fail_closed(self):
        for mutation in ('standalone','mixed_currency','quarter','duplicate_date','cropped_column'):
            table = simple()
            if mutation == 'standalone': table['rawLines'][0] = table['rawLines'][0].replace('Consolidated','Standalone')
            elif mutation == 'mixed_currency': table['rawLines'][0] += ' USD million'
            elif mutation == 'quarter': table['rawLines'][1] = ' '*60 + ''.join(('3 months March 31, '+str(y)).ljust(24) for y in (2026,2025,2024))
            elif mutation == 'duplicate_date': table['rawLines'][1] = table['rawLines'][1].replace('2025','2026')
            else: table['columnBounds'][-1] -= 2
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): extract_table(table)

    def test_repeated_or_corroborating_conflicts_are_rejected(self):
        table = simple(); table['rawLines'].append(table['rawLines'][2].replace('10.00','11.00')); table['endLine'] += 1
        with self.assertRaises(ValueError): extract_table(table)
        left,right=simple(),simple(tokens=('11.00','20.00','30.00'))
        with self.assertRaises(ValueError): build_evidence([left,right])

    def test_missing_metric_tampered_source_or_shifted_cell_cannot_replay(self):
        for mutation in ('cell','value','metric','unit','span'):
            evidence=fixture('htel'); value=financial_value(evidence)
            if mutation=='cell': evidence['cells']['FY2026.eps']['normalizedValue']=83531840
            elif mutation=='value': value['periods'][0]['eps']=83531840
            elif mutation=='metric': del value['periods'][0]['netWorthCr']
            elif mutation=='unit': value['unit']='₹ million'
            else: evidence['cells']['FY2026.eps']['start']+=1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): validate_evidence(value,evidence)


if __name__ == '__main__': unittest.main()
