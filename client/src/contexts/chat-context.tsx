"use client";

import { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { deleteChatSessionById, getChatSessions } from "@/lib/data";
import {
  IChatMessagesResponse,
  IChatSessionsResponse,
} from "@/schemas/api-responses";
import { IThinkingType } from "@/schemas/chat-types";
import {
  Brain,
  CircleCheckBig,
  NotebookPen,
  SearchIcon,
  TextSearch,
} from "lucide-react";
import {
  createContext,
  Dispatch,
  ReactNode,
  SetStateAction,
  useContext,
  useEffect,
  useState,
} from "react";

interface ChatContextType {
  // State
  messages: IChatMessagesResponse[];
  currentMessage: string;
  cot: IThinkingType[];
  sessionId: string;
  isLoading: boolean;
  chatSessions: IChatSessionsResponse[];

  // Setters
  setMessages: Dispatch<SetStateAction<IChatMessagesResponse[]>>;
  setCurrentMessage: Dispatch<SetStateAction<string>>;
  setCot: Dispatch<SetStateAction<IThinkingType[]>>;
  setSessionId: Dispatch<SetStateAction<string>>;
  setIsLoading: Dispatch<SetStateAction<boolean>>;
  setChatSessions: Dispatch<SetStateAction<IChatSessionsResponse[]>>;

  // Actions
  handleSubmit: (
    message: PromptInputMessage,
    event: React.FormEvent<HTMLFormElement>
  ) => Promise<void>;
  fetchChatSessions: () => Promise<void>;
  deleteChatSession: (sessionId: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = (): ChatContextType => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
  defaultSessionId?: string;
}

export const ChatProvider = ({ children }: ChatProviderProps) => {
  const [messages, setMessages] = useState<IChatMessagesResponse[]>([]);
  const [currentMessage, setCurrentMessage] = useState<string>("");
  const [cot, setCot] = useState<IThinkingType[]>([]);
  const [sessionId, setSessionId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [chatSessions, setChatSessions] = useState<IChatSessionsResponse[]>([]);

  const fetchChatSessions = async () => {
    try {
      const data: IChatSessionsResponse[] = await getChatSessions();
      const sorted = [...data].sort(
        (a, b) => Number(b.session_id) - Number(a.session_id)
      );

      setChatSessions(sorted);
    } catch (error) {
      console.error("Error fetching chat sessions:", error);
    }
  };

  const deleteChatSession = async (sessionId: string): Promise<void> => {
    try {
      await deleteChatSessionById(sessionId);
      const filteredChatSessions = chatSessions.filter(
        (session) => session.session_id.toString() !== sessionId
      );
      setChatSessions(filteredChatSessions);
    } catch (err) {
      console.error("Error while deleting chat session: ", err);
    }
  };

  useEffect(() => {
    fetchChatSessions();
  }, [sessionId]);

  const handleSubmit = async (
    message: PromptInputMessage,
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();
    if (currentMessage.trim()) {
      const newMessageId =
        messages.length > 0
          ? Math.max(...messages.map((msg) => msg.id)) + 1
          : 1;

      setMessages((prev) => [
        ...prev,
        {
          id: newMessageId,
          type: "user",
          content: currentMessage || "",
        },
      ]);

      const userInput = currentMessage;
      setCurrentMessage("");
      setCot([]);

      try {
        setIsLoading(true);
        const aiResponseId = newMessageId + 1;

        setMessages((prev) => [
          ...prev,
          { id: aiResponseId, type: "assistant", content: "" },
        ]);

        const url = `http://localhost:8000/agent/`;
        const payload = {
          input: userInput,
          session_id: sessionId,
        };
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        if (!response.body) {
          console.error("No response body!");
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let streamedContent = "";
        const iconMap = {
          text_search: TextSearch,
          search: SearchIcon,
          notebook: NotebookPen,
          check: CircleCheckBig,
          brain: Brain,
        };

        while (true) {
          const { done, value } = await reader.read();

          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const events = buffer.split("\n\n");

          buffer = events.pop() ?? "";

          for (const rawEvent of events) {
            if (!rawEvent.startsWith("data:")) continue;

            const jsonString = rawEvent.replace(/^data:\s*/, "");
            try {
              const parsed = JSON.parse(jsonString);
              if (parsed.type === "content") {
                // Handle text content
                if (parsed.content) {
                  streamedContent += parsed.content;
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiResponseId
                        ? {
                            ...msg,
                            type: "assistant",
                            content: streamedContent,
                          }
                        : msg
                    )
                  );
                }

                // Handle chart option data
                if (parsed.option) {
                  setMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === aiResponseId
                        ? {
                            ...msg,
                            type: "assistant",
                            content: "",
                            option: parsed.option,
                          }
                        : msg
                    )
                  );
                }
              } else {
                setCot((prev) => [
                  ...prev,
                  {
                    content: parsed.content,
                    search_query: parsed.search_query
                      ? parsed.search_query
                      : "",
                    icon:
                      iconMap[parsed.icon as keyof typeof iconMap] ||
                      NotebookPen,
                  },
                ]);
              }
            } catch (err) {
              console.error("Failed to parse SSE event:", jsonString, err);
            }
          }
        }
      } catch (err) {
        console.error("Error parsing event data:", err);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const value: ChatContextType = {
    // State
    messages,
    currentMessage,
    cot,
    sessionId,
    isLoading,
    chatSessions,

    // Setters
    setMessages,
    setCurrentMessage,
    setCot,
    setSessionId,
    setIsLoading,
    setChatSessions,

    // Actions
    handleSubmit,
    fetchChatSessions,
    deleteChatSession,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
