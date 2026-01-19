import { describe, expect, it, vi } from "vitest";

import { generateSessionId } from "@/utils/session";

describe("generateSessionId", () => {
    it("should return a string", () => {
        const sessionId = generateSessionId();
        expect(typeof sessionId).toBe("string");
    });

    it("should return a UUID v4 format", () => {
        const sessionId = generateSessionId();
        // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
        expect(sessionId).toMatch(uuidV4Regex);
    });

    it("should return unique values on each call", () => {
        const sessionId1 = generateSessionId();
        const sessionId2 = generateSessionId();
        const sessionId3 = generateSessionId();
        expect(sessionId1).not.toBe(sessionId2);
        expect(sessionId2).not.toBe(sessionId3);
        expect(sessionId1).not.toBe(sessionId3);
    });

    it("should call crypto.randomUUID()", () => {
        const mockUUID = "12345678-1234-4234-a234-123456789012";
        const spy = vi.spyOn(crypto, "randomUUID").mockReturnValue(mockUUID);

        const sessionId = generateSessionId();

        expect(spy).toHaveBeenCalled();
        expect(sessionId).toBe(mockUUID);

        spy.mockRestore();
    });
});
