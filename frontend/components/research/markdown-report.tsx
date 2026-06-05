"use client";

import ReactMarkdown from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import remarkGfm from "remark-gfm";
import { Copy } from "lucide-react";
import { Button } from "@/components/ui/button";

export function MarkdownReport({ markdown }: { markdown: string }) {
  return (
    <div className="prose prose-slate max-w-none dark:prose-invert">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          pre({ children }) {
            const text = String(children).replace(/\n$/, "");
            return (
              <div className="relative">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="absolute right-2 top-2 bg-background/80"
                  onClick={() => navigator.clipboard.writeText(text)}
                  aria-label="Copy code"
                >
                  <Copy className="h-4 w-4" />
                </Button>
                <pre>{children}</pre>
              </div>
            );
          }
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
