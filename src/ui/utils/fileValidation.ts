export function validateJsonFile(files: File[]): File | string {
  if (files.length !== 1) {
    return "Please upload exactly one file.";
  }
  const [file] = files;
  // File size is in bytes
  if (file.size > 10_000_000) return "Please upload a file smaller than 10 MB.";
  if (!file.name.endsWith(".json")) {
    return "Please upload only JSON files (.json)";
  }
  return file;
}

// Deprecated: kept for backward compatibility
export const validateExcelFile = validateJsonFile;
