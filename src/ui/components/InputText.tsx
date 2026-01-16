import "./InputText.css";

interface InputTextProps {
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  disabled?: boolean;
  width?: string;
}

export function InputText({
  value,
  onChange,
  placeholder,
  disabled = false,
  width
}: InputTextProps) {
  return (
    <input
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      className="custom-input"
      style={{ width }}
    />
  );
}
