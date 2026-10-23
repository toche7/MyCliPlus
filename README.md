# MyCliPlus

A Python CLI conversion of the agent in `BasicHarness5_MyCLI_Plus.ipynb`.
The project separates the API client, agent loop, chat session, and tools into
modules. It uses the Groq chat-completions API and starts a terminal
conversation instead of an `ipywidgets` interface.

## Requirements

- Python 3.10 or newer
- A Groq API key

## Install

From this directory, create and activate a virtual environment, then install
the project:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

Configure the app in a `.env` file in the directory where you run it (it is
loaded automatically at startup and is git-ignored). Start from the template:

```bash
cp .env.example .env
```

then set `GROQ_API_KEY` in it. Variables already set in your shell take
precedence over `.env`, and blank values are ignored. Do not put a real key in
source files or `.env.example`.

Choose the agent kind with `MYCLI_MODE` in `.env`:

- `limited` (default): only non-privileged tools such as `calc`. No file
  tools and no `create_tool`, so the agent cannot add tools.
- `self_improve`: adds the file tools (`read_file`, `write_file`,
  `replace_in_file`), `run_command` (bash) and `create_tool`. The agent creates a complete tool with
  a single `create_tool` call (it supplies the function source), which is saved
  to `workspace/generated_tools/`, and
  `/reload` loads it. A generated module that fails to import is skipped and
  reported.

```
MYCLI_MODE=self_improve
```

Optionally choose which tools are available to the model. Set `MYCLI_TOOLS` to
a comma-separated list of tool names; unset it (or leave it empty) to enable
every tool the mode allows:

```
MYCLI_TOOLS=calc,read_file
```

Use `/tools` to see the active tools. Unknown names cause a configuration error
at startup. This setting also applies after `/reload`.

## Run

```bash
mycli-plus
```

Or, without installing the console command:

```bash
python -m mycli_plus
```

Enter `/tools` to list available tools, `/reload` to reload the bundled
Python tool modules, or `/quit` to exit. The agent creates `workspace/` in
the current directory and confines file operations and generated tool drafts
to that directory.

## Colors

In a terminal, your `You:` prompt is cyan, the agent's `Agent:` replies are
green, errors are red, and verbose activity is dim. Colors are disabled
automatically when output is piped, when `NO_COLOR` is set, or with
`MYCLI_COLOR=0`.

## Verbose mode

To watch what the agent does behind the scenes (each model call, the tool it
requests with its arguments, and the tool result), enable verbose output any of
these ways:

- `MYCLI_VERBOSE=1` in `.env`
- `mycli-plus --verbose` (or `-v`)
- type `/verbose` in the chat to toggle it on or off

Activity is printed to stderr and long values are truncated. Arguments and
results can include file contents, so avoid sharing verbose logs if they hold
sensitive data.

## Shell tool (`run_command`)

In `self_improve` mode the agent can run bash commands to build and test its
tools. Commands run with `./workspace` as the working directory, a timeout
(default 30s, max 300s), capped output, and an environment with variables
whose names contain `KEY`, `TOKEN`, `SECRET`, `PASSWORD` or `CREDENTIAL`
removed (so `GROQ_API_KEY` is not visible). It is not a sandbox: a command can
still use absolute paths, the network and anything your user can do. If you set
`MYCLI_TOOLS`, include `run_command` in the list to enable it. It is never
available in `limited` mode.

## Tools and safety

In `limited` mode the model gets no privileged tools. In `self_improve` mode,
the model can run shell commands (`run_command`) and write Python into `workspace/generated_tools/` and `/reload`
imports and runs it **with your user's full privileges** (the workspace
confinement applies only to the file tools, not to generated code). Use that
mode only with prompts and models you trust, and review generated files. In
`limited` mode nothing generated is ever loaded. The bundled-tool loader also
imports Python modules from this package, so only add code there that you
trust.

## Tests

Run the standard-library unit tests from this directory:

```bash
python -m unittest discover -s tests -v
```
