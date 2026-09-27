/**
 * Stands in for ReactMarkdownCustom under jest, where the markdown stack (ESM
 * only) does not load. The text is drawn as handed over, with the options as
 * attributes, so a spec can read what the renderer was asked for; what it
 * draws from that is the Cypress journeys' to check. The one thing drawn is a
 * `[text](href)` where a renderLink is given: through it, as the real renderer
 * offers it every link out of the document, or as the plain anchor it
 * declines.
 */

import type { ComponentProps, ReactNode } from 'react';
import type ReactMarkdownCustom from '../ReactMarkdownCustom';

type Props = ComponentProps<typeof ReactMarkdownCustom>;

// An inline link; an image, which starts the same way after a `!`, is not one.
const LINK = /(?<!!)\[([^\]]*)\]\(([^)]*)\)/g;

function drawLinks(markdown: string, renderLink: NonNullable<Props['renderLink']>) {
  const parts: ReactNode[] = [];
  let last = 0;
  for (const match of markdown.matchAll(LINK)) {
    const [whole, text, href] = match;
    const start = match.index ?? 0;
    parts.push(markdown.slice(last, start));
    parts.push(
      <span key={start}>
        {renderLink(href, text) ?? <a href={href}>{text}</a>}
      </span>
    );
    last = start + whole.length;
  }
  parts.push(markdown.slice(last));
  return parts;
}

export default function ReactMarkdownCustomStub({
  markdown,
  allowHtml = false,
  allowImages = true,
  breaks = false,
  direction,
  className,
  renderLink,
}: Props) {
  return (
    <div
      data-testid="markdown"
      className={className}
      data-allow-html={allowHtml}
      data-allow-images={allowImages}
      data-breaks={breaks}
      data-direction={direction}
    >
      {renderLink ? drawLinks(markdown, renderLink) : markdown}
    </div>
  );
}
