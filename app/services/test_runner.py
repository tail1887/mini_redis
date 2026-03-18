from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any


PHASE_FILE_PREFIXES: dict[str, tuple[str, ...]] = {
    "phase0": ("test_health.py",),
    "phase1": (
        "test_kv_templates.py",
        "test_kv_del_exists.py",
        "test_key_namespace.py",
        "test_kv_service_unit.py",
        "test_error_responses.py",
    ),
    "phase2": (
        "test_kv_expire_part1.py",
        "test_ttl.py",
        "test_ttl_failure_cleanup.py",
        "test_kv_persist_part3.py",
        "test_kv_ttl_scaffold.py",
        "test_ttl_time_boundary_templates.py",
    ),
    "phase3": (
        "test_kv_invalidate_part1.py",
        "test_invalidate_prefix_safeguards.py",
        "test_cache_metrics.py",
        "test_kv_invalidate_metrics_scaffold.py",
        "test_invalidate_failure_templates.py",
    ),
    "phase4": (
        "test_deploy_health_check.py",
        "test_deploy_recovery_templates.py",
        "test_system_readiness.py",
        "test_regression_suite.py",
    ),
}


def _build_empty_phase_summary() -> dict[str, dict[str, int]]:
    return {
        phase: {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        for phase in PHASE_FILE_PREFIXES.keys()
    }


class DashboardTestRunner:
    def __init__(self, report_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self._started_at: float | None = None
        self._finished_at: float | None = None
        self._last_command: list[str] = []
        self._last_exit_code: int | None = None
        self._last_output: str = ""
        self._last_error: str | None = None
        self._last_report: dict[str, Any] | None = None
        self._last_summary: dict[str, int] = {}
        self._last_phase_summary: dict[str, dict[str, int]] = _build_empty_phase_summary()
        self._report_path = report_path or Path("artifacts") / "pytest-report.json"

    def start(self) -> bool:
        with self._lock:
            if self._running:
                return False

            self._running = True
            self._started_at = time.time()
            self._finished_at = None
            self._last_error = None
            self._last_exit_code = None
            self._last_output = ""
            self._last_report = None
            self._last_summary = {}
            self._last_phase_summary = _build_empty_phase_summary()

            command = [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--json-report",
                f"--json-report-file={self._report_path.as_posix()}",
            ]
            self._last_command = command
            self._thread = threading.Thread(target=self._run_tests, args=(command,), daemon=True)
            self._thread.start()
            return True

    def status(self) -> dict[str, Any]:
        with self._lock:
            phase_summary = {
                phase: dict(values)
                for phase, values in self._last_phase_summary.items()
            }
            return {
                "running": self._running,
                "startedAt": self._started_at,
                "finishedAt": self._finished_at,
                "lastExitCode": self._last_exit_code,
                "lastCommand": self._last_command,
                "lastError": self._last_error,
                "summary": dict(self._last_summary),
                "phaseSummary": phase_summary,
                "reportPath": str(self._report_path),
                "lastOutputTail": self._last_output[-2000:],
            }

    def _run_tests(self, command: list[str]) -> None:
        self._report_path.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(  # noqa: S603
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        output = (process.stdout or "") + ("\n" + process.stderr if process.stderr else "")

        report: dict[str, Any] | None = None
        summary: dict[str, int] = {}
        phase_summary = _build_empty_phase_summary()

        if self._report_path.exists():
            try:
                report = json.loads(self._report_path.read_text(encoding="utf-8"))
                summary = self._extract_summary(report)
                phase_summary = self._extract_phase_summary(report)
            except Exception as exc:  # pragma: no cover
                with self._lock:
                    self._last_error = f"failed to parse json report: {exc}"

        with self._lock:
            self._running = False
            self._finished_at = time.time()
            self._last_exit_code = process.returncode
            self._last_output = output
            self._last_report = report
            self._last_summary = summary
            self._last_phase_summary = phase_summary
            if process.returncode != 0 and not self._last_error:
                self._last_error = "pytest exited with non-zero code"

    @staticmethod
    def _extract_summary(report: dict[str, Any]) -> dict[str, int]:
        raw_summary = report.get("summary", {})
        return {
            "total": int(raw_summary.get("total", 0)),
            "passed": int(raw_summary.get("passed", 0)),
            "failed": int(raw_summary.get("failed", 0)),
            "skipped": int(raw_summary.get("skipped", 0)),
            "errors": int(raw_summary.get("error", 0) or raw_summary.get("errors", 0)),
        }

    @staticmethod
    def _extract_phase_summary(report: dict[str, Any]) -> dict[str, dict[str, int]]:
        phase_summary = _build_empty_phase_summary()
        tests = report.get("tests", [])
        if not isinstance(tests, list):
            return phase_summary

        for test in tests:
            if not isinstance(test, dict):
                continue
            nodeid = str(test.get("nodeid", ""))
            outcome = str(test.get("outcome", ""))
            phase = DashboardTestRunner._phase_for_nodeid(nodeid)
            if phase is None:
                continue

            phase_summary[phase]["total"] += 1
            if outcome == "passed":
                phase_summary[phase]["passed"] += 1
            elif outcome == "failed":
                phase_summary[phase]["failed"] += 1
            elif outcome == "skipped":
                phase_summary[phase]["skipped"] += 1

        return phase_summary

    @staticmethod
    def _phase_for_nodeid(nodeid: str) -> str | None:
        for phase, file_names in PHASE_FILE_PREFIXES.items():
            for file_name in file_names:
                if file_name in nodeid:
                    return phase
        return None


test_runner = DashboardTestRunner()
