import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// Organised with the Diátaxis framework: https://diataxis.fr
const sidebars: SidebarsConfig = {
  docs: [
    'intro',
    {
      type: 'category',
      label: 'Tutorials',
      description: 'Learning-oriented lessons. Follow them from start to finish.',
      collapsed: false,
      link: {type: 'generated-index', slug: '/tutorials'},
      items: ['tutorials/first-mcp-server', 'tutorials/connect-claude-desktop'],
    },
    {
      type: 'category',
      label: 'How-to guides',
      description: 'Task-oriented recipes for people who already know the basics.',
      collapsed: false,
      link: {type: 'generated-index', slug: '/how-to'},
      items: [
        'how-to/add-a-tool',
        'how-to/python-client',
        'how-to/configure-hosts',
        'how-to/debug-with-inspector',
      ],
    },
    {
      type: 'category',
      label: 'Reference',
      description: 'Exact, complete facts about the server. Look things up here.',
      collapsed: false,
      link: {type: 'generated-index', slug: '/reference'},
      items: [
        'reference/tools',
        'reference/resources-and-prompts',
        'reference/configuration',
        'reference/json-rpc-examples',
      ],
    },
    {
      type: 'category',
      label: 'Explanation',
      description: 'Background and design decisions: the why behind the server.',
      collapsed: false,
      link: {type: 'generated-index', slug: '/explanation'},
      items: [
        'explanation/how-mcp-works',
        'explanation/architecture',
        'explanation/security-model',
        'explanation/hint-pedagogy',
      ],
    },
    'troubleshooting',
    'why-i-built-this',
  ],
};

export default sidebars;
