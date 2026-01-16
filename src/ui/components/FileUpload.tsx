import "./FileUpload.css";
import { useRef } from "react";

interface FileUploadProps {
  label: string;
  helpText?: string;
  onSelect: (files: File[]) => void;
  accept?: string;
  compact?: boolean;
}

interface FileListProps {
  children: React.ReactNode;
  onRemove: () => void;
}

interface FileListItemProps {
  name: string;
  size: number;
}

export function FileUpload({ label, helpText, onSelect, accept, compact = true }: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      onSelect(Array.from(files));
    }
  };

  const handleClick = () => {
    inputRef.current?.click();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files) {
      onSelect(Array.from(files));
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const formattedHelpText = helpText?.replace(
    "{{browse}}",
    '<span class="browse-link">browse</span>'
  );

  return (
    <div className={`file-upload ${compact ? "compact" : ""}`}>
      <label className="file-upload-label">{label}</label>
      <div
        className="file-upload-dropzone"
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleFileChange}
          style={{ display: "none" }}
        />
        <p
          dangerouslySetInnerHTML={{
            __html: formattedHelpText || "Drag and drop or click to browse"
          }}
        />
      </div>
    </div>
  );
}

const FileList = ({ children, onRemove }: FileListProps) => {
  return (
    <div className="file-list">
      {children}
      <button className="file-remove" onClick={onRemove}>
        Remove
      </button>
    </div>
  );
};

const FileListItem = ({ name, size }: FileListItemProps) => {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="file-list-item">
      <span className="file-name">{name}</span>
      <span className="file-size">{formatSize(size)}</span>
    </div>
  );
};

FileUpload.FileList = Object.assign(FileList, {
  Item: FileListItem
});
