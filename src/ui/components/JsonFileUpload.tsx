import { FileUpload } from "@/components/FileUpload";
import { error } from "@/utils/error";
import { validateJsonFile } from "@/utils/fileValidation";

interface JsonFileUploadProps {
  label: string;
  helpText?: string;
  file: File | undefined;
  onFileUpdate: (file: File | undefined) => void;
  compact?: boolean;
}
export function JsonFileUpload({
  label,
  helpText = "Drag and drop file here, or {{browse}}",
  file,
  onFileUpdate,
  compact = true
}: JsonFileUploadProps) {
  const handleFileSelect = (files: File[]) => {
    const result = validateJsonFile(files);
    if (typeof result === "string") {
      error(result);
      return;
    }
    onFileUpdate(result);
  };
  return (
    <>
      {!file ? (
        <FileUpload
          label={label}
          helpText={helpText}
          onSelect={handleFileSelect}
          accept=".json"
          compact={compact}
        />
      ) : (
        <FileUpload.FileList onRemove={() => onFileUpdate(undefined)}>
          <FileUpload.FileList.Item name={file.name} size={file.size} />
        </FileUpload.FileList>
      )}
    </>
  );
}
