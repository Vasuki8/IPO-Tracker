"""Reuse the previous read-only inventory at this cohort's immutable base."""
import importlib.util
from pathlib import Path

PREVIOUS = Path(__file__).resolve().parent.parent / '2026-09-19' / 'inventory.py'
spec = importlib.util.spec_from_file_location('previous_commercial_inventory', PREVIOUS)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)
inventory.BASE = '1e86840856525db2ee2b436ed64f2b6e60374ee0'

if __name__ == '__main__':
    inventory.main()
