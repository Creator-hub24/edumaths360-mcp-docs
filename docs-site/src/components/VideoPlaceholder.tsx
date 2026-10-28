import type {ReactNode} from 'react';
import Admonition from '@theme/Admonition';

/**
 * Placeholder for the walkthrough video (under 3 minutes).
 * Replace this component with the real embed once the video is recorded.
 * No link is shown until a real video exists.
 */
export default function VideoPlaceholder(): ReactNode {
  return (
    <Admonition type="info" title="Video walkthrough: coming soon">
      <p>
        A short walkthrough video (under 3 minutes) will appear here. It will show the server
        running in Claude Desktop: generating a problem, giving a hint, and marking an answer.
      </p>
      <p>
        <em>Placeholder: the video has not been recorded yet, so there is no link.</em>
      </p>
    </Admonition>
  );
}
