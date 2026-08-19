"""`replay_act1.py` 的測試 —— 全部離線,對 tmp_path 造的假 run-dir 跑。

它是講課用的播放器,壞掉的代價是**現場開不出來**,所以測的是三件事:
順序照帳本(不是照檔名排序)、帳本指的檔不見時大聲說出來、轉交字數對不上時看得見。
"""

from __future__ import annotations

import json

import pytest

from replay_act1 import load_ledger, main, rounds_from


def _write_run(tmp_path, events, files):
    (tmp_path / "rounds").mkdir(exist_ok=True)
    (tmp_path / "relay-ledger.jsonl").write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n", encoding="utf-8"
    )
    for rel, body in files.items():
        (tmp_path / rel).write_text(body, encoding="utf-8")
    return tmp_path


def _round(n, asked_chars=10, answered_chars=5, relayed_chars=None):
    return [
        {"event": "asked", "round": n, "chars": asked_chars, "file": f"rounds/r{n}-questions.md"},
        {"event": "answered", "round": n, "chars": answered_chars, "file": f"rounds/r{n}-answers.md"},
        {"event": "relayed", "round": n, "chars": relayed_chars if relayed_chars is not None else answered_chars},
    ]


def _files(ns):
    out = {}
    for n in ns:
        out[f"rounds/r{n}-questions.md"] = f"Q{n}. 問題 {n}"
        out[f"rounds/r{n}-answers.md"] = f"{n} => 答案 {n}"
    return out


def test_順序照帳本而不是檔名排序(tmp_path):
    """帳本裡第 2 輪先出現、第 1 輪後出現時,rounds_from 仍照輪次排 ——
    但重點是它**讀的是帳本裡的 round 欄位**,不是去 glob 目錄。"""
    events = _round(2) + _round(1)
    assert [r["round"] for r in rounds_from(events)] == [1, 2]


def test_帳本沒有的格子留成_None_不補預設(tmp_path):
    events = [{"event": "asked", "round": 1, "chars": 3, "file": "rounds/r1-questions.md"}]
    (r,) = rounds_from(events)
    assert r["asked"] is not None
    assert r["answered"] is None and r["relayed"] is None


def test_播得出來_離開碼_0(tmp_path, capsys):
    _write_run(tmp_path, _round(1) + _round(2), _files([1, 2]))
    assert main([str(tmp_path), "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "Q1. 問題 1" in out and "2 => 答案 2" in out


def test_帳本指的檔不見時離開碼_3(tmp_path, capsys):
    _write_run(tmp_path, _round(1), {})  # 帳本在,檔案不在
    assert main([str(tmp_path), "--no-pause"]) == 3
    assert "檔案不存在" in capsys.readouterr().err


def test_沒有帳本時離開碼_2(tmp_path, capsys):
    assert main([str(tmp_path), "--no-pause"]) == 2
    assert "找不到帳本" in capsys.readouterr().err


def test_轉交字數對不上會印出來(tmp_path, capsys):
    """2026-08-19 真的發生過:轉交途中全形箭頭被正規化,五輪共少 39 字。
    播放器不負責驗證,但**必須讓那個差額出現在螢幕上**。"""
    _write_run(tmp_path, _round(1, answered_chars=100, relayed_chars=61), _files([1]))
    assert main([str(tmp_path), "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "100 字 → 轉交 61 字" in out
    assert "不一致" in out


def test_只播某一輪時仍印出總輪數(tmp_path, capsys):
    _write_run(tmp_path, _round(1) + _round(2) + _round(3), _files([1, 2, 3]))
    assert main([str(tmp_path), "--round", "2", "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "第 2 輪(全 3 輪)" in out
    assert "Q1. 問題 1" not in out


def test_帳本裡沒有那一輪時離開碼_2(tmp_path, capsys):
    _write_run(tmp_path, _round(1), _files([1]))
    assert main([str(tmp_path), "--round", "9", "--no-pause"]) == 2


def test_壞掉的_jsonl_行會指出行號(tmp_path):
    (tmp_path / "relay-ledger.jsonl").write_text('{"event": "asked"}\n{壞掉\n', encoding="utf-8")
    with pytest.raises(ValueError, match="第 2 行"):
        load_ledger(tmp_path)


def test_逗號分隔可以播好幾輪(tmp_path, capsys):
    _write_run(tmp_path, _round(1) + _round(2) + _round(3), _files([1, 2, 3]))
    assert main([str(tmp_path), "--round", "1,3", "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "第 1,3 輪(全 3 輪)" in out
    assert "Q1. 問題 1" in out and "Q3. 問題 3" in out
    assert "Q2. 問題 2" not in out


def test_round_吃到非數字時離開碼_2(tmp_path, capsys):
    _write_run(tmp_path, _round(1), _files([1]))
    assert main([str(tmp_path), "--round", "3,x", "--no-pause"]) == 2
    assert "只吃數字" in capsys.readouterr().err


def test_補字句被拆到自己一行而且一個字都沒少(tmp_path, capsys):
    """拆行是**排版**不是改內容 —— 括號裡的字必須原封不動出現。"""
    _write_run(
        tmp_path,
        _round(1),
        {"rounds/r1-questions.md": "Q1. 這題問什麼?(補:小尺度—§1 GLOSSARY 名詞)",
         "rounds/r1-answers.md": "1 => 答"},
    )
    assert main([str(tmp_path), "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "Q1. 這題問什麼?\n      ↳ (補:小尺度—§1 GLOSSARY 名詞)" in out


def test_raw_不拆行(tmp_path, capsys):
    _write_run(
        tmp_path,
        _round(1),
        {"rounds/r1-questions.md": "Q1. 這題問什麼?(補:小尺度—§1 GLOSSARY 名詞)",
         "rounds/r1-answers.md": "1 => 答"},
    )
    assert main([str(tmp_path), "--no-pause", "--raw"]) == 0
    out = capsys.readouterr().out
    assert "Q1. 這題問什麼?(補:小尺度—§1 GLOSSARY 名詞)" in out
    assert "↳" not in out


def test_答案那一格不拆行(tmp_path, capsys):
    """需求方的原話一個字都不准動 —— 就算他自己打了括號。"""
    _write_run(
        tmp_path,
        _round(1),
        {"rounds/r1-questions.md": "Q1. 問?",
         "rounds/r1-answers.md": "1 => 看有幾集鞋:(每雙的單價x該鞋的數量加總) + 運費"},
    )
    assert main([str(tmp_path), "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "1 => 看有幾集鞋:(每雙的單價x該鞋的數量加總) + 運費" in out


def test_粗體星號不會原樣印出來(tmp_path, capsys):
    """Q26 逼裁決「**總價**」是全場最重要的一題 —— 終端機不吃 markdown,
    原樣印就是一堆星號。非 tty(測試/管線)時去掉星號,輸出保持決定性。"""
    _write_run(
        tmp_path,
        _round(1),
        {"rounds/r1-questions.md": "Q1. 請你定一個:**總價** 指的是哪一個?",
         "rounds/r1-answers.md": "1 => **最後一個**"},
    )
    assert main([str(tmp_path), "--no-pause"]) == 0
    out = capsys.readouterr().out
    assert "**" not in out
    assert "請你定一個:總價 指的是哪一個?" in out
    assert "1 => 最後一個" in out


def test_no_ansi_也去星號(tmp_path, capsys):
    _write_run(
        tmp_path, _round(1),
        {"rounds/r1-questions.md": "Q1. **重點**", "rounds/r1-answers.md": "1 => 答"},
    )
    assert main([str(tmp_path), "--no-pause", "--no-ansi"]) == 0
    out = capsys.readouterr().out
    assert "**" not in out and "\033[" not in out and "Q1. 重點" in out


def test_明確要求_ansi_時轉成粗體逸出序列(tmp_path, capsys):
    from replay_act1 import play
    _write_run(
        tmp_path, _round(1),
        {"rounds/r1-questions.md": "Q1. **重點**", "rounds/r1-answers.md": "1 => 答"},
    )
    assert play(tmp_path, None, do_pause=False, ansi=True) == 0
    assert "\033[1m重點\033[0m" in capsys.readouterr().out


def test_非_tty_時打字模式直接整段印_不逐字(tmp_path, capsys, monkeypatch):
    """逐字寫進管線只是把同樣的字寫慢一點,沒有人在看 —— 而且會讓測試變慢。"""
    import time as _time
    slept = []
    monkeypatch.setattr(_time, "sleep", lambda s: slept.append(s))
    _write_run(tmp_path, _round(1), _files([1]))
    assert main([str(tmp_path), "--no-pause", "--type"]) == 0
    assert slept == [], "非 tty 不該有任何 sleep"
    assert "Q1. 問題 1" in capsys.readouterr().out


def test_cps_為零或負時不逐字(tmp_path, capsys, monkeypatch):
    import time as _time
    slept = []
    monkeypatch.setattr(_time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    from replay_act1 import typewrite
    typewrite("abc", cps=0, enabled=True)
    assert slept == []
    assert "abc" in capsys.readouterr().out


def test_打字模式在_tty_下真的逐字且標點停久一點(capsys, monkeypatch):
    import time as _time
    slept = []
    monkeypatch.setattr(_time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    from replay_act1 import typewrite
    typewrite("ab。c", cps=100, enabled=True)
    assert len(slept) == 4, "四個字元各停一次"
    assert slept[2] > slept[0], "句號後要停久一點(像換氣)"
    assert "ab。c" in capsys.readouterr().out
