# K4 RAG Demo UI

Static dashboard for the Lab 7 Shopee policy retrieval demo.

## Run UI

From the repo root:

```powershell
python -m http.server 8000 --directory demo_ui
```

Open:

```text
http://localhost:8000
```

This static mode shows the prepared benchmark story. To make the `Run real bench.py` button execute the real pipeline, use live mode instead:

```powershell
conda activate vmec-clinical-copilot
python demo_ui\server.py
```

Open:

```text
http://127.0.0.1:8000
```

## Run Real Benchmark

```powershell
cd D:\codein\misp@ce\aiaction\K4-Day07-Gehihi36
conda activate vmec-clinical-copilot

$env:PYTHONIOENCODING='utf-8'
$env:EMBEDDING_PROVIDER='local'
$env:VECTOR_STORE='chroma'
$env:CHROMA_DIR='.chroma\shopee_heading_700'
$env:CHUNKER='heading'
$env:CHUNK_SIZE='700'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'

python bench.py
```

## Demo Route

- 1 minute: scope, public sources, metadata schema.
- 2 minutes: HeadingAwareChunker strategy.
- 3 minutes: benchmark results, Q3 A/B metadata filter, Q4 failure case.
- 1-2 minutes: live query or prepared output from `bench.py`.

## Interactive Flow

Use the Overview screen first:

- Select a benchmark query in the pipeline console.
- Click `Run pipeline` to animate Load -> Chunk -> Embed -> Store -> Retrieve -> Evaluate.
- Click `Run all 5` to show the full fixed benchmark set in one batch.
- Use `Next step` if you want to explain each stage slowly during the demo.
- The Retrieve stage opens the matching query detail; the Evaluate stage shows doc/evidence rank, filter, and top-1 result.

## Current Benchmark Story

- Strategy: `HeadingAwareChunker(chunk_size=700)`
- Embedding: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Vector store: Chroma persistent
- Chunks loaded: `392`
- Doc hit@3: `5/5`
- Evidence hit@3: `4/5`
- Chunk-level score: `6/10`

Main insight: document-level retrieval looks perfect, but chunk-level evidence exposes the real failure in Q4.
