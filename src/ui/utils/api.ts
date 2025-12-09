import * as z from "zod";

const ApiTextChunk = z.object({
  type: z.literal("text"),
  text: z.string()
});
const ApiAxiomCitationChunk = z.object({
  type: z.literal("axiom_citation"),
  id: z.string(),
  description: z.string()
});
const ApiRealityCitationChunk = z.object({
  type: z.literal("reality_citation"),
  id: z.string(),
  description: z.string()
});

const ApiChunk = z.discriminatedUnion("type", [
  ApiTextChunk,
  ApiAxiomCitationChunk,
  ApiRealityCitationChunk
]);
type ApiChunkType = z.infer<typeof ApiChunk>;
export type TextChunk = z.infer<typeof ApiTextChunk>;
export type Citation = z.infer<typeof ApiAxiomCitationChunk | typeof ApiRealityCitationChunk>;
export interface Message {
  role: "user" | "assistant";
  content: string;
}
interface AnswerRequest {
  context: string;
  question: string;
  history: Message[];
  reality: string | null; // Base64 encoded Excel file
  debugConstitution: string | null; // Base64 encoded Excel file
}
export function useApi(): ApiClient {
  const apiBaseUrl = import.meta.env.API_BASE_URL || "http://127.0.0.1:8080/api/";
  return new ApiClient(new URL(apiBaseUrl));
}
export async function* parseChunks(stream: ReadableStream<string>): AsyncGenerator<ApiChunkType> {
  function* parse(lines: Iterable<string>) {
    for (const line of lines) {
      if (!line.trim()) continue;
      try {
        yield ApiChunk.parse(JSON.parse(line));
      } catch (err) {
        if (err instanceof z.ZodError) {
          throw new ApiError("Received an unexpected response from the API.", { cause: err });
        }
        throw err;
      }
    }
  }
  const reader = stream.getReader();
  let buffer = "";
  while (true) {
    // If done is true, chunk must be undefined and to process it safely we use the empty string as default.
    // https://streams.spec.whatwg.org/#default-reader-prototype
    const { value: chunk = "", done: done } = await reader.read();
    buffer += chunk;
    const lines = buffer.split(/[\r\n]+/g);
    // The empty string ("") is split as a list of one empty string ([""]), hence we can always pop something.
    buffer = lines.pop()!;
    yield* parse(lines);
    if (done) break;
  }
  // Parse the remainder
  yield* parse([buffer]);
}
export class HttpError extends Error {
  status: number;
  body: string | null;
  constructor(status: number, body: string | null) {
    super(`HTTP ${status}`);
    this.status = status;
    this.body = body;
  }
}
export class ApiError extends Error { }
async function readFileAsBase64(file: File): Promise<string> {
  // Note the FileReader API does not exist in node, hence we can't unit test this function.
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      // Remove the data URL prefix to get just the base64 data
      const [, base64Data] = result.split(",");
      resolve(base64Data);
    };
    reader.onerror = () => {
      reject(new Error("Failed to read file"));
    };
    reader.readAsDataURL(file);
  });
}
export class ApiClient {
  private baseUrl: URL;
  constructor(baseUrl: URL) {
    this.baseUrl = baseUrl;
  }
  public async *answer(
    question: string,
    reality: string,
    history: Message[],
    debugConstitution?: File,
    realityFile?: File
  ): AsyncGenerator<TextChunk | Citation> {
    const base64EncodedConstitution = debugConstitution
      ? await readFileAsBase64(debugConstitution)
      : null;
    const base64EncodedReality = realityFile ? await readFileAsBase64(realityFile) : null;
    const request: AnswerRequest = {
      context: reality,
      question,
      history,
      reality: base64EncodedReality,
      debugConstitution: base64EncodedConstitution
    };
    const response = await fetch(new URL("generate", this.baseUrl), {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(request)
    });
    if (!response.ok) {
      throw new HttpError(response.status, await response.text());
    }
    if (!response.body) {
      throw new ApiError("No response body received from API.");
    }
    yield* parseChunks(response.body.pipeThrough(new TextDecoderStream()));
  }
}
