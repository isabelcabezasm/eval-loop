import { useRef, useState } from "react";

import { Button } from "@/components/Button";
import { ContentBlock } from "@/components/ContentBlock";
import { ExcelFileUpload } from "@/components/ExcelFileUpload";
import { InputText } from "@/components/InputText";
import { Overlay } from "@/components/Overlay";
import { TextArea } from "@/components/TextArea";
import "@/styles/App.css";
import "@/styles/App.css";
import { Citation, TextChunk, useApi } from "@/utils/api";

const assistant = "assistant";
const user = "user";
type ChatMessage = {
  role: "user" | "assistant";
  content?: string; // Raw text content for API
  chunks?: (TextChunk | Citation)[]; // Chunks for display (only for assistant messages)
};
function App() {
  const [context, setContext] = useState<string>("");
  const [isContextLocked, setIsContextLocked] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState<string>("");
  const [streamingBot, setStreamingBot] = useState<boolean>(false);
  const [showCitationOverlay, setShowCitationOverlay] = useState<boolean>(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [citations, setCitations] = useState<Record<string, Citation>>({});
  const [debugConstitution, setDebugConstitution] = useState<File | undefined>(undefined);
  const [realityFile, setRealityFile] = useState<File | undefined>(undefined);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const apiClient = useApi();
  const addUserMessage = (text: string) => {
    setMessages((msgs: ChatMessage[]) => [...msgs, { role: user, content: text }]);
  };
  const handleShowCitation = (citationId: string) => {
    setSelectedCitation(citations[citationId]);
    setShowCitationOverlay(true);
  };
  const handleCloseCitationOverlay = () => {
    setShowCitationOverlay(false);
    setSelectedCitation(null);
  };
  const streamAnswer = async (question: string) => {
    setStreamingBot(true);
    // Convert ChatMessage[] to Message[] for API (raw content only)
    const response = apiClient.answer(
      question,
      context,
      messages.map((msg) => ({
        role: msg.role,
        content: msg.content ?? ""
      })),
      debugConstitution,
      realityFile
    );
    // Add a new response message
    setMessages((msgs: ChatMessage[]) => [
      ...msgs,
      { role: assistant, content: undefined, chunks: [] }
    ]);
    for await (const chunk of response) {
      let content = "";
      if (chunk.type === "text") {
        content = chunk.text;
      }
      if (chunk.type === "citation") {
        content = `[${chunk.id}]`;
        // Add to citations store and update chunks
        setCitations((prev) => ({
          ...prev,
          [chunk.id]: chunk
        }));
      }
      setMessages((msgs: ChatMessage[]) => {
        const answerMessage = msgs.at(-1);
        if (!answerMessage) throw new Error("No answer message");
        return [
          ...msgs.slice(0, -1),
          {
            ...answerMessage,
            content: answerMessage.content + content,
            chunks: [...(answerMessage.chunks || []), chunk]
          }
        ];
      });
    }
    setStreamingBot(false);
  };
  const handleSend = async () => {
    if (!input.trim() || streamingBot || !isContextLocked) return;
    addUserMessage(input);
    setInput("");
    await streamAnswer(input);
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  const handleStartChat = () => {
    if (context.trim()) {
      setIsContextLocked(true);
    }
  };
  const handleClearAndRestart = () => {
    setMessages([]);
    setCitations({});
    setIsContextLocked(false);
    setInput("");
  };
  return (
    <div className="app-container">
      {/* Context Setup Step */}
      <ContentBlock boxed cssModule={{ container: "setup-section" }}>
        <div className="section-header">
          <h2>Context</h2>
          {debugConstitution && <span className="debug-indicator">Debug Constitution is used</span>}
          {isContextLocked && (
            <Button type="secondary" onClick={handleClearAndRestart}>
              Clear & Restart
            </Button>
          )}
        </div>
        {!isContextLocked ? (
          <div>
            <TextArea
              label="Set the context for this conversation:"
              // value={context}
              value="Banking and financial markets are sensitive to political conditions and governance stability."
              onChange={(e) => setContext(e.target.value)}
              placeholder="Describe the context or scenario for this chat..."
              height="120px"
              width="100%"
            />
            <div className="reality-upload-section">
              <ExcelFileUpload
                label="Reality File"
                file={realityFile}
                onFileUpdate={setRealityFile}
              />
            </div>
            <details className="debug-section">
              <summary className="debug-summary">Advanced: Debug Constitution</summary>
              <div className="debug-content">
                <p className="debug-help-text">
                  Upload a debug constitution instead of the default one. This is for testing
                  purposes only and will override the default constitution.
                </p>
                <ExcelFileUpload
                  label="Debug Constitution"
                  file={debugConstitution}
                  onFileUpdate={setDebugConstitution}
                />
              </div>
            </details>
            <div className="form-actions">
              <Button onClick={handleStartChat} disabled={!context.trim()} type="primary">
                Start Chat →
              </Button>
            </div>
          </div>
        ) : (
          <ContentBlock boxed>
            <div className="context-display">{context}</div>
          </ContentBlock>
        )}
      </ContentBlock>
      {/* Chat Step */}
      {isContextLocked && (
        <ContentBlock boxed cssModule={{ container: "chat-section" }}>
          <div className="section-header">
            <h2>Chat</h2>
          </div>
          <div className="chat-container">
            <div className="messages-area">
              {messages.length === 0 ? (
                <div className="empty-state">Ask your first question to start the conversation</div>
              ) : (
                messages.map((msg: ChatMessage, idx: number) => (
                  <div key={idx} className={`message ${msg.role}`}>
                    <div className={`message-bubble ${msg.role}`}>
                      {msg.chunks
                        ? msg.chunks.map((chunk, chunkIdx) =>
                          chunk.type === "text" ? (
                            chunk.text
                          ) : (
                            <a
                              key={chunkIdx}
                              onClick={() => handleShowCitation(chunk.id)}
                              className="citation-link"
                            >
                              [{chunk.id}]
                            </a>
                          )
                        )
                        : msg.content}
                    </div>
                  </div>
                ))
              )}
              <div ref={chatEndRef} />
            </div>
            <form
              className="input-form"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              <div className="input-wrapper">
                <InputText
                  // value={input}
                  value="How does political instability affect investor confidence in financial markets?"
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type your question..."
                  disabled={streamingBot}
                  width="100%"
                />
              </div>
              <Button type="primary" nativeType="submit" disabled={!input.trim() || streamingBot}>
                Send
              </Button>
            </form>
          </div>
        </ContentBlock>
      )}
      {/* Citation Overlay */}
      <Overlay
        id="citation-overlay"
        closeLabel="Close"
        onClose={handleCloseCitationOverlay}
        onCloseButtonClick={handleCloseCitationOverlay}
        open={showCitationOverlay}
        modal
        lightDismiss={true}
        hasCloseButton
      >
        <Overlay.Header>{selectedCitation && <h3>{selectedCitation.id}</h3>}</Overlay.Header>
        <Overlay.Body>
          {selectedCitation && (
            <div>
              <div className="citation-section">
                <h4>Subject</h4>
                <p>{selectedCitation.subject}</p>
              </div>
              <div className="citation-section">
                <h4>Object</h4>
                <p>{selectedCitation.object}</p>
              </div>
              <div className="citation-section">
                <h4>Link</h4>
                <p>{selectedCitation.link}</p>
              </div>
              <div className="citation-section">
                <h4>Conditions</h4>
                <p>{selectedCitation.conditions}</p>
              </div>
              <div className="citation-section">
                <h4>Description</h4>
                <p>{selectedCitation.description}</p>
              </div>
              <div className="citation-section">
                <h4>Amendments</h4>
                <p>{selectedCitation.amendments}</p>
              </div>
            </div>
          )}
        </Overlay.Body>
      </Overlay>
    </div>
  );
}
export default App;
