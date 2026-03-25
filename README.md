# aiagent

`aiagent` is a minimal, library-first Python agent project with a thin command-line interface for one-shot prompts and an interactive REPL.

## Usage

Run a single prompt:

```bash
python -m aiagent "hello"
```

Start the interactive REPL:

```bash
python -m aiagent --repl
```

Exit the REPL with `quit` or `exit`.

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
