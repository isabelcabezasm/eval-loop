function Separator({ decorative = true, ...props }) {
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
