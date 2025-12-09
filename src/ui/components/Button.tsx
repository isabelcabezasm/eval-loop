import "./Button.css";

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "primary" | "secondary";
  nativeType?: "button" | "submit" | "reset";
  disabled?: boolean;
}

export function Button({
  children,
  onClick,
  type = "primary",
  nativeType = "button",
  disabled = false
}: ButtonProps) {
  return (
    <button
      type={nativeType}
      onClick={onClick}
      disabled={disabled}
      className={`custom-button ${type}`}
    >
      {children}
    </button>
  );
}
