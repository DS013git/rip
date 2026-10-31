# RIP.git

Build a spooky graveyard of a GitHub user's abandoned repositories. RIP.git uses Python for repository facts and an open-weight Gemma model through Ollama for short, fact-grounded epitaphs. The generated site is a self-contained static page suitable for GitHub Pages.

## What it is

Give RIP.git a GitHub username and it fetches owned, non-fork, non-empty repositories, sorts them by the time since their last push, and labels them alive (0–30 days), dying (31–90 days), or dead (more than 90 days). Each tombstone shows repository details, a cause of death, and gentle and savage epitaphs. A haunting section whispers to up to three dying repositories.

Try the bundled fictional data with `--sample`; this mode works offline and does not need a GitHub token or Ollama to produce a page. When Ollama is unavailable, RIP.git uses deterministic fallback text so the page can still be built.

## Demo

Live demo: [GitHub Pages demo](https://your-username.github.io/rip-git/) (replace this placeholder after publishing).

## How it works

- **Facts come from Python.** RIP.git reads repository name, description, language, stars, open issues, last push date, and the first line of the latest commit message from GitHub's REST API. Status labels and day counts are computed locally.
- **Jokes come from Gemma.** One Ollama chat call per repository asks for gentle and savage epitaphs plus a short cause of death. A separate call creates whispers for up to three dying repositories. Prompts provide only repository facts and forbid invented details and personal insults. Invalid output is retried once; Ollama failures use deterministic fallback text.
- **The result is static.** `docs/index.html` includes its CSS and JavaScript inline. It makes no network calls when opened and uses no external fonts or CDN assets.

## Quick start for PowerShell

Requirements: Python 3.10 or later, Git, and [Ollama](https://ollama.com/download) for model-generated text. The sample build can run without Ollama.

```powershell
cd C:\path\to\rip-git
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` in a text editor and set `GITHUB_TOKEN` to a GitHub token if you plan to fetch real repositories. A token is optional, but GitHub's unauthenticated API has a lower rate limit. Do not paste the token into commands or commit `.env`.

Install and start Ollama using its Windows installer. In PowerShell, download the configured model once:

```powershell
ollama pull gemma4:cloud
```

Ollama normally runs as a background service at `http://localhost:11434`. If needed, start it in another PowerShell window with `ollama serve`. Then build and open the offline demo:

```powershell
python -m ripgit.cli build --sample
Start-Process .\docs\index.html
```

Build a real user's graveyard (replace the example username):

```powershell
python -m ripgit.cli build octocat
```

The real build fetches up to 30 repositories by default, narrates them, and writes `docs/index.html`. The output summary reports how many repositories used Gemma and fallback text. Ollama request timing and approximate token counts are appended to the ignored local `trace.jsonl` file; it does not contain the GitHub token.

## Configuration

Set values in the local `.env` file:

| Variable | Default | Purpose |
| --- | --- | --- |
| `GITHUB_TOKEN` | empty | Optional token for GitHub API requests; read only from `.env`. |
| `OLLAMA_HOST` | `http://localhost:11434` | Base URL of the Ollama HTTP service. |
| `OLLAMA_MODEL` | `gemma4:cloud` | Ollama model used for epitaphs and whispers. |

The model can also be overridden for a single build with `--model NAME`. The repository count can be changed with `--limit N`.

## Project structure

```text
rip-git/
  ripgit/                 Python fetch, narration, site builder, and CLI
    templates/            Jinja2 page template
  data/                   Fictional offline sample repositories
  docs/                   Generated GitHub Pages site
  tests/                  Unit tests
  .env.example            Configuration template (copy to local .env)
  requirements.txt        Runtime and test dependencies
```

## Why open-source AI matters here

RIP.git uses an open-weight model through Ollama, and you can switch models by changing `OLLAMA_MODEL`. With a locally available model, narration can run on your machine without vendor lock-in or per-call API fees. The sample mode also demonstrates the whole site-building flow offline. `gemma4:cloud` is the configured default; choose a locally runnable Ollama model if you want model inference to stay entirely on your computer.

## Publish with GitHub Pages

1. Push this repository to GitHub. Keep `.env` local; it is ignored by Git.
2. In the repository, open **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, select the branch containing the generated page (usually `main`) and the `/docs` folder, then save.
4. Wait for GitHub Pages to publish the site. The demo URL should be `https://YOUR-USERNAME.github.io/rip-git/` for a repository named `rip-git`.
5. To attach a custom domain, enter it in the **Custom domain** field on that Pages settings screen and save. Configure the DNS records GitHub Pages requests for your domain, then wait for DNS verification. Add a `CNAME` file in `docs/` containing the domain if you manage the site source directly; keep it in place on later builds.

Regenerate the committed page after changing its data or design:

```powershell
python -m ripgit.cli build --sample
git add docs/index.html
git commit -m "Refresh graveyard demo"
git push
```

## Checks

Run the test suite from the project root:

```powershell
python -m pytest
```

## Contest deadline follow-up

Any commits after the contest deadline are listed here:

-
