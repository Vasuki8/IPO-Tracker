"""Isolated compatibility modules for archived parser entrypoints.

Legacy wrappers assign functions and registries on their dependencies. Each
load gets a private dependency graph, so importing one wrapper cannot mutate
another caller's parser. New production code uses offer_parser's explicit API.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from contextvars import ContextVar
from pathlib import Path
from uuid import uuid4

_graph: ContextVar[dict | None] = ContextVar("ipo_parser_graph", default=None)


def isolated_module(name: str):
    if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
        raise ValueError("Expected a local Python module name")
    graph = _graph.get()
    token = None
    if graph is None:
        graph = {}
        token = _graph.set(graph)
    try:
        if name in graph:
            return graph[name]
        path = Path(__file__).resolve().parent / (name + ".py")
        private_name = "_ipo_compat_" + uuid4().hex
        spec = importlib.util.spec_from_file_location(private_name, path)
        module = importlib.util.module_from_spec(spec)
        graph[name] = module
        # dataclasses consult sys.modules during class construction.
        sys.modules[private_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(private_name, None)
        return module
    finally:
        if token is not None:
            _graph.reset(token)
