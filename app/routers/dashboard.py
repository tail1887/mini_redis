from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.schemas.common import SuccessResponse
from app.services.test_runner import test_runner

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> str:
    return """
<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Mini Redis Test Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 24px; background: #0f172a; color: #e2e8f0; }
      .row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
      .card { background: #111827; border: 1px solid #374151; border-radius: 10px; padding: 14px; min-width: 220px; }
      .title { font-size: 18px; margin-bottom: 8px; }
      button { padding: 8px 14px; border-radius: 8px; border: none; background: #2563eb; color: white; cursor: pointer; }
      button:disabled { background: #475569; cursor: not-allowed; }
      pre { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 10px; overflow: auto; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border-bottom: 1px solid #334155; padding: 8px; text-align: left; }
      .muted { color: #94a3b8; }
    </style>
  </head>
  <body>
    <h1>Mini Redis Test Dashboard</h1>
    <p class="muted">테스트 실행 버튼으로 pytest를 돌리고, 결과 JSON을 자동 파싱해 표시합니다.</p>
    <div class="row">
      <button id="runBtn" onclick="runTests()">테스트 실행</button>
      <span id="statusText" class="muted">상태 로딩 중...</span>
    </div>

    <div class="row">
      <div class="card"><div class="title">전체</div><div id="summaryAll">-</div></div>
      <div class="card"><div class="title">Phase 1</div><div id="phase1">-</div></div>
      <div class="card"><div class="title">Phase 2</div><div id="phase2">-</div></div>
      <div class="card"><div class="title">Phase 3</div><div id="phase3">-</div></div>
      <div class="card"><div class="title">Phase 4</div><div id="phase4">-</div></div>
    </div>

    <h3>실행 상세</h3>
    <table>
      <tr><th>startedAt</th><td id="startedAt">-</td></tr>
      <tr><th>finishedAt</th><td id="finishedAt">-</td></tr>
      <tr><th>exitCode</th><td id="exitCode">-</td></tr>
      <tr><th>error</th><td id="errorText">-</td></tr>
    </table>

    <h3>로그 (tail)</h3>
    <pre id="output"></pre>

    <script>
      function fmtPhase(v) {
        return `total=${v.total}, pass=${v.passed}, fail=${v.failed}, skip=${v.skipped}`;
      }

      function fmtTs(ts) {
        if (!ts) return "-";
        return new Date(ts * 1000).toLocaleString();
      }

      async function fetchStatus() {
        const resp = await fetch('/v1/dashboard/test-status');
        const payload = await resp.json();
        const d = payload.data;
        const sum = d.summary || {};
        const phases = d.phaseSummary || {};

        document.getElementById('statusText').innerText = d.running ? 'running...' : 'idle';
        document.getElementById('runBtn').disabled = d.running;
        document.getElementById('summaryAll').innerText =
          `total=${sum.total || 0}, pass=${sum.passed || 0}, fail=${sum.failed || 0}, skip=${sum.skipped || 0}, err=${sum.errors || 0}`;

        document.getElementById('phase1').innerText = phases.phase1 ? fmtPhase(phases.phase1) : '-';
        document.getElementById('phase2').innerText = phases.phase2 ? fmtPhase(phases.phase2) : '-';
        document.getElementById('phase3').innerText = phases.phase3 ? fmtPhase(phases.phase3) : '-';
        document.getElementById('phase4').innerText = phases.phase4 ? fmtPhase(phases.phase4) : '-';

        document.getElementById('startedAt').innerText = fmtTs(d.startedAt);
        document.getElementById('finishedAt').innerText = fmtTs(d.finishedAt);
        document.getElementById('exitCode').innerText = d.lastExitCode ?? '-';
        document.getElementById('errorText').innerText = d.lastError || '-';
        document.getElementById('output').innerText = d.lastOutputTail || '';
      }

      async function runTests() {
        await fetch('/v1/dashboard/run-tests', { method: 'POST' });
        await fetchStatus();
      }

      fetchStatus();
      setInterval(fetchStatus, 2000);
    </script>
  </body>
</html>
"""


@router.post("/v1/dashboard/run-tests", response_model=SuccessResponse)
def run_tests() -> SuccessResponse:
    started = test_runner.start()
    return SuccessResponse(
        data={
            "started": started,
            "message": "test run started" if started else "test run already in progress",
        }
    )


@router.get("/v1/dashboard/test-status", response_model=SuccessResponse)
def test_status() -> SuccessResponse:
    return SuccessResponse(data=test_runner.status())
