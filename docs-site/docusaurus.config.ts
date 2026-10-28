import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const REPO = 'https://github.com/Creator-hub24/edumaths360-mcp-docs';

const config: Config = {
  title: 'Edumaths360 MCP Docs',
  tagline:
    'Developer documentation for an MCP server that lets AI assistants run maths practice without doing the thinking for the student.',
  favicon: 'img/favicon.svg',

  future: {
    v4: true,
  },

  url: 'https://creator-hub24.github.io',
  baseUrl: '/edumaths360-mcp-docs/',
  organizationName: 'Creator-hub24',
  projectName: 'edumaths360-mcp-docs',
  trailingSlash: false,

  // Docs-as-code: a broken link fails the build (and CI).
  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',

  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
      onBrokenMarkdownImages: 'throw',
    },
  },
  themes: ['@docusaurus/theme-mermaid'],

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: `${REPO}/tree/main/docs-site/`,
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/social-card.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'Edumaths360 MCP',
      logo: {
        alt: 'Edumaths360 MCP logo',
        src: 'img/logo.svg',
      },
      items: [
        {type: 'doc', docId: 'intro', position: 'left', label: 'Docs'},
        {type: 'doc', docId: 'tutorials/first-mcp-server', position: 'left', label: 'Tutorials'},
        {type: 'doc', docId: 'how-to/add-a-tool', position: 'left', label: 'How-to guides'},
        {type: 'doc', docId: 'reference/tools', position: 'left', label: 'Reference'},
        {type: 'doc', docId: 'explanation/how-mcp-works', position: 'left', label: 'Explanation'},
        {href: REPO, label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Learn',
          items: [
            {label: 'Introduction', to: '/docs/intro'},
            {label: 'Your first MCP server', to: '/docs/tutorials/first-mcp-server'},
            {label: 'Connect to Claude Desktop', to: '/docs/tutorials/connect-claude-desktop'},
          ],
        },
        {
          title: 'Reference',
          items: [
            {label: 'Tools', to: '/docs/reference/tools'},
            {label: 'JSON-RPC examples', to: '/docs/reference/json-rpc-examples'},
            {label: 'Troubleshooting', to: '/docs/troubleshooting'},
          ],
        },
        {
          title: 'Project',
          items: [
            {label: 'GitHub repository', href: REPO},
            {label: 'Why I built this', to: '/docs/why-i-built-this'},
            {label: 'Model Context Protocol', href: 'https://modelcontextprotocol.io'},
          ],
        },
      ],
      copyright: `© ${new Date().getFullYear()} Vaibhav Gupta · Edumaths360. Docs built with Docusaurus. Code under the MIT licence.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'python', 'powershell'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
