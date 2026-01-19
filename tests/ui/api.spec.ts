import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClient, ApiError, Citation, HttpError, TextChunk, parseChunks } from "@/utils/api";

const TEST_SESSION_ID = "test-session-123";

type Chunk = TextChunk | Citation;
async function accumulate<T>(generator: AsyncGenerator<T>): Promise<T[]> {
  const result: T[] = [];
  for await (const value of generator) {
    result.push(value); // Accumulate each value into the results array
  }
  return result;
}
function readableStream(chunks: Iterable<string>): ReadableStream<string> {
  // @ts-expect-error ReadableStream.from was added with Node 18+
  return ReadableStream.from(chunks);
}
function apiClient(url: URL | null = null) {
  return new ApiClient(url ?? new URL("http://localhost:8000/api/"));
}
describe("parse_chunks", () => {
  it.each([
    { raw_chunks: [], expected: [] },
    { raw_chunks: [""], expected: [] },
    { raw_chunks: ["\n"], expected: [] },
    { raw_chunks: ["\n", " ", "  "], expected: [] },
    // preserves whitespace
    {
      raw_chunks: ['{"type":"text","text":" foo "}'],
      expected: [{ type: "text" as const, text: " foo " }]
    },
    {
      raw_chunks: ['{"type":"text","text":"foo"}\n', '{"type":"text","text":"bar"}'],
      expected: [
        { type: "text" as const, text: "foo" },
        { type: "text" as const, text: "bar" }
      ]
    },
    // single chunk
    {
      raw_chunks: [
        '{"type":"text","text":"foo"}\n{"type":"text","text":"bar"}\n{"type":"text","text":"baz"}\n'
      ],
      expected: [
        { type: "text" as const, text: "foo" },
        { type: "text" as const, text: "bar" },
        { type: "text" as const, text: "baz" }
      ]
    },
    // carriage-return style newline
    {
      raw_chunks: ['{"type":"text","text":"foo"}', "\r\n", '{"type":"text","text":"bar"}'],
      expected: [
        { type: "text" as const, text: "foo" },
        { type: "text" as const, text: "bar" }
      ]
    },
    // multiple newlines
    {
      raw_chunks: [
        '{"type":"text","text":"foo"}',
        "\n",
        "\n",
        '{"type":"text","text":"bar"}',
        "\n\n"
      ],
      expected: [
        { type: "text" as const, text: "foo" },
        { type: "text" as const, text: "bar" }
      ]
    },
    // chunks without newline
    {
      raw_chunks: ['{"type":"text","text":', '"foo"}'],
      expected: [{ type: "text" as const, text: "foo" }]
    }
  ])(
    "should parse chunks correctly",
    async ({ raw_chunks, expected }: { raw_chunks: string[]; expected: Chunk[] }) => {
      // arrange
      const stream = readableStream(raw_chunks);
      // act
      const result = await accumulate(parseChunks(stream));
      // assert
      expect(result).toEqual(expected);
    }
  );
});
describe("ApiClient", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });
  it("should call the fetch API correctly", async () => {
    // arrange
    const body = readableStream(['{"type":"text","text":"foo"}']).pipeThrough(
      new TextEncoderStream()
    );
    const fetch = vi.fn<typeof fetch>(() =>
      Promise.resolve(
        new Response(body, {
          status: 200,
          headers: {
            "Content-Type": "application/x-ndjson"
          }
        })
      )
    );
    vi.stubGlobal("fetch", fetch);
    const subject = apiClient(new URL("http://localhost:8000/api/"));
    // act
    const result = await accumulate(
      subject.answer("some question", "some reality", TEST_SESSION_ID)
    );
    // assert
    expect(result).toEqual([{ type: "text", text: "foo" }]);
    const [[actualUrl, { method: actualMethod, body: actualBody, headers: actualHeaders }]] =
      fetch.mock.calls;
    expect(actualUrl).toEqual(new URL("http://localhost:8000/api/generate"));
    expect(actualMethod).toEqual("POST");
    expect(JSON.parse(actualBody)).toEqual({
      context: "some reality",
      question: "some question",
      reality: null,
      debugConstitution: null,
      session_id: TEST_SESSION_ID
    });
    expect(actualHeaders).toEqual({ "Content-Type": "application/json" });
  });
  it("should raise an error if unsuccessful", async () => {
    // arrange
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(() =>
        Promise.resolve({ status: 400, text: () => Promise.resolve("some error") } as Response)
      )
    );
    const subject = apiClient();
    // act + assert
    await expect(accumulate(subject.answer("", "", TEST_SESSION_ID))).rejects.toThrowError(
      new HttpError(400, "some error")
    );
  });
  it("should raise an error if no body is present", async () => {
    // arrange
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(() => Promise.resolve(new Response(null, { status: 200 })))
    );
    const subject = apiClient();
    // act + assert
    await expect(accumulate(subject.answer("", "", TEST_SESSION_ID))).rejects.toThrowError(
      new ApiError("No response body received from API.")
    );
  });
  it("should raise an error if the API returns an unexpected object", async () => {
    // arrange
    const body = readableStream(['{"content":"foo"}']).pipeThrough(new TextEncoderStream());
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(() => Promise.resolve(new Response(body, { status: 200 })))
    );
    const subject = apiClient();
    // act + assert
    await expect(accumulate(subject.answer("", "", TEST_SESSION_ID))).rejects.toThrowError(
      new ApiError("Received an unexpected response from the API.")
    );
  });

  it("should call restart with session_id in request body", async () => {
    // arrange
    const fetch = vi.fn<typeof fetch>(() =>
      Promise.resolve(
        new Response(JSON.stringify({ status: "ok" }), {
          status: 200,
          headers: { "Content-Type": "application/json" }
        })
      )
    );
    vi.stubGlobal("fetch", fetch);
    const subject = apiClient(new URL("http://localhost:8000/api/"));
    // act
    await subject.restart(TEST_SESSION_ID);
    // assert
    const [[actualUrl, { method: actualMethod, body: actualBody, headers: actualHeaders }]] =
      fetch.mock.calls;
    expect(actualUrl).toEqual(new URL("http://localhost:8000/api/restart"));
    expect(actualMethod).toEqual("POST");
    expect(JSON.parse(actualBody)).toEqual({ session_id: TEST_SESSION_ID });
    expect(actualHeaders).toEqual({ "Content-Type": "application/json" });
  });

  it("should throw HttpError when restart fails", async () => {
    // arrange
    vi.stubGlobal(
      "fetch",
      vi.fn<typeof fetch>(() =>
        Promise.resolve({ status: 500, text: () => Promise.resolve("server error"), ok: false } as Response)
      )
    );
    const subject = apiClient();
    // act + assert
    await expect(subject.restart(TEST_SESSION_ID)).rejects.toThrowError(new HttpError(500, "server error"));
  });
});
