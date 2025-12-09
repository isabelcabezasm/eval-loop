import "./ContentBlock.css";

interface ContentBlockProps {
  children: React.ReactNode;
  boxed?: boolean;
  cssModule?: {
    container?: string;
  };
}

export function ContentBlock({ children, boxed = false, cssModule }: ContentBlockProps) {
  const className = `content-block ${boxed ? "boxed" : ""} ${cssModule?.container || ""}`.trim();
  return <div className={className}>{children}</div>;
}
