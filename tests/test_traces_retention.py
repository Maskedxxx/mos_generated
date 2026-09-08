#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тесты F28 (генерация): журнал чистится по объёму — самые старые session_* целиком; 0 — не удалять."""
import os
import time

import engine

GB = 1024 ** 3


def _session(root, doc_type, name, size, age_sec):
    sd = root / doc_type / name
    sd.mkdir(parents=True)
    (sd / f"{doc_type}.docx").write_bytes(b"x" * size)
    t = time.time() - age_sec
    os.utime(sd, (t, t))
    return sd


def test_prune_traces_removes_oldest(tmp_path):
    old = _session(tmp_path, "prikaz_ppu", "session_1", 1000, 300)
    new = _session(tmp_path, "prikaz_ppu", "session_2", 1000, 100)
    assert engine.prune_traces(tmp_path, 1500 / GB) == [old]
    assert not old.exists() and new.exists()


def test_prune_traces_zero_limit(tmp_path):
    sd = _session(tmp_path, "prikaz_ppu", "session_1", 1000, 300)
    assert engine.prune_traces(tmp_path, 0) == [] and sd.exists()
