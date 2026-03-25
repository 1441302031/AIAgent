# aiagent

`aiagent` is a minimal, library-first Python agent project with a thin command-line interface for one-shot prompts and an interactive REPL.

## Install and run

This repository uses a `src` layout. For a fresh checkout, use one of these supported approaches:

Install the project in editable mode, then run the console command:

```bash
python -m pip install -e .
aiagent "hello"
aiagent --repl
```

Or run directly from the checkout by setting `PYTHONPATH=src`:

```bash
PYTHONPATH=src python -m aiagent "hello"
PYTHONPATH=src python -m aiagent --repl
```

## Usage

Run a single prompt:

```bash
aiagent "hello"
```

Start the interactive REPL:

```bash
aiagent --repl
```

Exit the REPL with `quit`, `exit`, `Ctrl+C`, or `Ctrl+D` / EOF.

## Tests

Run the full test suite with:

```bash
python -B -m pytest -p no:cacheprovider -v
```

## Configuration

Set configuration through environment variables:

- `AIAGENT_PROVIDER`
- `AIAGENT_API_KEY`
- `AIAGENT_API_BASE`
- `AIAGENT_MODEL`

Optional variables used by the mock and runtime configuration include `AIAGENT_TEMPERATURE`, `AIAGENT_MOCK_MODE`, and `AIAGENT_MOCK_RESPONSE`.
