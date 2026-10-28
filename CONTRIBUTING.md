# 🤝 Contributing

Thank you for helping. This project treats documentation as code: docs changes go through the same pull request, review and CI process as code changes.

## 🧭 Ways to help

| You want to… | Do this |
| --- | --- |
| Report a mistake in the docs | [Open an issue](https://github.com/Creator-hub24/edumaths360-mcp-docs/issues) with the page link and what is wrong. |
| Report an error you hit | Open an issue with the **full** error message. Real errors are added to the Troubleshooting page. |
| Fix a typo or unclear sentence | Use the **Edit this page** link at the bottom of any docs page. |
| Add a topic, tool or page | Open an issue first so we can agree on the approach. |

## 🛠️ Set up

You need Python 3.10+, [uv](https://docs.astral.sh/uv/) and Node.js 22.

```bash
git clone https://github.com/Creator-hub24/edumaths360-mcp-docs.git
cd edumaths360-mcp-docs

# Server and tests
cd server && uv sync --extra dev && uv run pytest -q && cd ..

# Docs site
cd docs-site && npm ci && npm start
```

The site opens at `http://localhost:3000/edumaths360-mcp-docs/` and reloads as you edit.

## ✅ Before you open a pull request

Run the same checks as CI:

```bash
# From the repository root
uvx ruff check . && uvx ruff format --check .
(cd server && uv run pytest -q)
(cd docs-site && npm run typecheck && npm run build)
vale docs-site/docs        # optional locally; non-blocking in CI
```

`npm run build` fails on any broken link or anchor. That is on purpose.

## 📏 Rules for docs changes

1. **Code in the docs must be real.** Put runnable code in `snippets/` and import it into the page with `raw-loader` (see `docs-site/docs/how-to/add-a-tool.mdx`). Add a test in `server/tests/test_snippets.py`.
2. **Outputs must be real.** Paste output from an actual run. If you change server behaviour, update the outputs and run `python snippets/capture_payloads.py` to refresh the JSON-RPC examples.
3. **Put the page in the right Diátaxis section.** Tutorials teach, how-to guides solve a task, reference describes, explanation discusses. If a page does two of these, split it.
4. **Follow the [style guide](STYLE_GUIDE.md).**
5. **Do not guess about other products.** If you are not sure how a host's interface looks, say so in the text.

## 🔀 Pull request process

1. Create a branch: `git checkout -b docs/short-description`.
2. Make small, focused commits with clear messages, for example `docs: explain hint levels in tools reference`.
3. Open a pull request. CI runs the tests, the docs build and Vale.
4. After review and merge to `main`, the site deploys to GitHub Pages automatically.

## 📜 License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
