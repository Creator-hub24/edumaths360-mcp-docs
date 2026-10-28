import type {ReactNode} from 'react';
import CodeBlock from '@theme/CodeBlock';
import Heading from '@theme/Heading';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';
import payloads from '@site/../snippets/example_payloads.json';

type Exchange = {
  title: string;
  request: Record<string, unknown>;
  response: Record<string, unknown> | null;
};

/** The equivalent call with the MCP Python SDK client, keyed by JSON-RPC method. */
function pythonFor(request: Record<string, any>): string | null {
  const params = request.params ?? {};
  switch (request.method) {
    case 'initialize':
      return '# The SDK client performs the handshake for you:\nasync with Client(server) as client:\n    print(client.server_info, client.protocol_version)';
    case 'notifications/initialized':
      return '# Sent automatically by the SDK client after initialize.';
    case 'tools/list':
      return 'tools = await client.list_tools()';
    case 'tools/call':
      return `result = await client.call_tool(\n    "${params.name}",\n    ${JSON.stringify(params.arguments)},\n)\nprint(result.is_error, result.structured_content)`;
    case 'resources/list':
      return 'resources = await client.list_resources()';
    case 'resources/templates/list':
      return 'templates = await client.list_resource_templates()';
    case 'resources/read':
      return `result = await client.read_resource("${params.uri}")\nprint(result.contents[0].text)`;
    case 'prompts/list':
      return 'prompts = await client.list_prompts()';
    case 'prompts/get':
      return `prompt = await client.get_prompt("${params.name}", ${JSON.stringify(params.arguments)})`;
    default:
      return null;
  }
}

function slug(title: string): string {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export default function JsonRpcExchanges(): ReactNode {
  const exchanges = (payloads as {exchanges: Exchange[]}).exchanges;
  return (
    <>
      {exchanges.map((ex) => {
        const python = pythonFor(ex.request as Record<string, any>);
        return (
          <section key={ex.title}>
            <Heading as="h3" id={slug(ex.title)}>
              {ex.title}
            </Heading>
            <Tabs groupId="rpc-language">
              <TabItem value="json" label="JSON-RPC" default>
                <CodeBlock language="json" title="Request (client → server)">
                  {JSON.stringify(ex.request, null, 2)}
                </CodeBlock>
                {ex.response === null ? (
                  <p>
                    <em>Notifications have no <code>id</code> and get no response.</em>
                  </p>
                ) : (
                  <CodeBlock language="json" title="Response (server → client)">
                    {JSON.stringify(ex.response, null, 2)}
                  </CodeBlock>
                )}
              </TabItem>
              {python && (
                <TabItem value="python" label="Python SDK">
                  <CodeBlock language="python">{python}</CodeBlock>
                </TabItem>
              )}
            </Tabs>
          </section>
        );
      })}
    </>
  );
}
