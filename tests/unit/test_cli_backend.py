"""Unit tests for extended CLI commands (ingest, nearby, grievance)."""

import json
from pathlib import Path

from click.testing import CliRunner

from india_ate.cli import app


def test_cli_ingest_recall_enforcement_ondc_ifct_and_queries(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "cli_backend.db"

    recall_file = tmp_path / "recall.json"
    recall_file.write_text(
        json.dumps(
            [
                {
                    "fssai_id": "13624001000999",
                    "legal_name": "Verified Kitchen Ltd",
                    "recall_date": "2026-04-01",
                    "status": "Initiated",
                    "verbatim_summary": "Batch recall",
                    "postal_code": "500081",
                }
            ]
        ),
        encoding="utf-8",
    )
    res = runner.invoke(
        app, ["ingest", "recall", "--from-file", str(recall_file), "--db", str(db_path)]
    )
    assert res.exit_code == 0
    assert json.loads(res.output)["events_ingested"] == 1

    ondc_file = tmp_path / "ondc.json"
    ondc_file.write_text(
        json.dumps(
            [
                {
                    "fssai_id": "13624001000777",
                    "legal_name": "Good Kitchen Ltd",
                    "display_name": "Good Bowl",
                    "postal_code": "500081",
                }
            ]
        ),
        encoding="utf-8",
    )
    res = runner.invoke(
        app, ["ingest", "ondc", "--from-file", str(ondc_file), "--db", str(db_path)]
    )
    assert res.exit_code == 0
    assert json.loads(res.output)["premises_ingested"] == 1

    enf_file = tmp_path / "enf.json"
    enf_file.write_text(
        json.dumps(
            [
                {
                    "fssai_id": "23624001000123",
                    "legal_name": "Suspended Cloud",
                    "event_date": "2026-04-02",
                    "status": "Suspended",
                    "verbatim_summary": "Suspended by TG SAFE",
                    "postal_code": "500081",
                }
            ]
        ),
        encoding="utf-8",
    )
    res = runner.invoke(
        app,
        [
            "ingest",
            "enforcement",
            "--source-name",
            "Telangana TG SAFE",
            "--from-file",
            str(enf_file),
            "--db",
            str(db_path),
        ],
    )
    assert res.exit_code == 0

    ifct_file = tmp_path / "ifct.csv"
    ifct_file.write_text(
        "code,name,enerc,protcnt\nA001,Amaranth,1490,14.59\n",
        encoding="utf-8",
    )
    res = runner.invoke(
        app, ["ingest", "ifct", "--from-file", str(ifct_file), "--db", str(db_path)]
    )
    assert res.exit_code == 0
    assert json.loads(res.output)["entities_ingested"] >= 3

    nearby_res = runner.invoke(app, ["nearby", "500081", "--db", str(db_path)])
    assert nearby_res.exit_code == 0
    nearby_data = json.loads(nearby_res.output)
    assert len(nearby_data["options"]) == 1
    assert nearby_data["options"][0]["premises"]["legal_name"] == "Good Kitchen Ltd"

    grievance_res = runner.invoke(
        app,
        [
            "grievance",
            "23624001000123",
            "--category",
            "spoiled_food",
            "--description",
            "Arrived spoiled",
            "--incident-date",
            "2026-04-03",
            "--db",
            str(db_path),
        ],
    )
    assert grievance_res.exit_code == 0
    assert json.loads(grievance_res.output)["escalation_deadline"] == "2026-04-18"

    bad_grievance = runner.invoke(
        app,
        [
            "grievance",
            "23624001000123",
            "--category",
            "spoiled_food",
            "--description",
            "Arrived spoiled",
            "--incident-date",
            "not-a-date",
            "--db",
            str(db_path),
        ],
    )
    assert bad_grievance.exit_code != 0

    serve_help = runner.invoke(app, ["serve", "--help"])
    assert serve_help.exit_code == 0
    assert "--allow-grievance-persist" in serve_help.output
    assert runner.invoke(app, ["mcp", "--help"]).exit_code == 0
