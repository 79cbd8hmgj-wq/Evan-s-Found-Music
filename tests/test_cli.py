"""Regressions for mandatory served-song exclusions in the CLI."""

import sys

from found_music import cli


def test_cli_uses_default_seen_ledger(tmp_path, monkeypatch, capsys):
    candidates = tmp_path / "candidates.csv"
    feedback = tmp_path / "feedback.csv"
    library = tmp_path / "library.csv"
    seen = tmp_path / "seen.csv"
    candidates.write_text("title,artist,year,genres,tags\\nServed,Artist,2005,,\\nFresh,Other,2005,,\\n", encoding="utf-8")
    feedback.write_text("title,artist,year,genres,tags,feedback\\n", encoding="utf-8")
    library.write_text("title,artist,year,genres,tags\\n", encoding="utf-8")
    seen.write_text("title,artist,year,genres,tags,batch_id\\nServed,Artist,2005,, ,previous\\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["found-music", "--candidates", str(candidates), "--feedback", str(feedback), "--library", str(library), "--size", "2"])
    cli.main()
    output = capsys.readouterr().out
    assert "Fresh" in output
    assert "Served" not in output
