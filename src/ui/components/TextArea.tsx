import "./TextArea.css";

interface TextAreaProps {
  label?: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  height?: string;
  width?: string;
}

export function TextArea({ label, value, onChange, placeholder, height, width }: TextAreaProps) {
  return (
    <div className="textarea-wrapper">
      {label && <label className="textarea-label">{label}</label>}
      <textarea
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="custom-textarea"
        style={{ height, width }}
      />
    </div>
  );
}
