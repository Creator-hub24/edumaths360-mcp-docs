# ✍️ Style guide

These rules keep the docs clear for every reader, including people who read English as a second language and people who are new to MCP. Vale checks some of them automatically (see `.vale.ini`).

## 🎯 Principles

<!-- vale off -->

| Principle | In practice |
| --- | --- |
| **Plain English** | Short sentences. One idea per sentence. Common words over clever ones. |
| **Explain jargon** | Define a term the first time it appears on a page, for example "a *transport* (how messages travel between client and server)". |
| **Be accurate** | Every code sample is tested, every output is real, and anything unverified is labelled as such. |
| **Respect the reader** | No "simply", "just", "obviously" or "easy". What is easy for you may not be for them. |
| **Be direct** | Use "you" for the reader and the imperative for steps: "Run the tests", not "The tests should be run". |

<!-- vale on -->

## 🗂️ Page types (Diátaxis)

| Type | Purpose | Voice | Example |
| --- | --- | --- | --- |
| Tutorial | Learning by doing | "We will build…", guided, one path | *Build your first MCP server* |
| How-to guide | Solve one task | Steps, assumes basic knowledge | *Add a new tool* |
| Reference | Look something up | Neutral, complete, tables | *Tools* |
| Explanation | Understand why | Discussion, context, trade-offs | *Hint pedagogy* |

## 🔤 Words and spelling

<!-- vale off -->

- Use British English spelling (behaviour, recognise, practise as a verb), matching the Indian classroom audience.
- Use **Class 6–10** for grades in text. The API argument is still `grade`.
- Write **MCP**, not "MCP protocol" (the P already means protocol).
- Product names: **GitHub**, **JavaScript**, **TypeScript**, **JSON-RPC**, **Docusaurus**, **Claude Desktop**, **MCP Inspector**.
- Avoid Latin abbreviations: "for example" not "e.g.", "that is" not "i.e.".

<!-- vale on -->

## 🧱 Formatting

- **Headings:** sentence case ("Add a new tool", not "Add A New Tool"). Do not skip levels.
- **Code:** use backticks for anything a reader might type or see on screen: `generate_problem`, `server/`, `-32602`.
- **Code blocks:** always set the language (`python`, `json`, `bash`). Give long blocks a `title`.
- **Multiple languages or platforms:** use tabs (Python / JSON, macOS / Windows / Linux) with a shared `groupId`, so the reader's choice is remembered.
- **Admonitions:** `:::tip` for helpful extras, `:::caution` for things that can go wrong, `:::info` for context. Use them sparingly.
- **Diagrams:** use Mermaid in a fenced `mermaid` block so diagrams live in Git and are reviewed like text.
- **Links:** link to files with relative paths and the file extension (`../reference/tools.md#errors`). The build checks them.

## 🚫 Honesty rules

- Do not invent numbers, results or user counts.
- Do not show output you did not get from a real run.
- When describing another product's interface that you could not verify, say so: "the exact label may differ".
- Placeholders (such as the video) must be labelled as placeholders and must not contain fake links.
