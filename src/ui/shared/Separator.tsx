import * as React from "react";

type SeparatorProps = React.ComponentProps<"div"> & {
  decorative?: boolean;
};

function Separator({ decorative = true, ...props }: SeparatorProps) {
  return (
    <div
      role={decorative ? "presentation" : "separator"}
      data-slot="separator"
      className={"bg-border shrink-0 h-px w-full"}
      {...props}
    />
  );
}

export { Separator };
export type { SeparatorProps };
