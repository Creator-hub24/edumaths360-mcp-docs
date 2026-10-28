import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import CodeBlock from '@theme/CodeBlock';

import styles from './index.module.css';

type Card = {title: string; kind: string; to: string; description: string};

const CARDS: Card[] = [
  {
    kind: 'Tutorial',
    title: 'Build your first MCP server',
    to: '/docs/tutorials/first-mcp-server',
    description: 'Learn by doing: a times-table server in about 30 lines of Python, tested in the MCP Inspector.',
  },
  {
    kind: 'How-to guide',
    title: 'Add a tool',
    to: '/docs/how-to/add-a-tool',
    description: 'Extend the server with a worksheet tool: schema, annotations, errors and a test.',
  },
  {
    kind: 'Reference',
    title: 'Tools, resources and prompts',
    to: '/docs/reference/tools',
    description: 'Every argument, limit, output field and error message, taken from the real server.',
  },
  {
    kind: 'Explanation',
    title: 'Why hints come in levels',
    to: '/docs/explanation/hint-pedagogy',
    description: 'How classroom teaching shaped the design: graduated hints and feedback that names the mistake.',
  },
];

const CONFIG = `{
  "mcpServers": {
    "edumaths360": {
      "command": "uv",
      "args": ["--directory", "/path/to/edumaths360-mcp-docs/server",
               "run", "edumaths360-mcp"]
    }
  }
}`;

export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title="Home" description={siteConfig.tagline}>
      <header className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>Edumaths360 · Docs as Code</p>
          <Heading as="h1" className={styles.title}>
            Give AI assistants the tools of a good maths tutor
          </Heading>
          <p className={styles.subtitle}>
            An open-source <strong>Model Context Protocol</strong> server that generates Class 6–10 practice
            problems, checks answers and gives graduated hints, without handing over the answer. Documented
            end to end, with the code examples tested in CI.
          </p>
          <div className={styles.buttons}>
            <Link className="button button--primary button--lg" to="/docs/intro">
              Get started
            </Link>
            <Link className="button button--secondary button--outline button--lg" to="/docs/tutorials/first-mcp-server">
              Build your first server
            </Link>
          </div>
        </div>
      </header>
      <main>
        <section className="container margin-vert--xl">
          <Heading as="h2" className="text--center">
            Find what you need
          </Heading>
          <p className="text--center margin-bottom--lg">
            The docs follow the <a href="https://diataxis.fr/">Diátaxis</a> framework: four kinds of page for four
            different needs.
          </p>
          <div className="row">
            {CARDS.map((card) => (
              <div key={card.to} className="col col--3 margin-bottom--lg">
                <Link to={card.to} className={styles.card}>
                  <span className={styles.kind}>{card.kind}</span>
                  <Heading as="h3">{card.title}</Heading>
                  <p>{card.description}</p>
                </Link>
              </div>
            ))}
          </div>
        </section>
        <section className={styles.band}>
          <div className="container">
            <div className="row">
              <div className="col col--5">
                <Heading as="h2">Connect it in one step</Heading>
                <p>
                  Add the server to Claude Desktop, Cursor or any MCP host. No API keys, no database and no
                  network access: it runs locally over stdio.
                </p>
                <ul>
                  <li>
                    <strong>3 tools:</strong> <code>generate_problem</code>, <code>check_answer</code>,{' '}
                    <code>get_hint</code>
                  </li>
                  <li>
                    <strong>2 resources:</strong> the syllabus, overall and per class
                  </li>
                  <li>
                    <strong>1 prompt:</strong> a Socratic tutor that asks before it tells
                  </li>
                </ul>
                <Link to="/docs/how-to/configure-hosts">Configure your host →</Link>
              </div>
              <div className="col col--7">
                <CodeBlock language="json" title="claude_desktop_config.json">
                  {CONFIG}
                </CodeBlock>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
