from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_PYTHON = Path(r"C:\Users\Admin\miniconda3\envs\vmec-clinical-copilot\python.exe")


def bench_python() -> str:
    configured = os.getenv("BENCH_PYTHON")
    if configured:
        return configured
    if DEFAULT_ENV_PYTHON.exists():
        return str(DEFAULT_ENV_PYTHON)
    return sys.executable


def parse_summary(output: str) -> dict[str, str]:
    summary = {}
    for key in ("Strategy", "Embedding", "Vector store", "Chroma dir", "Chroma collection", "Chunks loaded", "Doc hit@3", "Evidence hit@3", "Chunk-level score"):
        matches = re.findall(rf"^{re.escape(key)}:\s*(.+)$", output, re.MULTILINE)
        if matches:
            summary[key] = matches[-1].strip()
    return summary


class DemoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        if self.path == "/api/health":
            self._json({"ok": True})
            return
        super().do_GET()

    def do_POST(self):
        if self.path == "/api/strategy-sweep":
            self._run_strategy_sweep()
            return
        if self.path != "/api/benchmark":
            self.send_error(404)
            return

        self._run_benchmark({"CHUNKER": "heading", "CHROMA_DIR": ".chroma\\shopee_heading_700"})

    def _run_strategy_sweep(self):
        strategies = ["heading", "recursive", "fixed", "sentence"]
        runs = []
        for strategy in strategies:
            payload = self._run_benchmark_payload(
                {
                    "CHUNKER": strategy,
                    "CHROMA_DIR": f".chroma\\sweep_{strategy}",
                    "CHROMA_COLLECTION": f"lab7_sweep_{strategy}",
                },
                timeout=240,
            )
            runs.append({"strategy": strategy, **payload})
            if not payload["ok"]:
                break
        self._json({"ok": all(run["ok"] for run in runs), "runs": runs})

    def _run_benchmark(self, overrides: dict[str, str]):
        self._json(self._run_benchmark_payload(overrides))

    def _run_benchmark_payload(self, overrides: dict[str, str], timeout: int = 240) -> dict:
        env = os.environ.copy()
        env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "EMBEDDING_PROVIDER": "local",
                "VECTOR_STORE": "chroma",
                "CHUNK_SIZE": "700",
                "HF_HUB_OFFLINE": env.get("HF_HUB_OFFLINE", "1"),
                "TRANSFORMERS_OFFLINE": env.get("TRANSFORMERS_OFFLINE", "1"),
            }
        )
        env.update(overrides)

        try:
            result = subprocess.run(
                [bench_python(), "bench.py"],
                cwd=ROOT,
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return {"ok": False, "output": exc.stdout or "", "error": f"bench.py timed out after {timeout}s"}

        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "python": bench_python(),
            "summary": parse_summary(result.stdout),
            "output": result.stdout,
            "error": result.stderr,
        }

    def _json(self, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), DemoHandler)
    print(f"Demo UI with live benchmark: http://127.0.0.1:{port}")
    server.serve_forever()
