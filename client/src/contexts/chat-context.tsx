"use client";

import { PromptInputMessage } from "@/components/ai-elements/prompt-input";
import { deleteChatSessionById, getChatSessions } from "@/lib/data";
import { createFormDataWithFiles, streamParser } from "@/lib/utils";
import {
  IChatMessagesResponse,
  IChatSessionsResponse,
} from "@/schemas/api-responses";
import { IThinkingType } from "@/schemas/chat-types";
import {
  Blocks,
  Brain,
  ChartBar,
  ChartLine,
  CircleCheckBig,
  Hammer,
  NotebookPen,
  Pencil,
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
        let response: Response;

        if (message.files && message.files.length > 0) {
          const formData = await createFormDataWithFiles(
            userInput,
            sessionId,
            message
          );

          response = await fetch(url, {
            method: "POST",
            body: formData,
          });
        } else {
          const payload = {
            input: userInput,
            session_id: sessionId,
          };

          response = await fetch(url, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
          });
        }

        if (!response.body) {
          console.error("No response body!");
          return;
        }

        let streamedContent = "";
        const iconMap = {
          text_search: TextSearch,
          search: SearchIcon,
          notebook: NotebookPen,
          check: CircleCheckBig,
          brain: Brain,
          pencil: Pencil,
          line_chart: ChartLine,
          bar_chart: ChartBar,
          hammer: Hammer,
          blocks: Blocks,
        };

        await streamParser(response, (parsed: any) => {
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
                        option: parsed.option,
                      }
                    : msg
                )
              );
            }

            // Handle component data
            if (parsed.component) {
              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.id === aiResponseId) {
                    const existingComponents = msg.component || [];
                    let hasChanges = false;
                    let mergedComponents = existingComponents;

                    parsed.component.forEach((newComp: any) => {
                      if (
                        newComp.type === "ui_event" &&
                        newComp.target &&
                        newComp.component
                      ) {
                        const existingIndex = existingComponents.findIndex(
                          (existing: any) =>
                            existing.type === "ui_event" &&
                            existing.target === newComp.target
                        );

                        if (existingIndex >= 0) {
                          if (
                            JSON.stringify(
                              existingComponents[existingIndex].component
                            ) !== JSON.stringify(newComp.component)
                          ) {
                            if (!hasChanges) {
                              mergedComponents = [...existingComponents];
                              hasChanges = true;
                            }
                            mergedComponents[existingIndex] = newComp;
                          }
                        } else {
                          if (!hasChanges) {
                            mergedComponents = [...existingComponents];
                            hasChanges = true;
                          }
                          mergedComponents.push(newComp);
                        }
                      } else {
                        if (!hasChanges) {
                          mergedComponents = [...existingComponents];
                          hasChanges = true;
                        }
                        mergedComponents.push(newComp);
                      }
                    });

                    if (hasChanges) {
                      return { ...msg, component: mergedComponents };
                    }
                    return msg;
                  }
                  return msg;
                })
              );
            }
          } else {
            setCot((prev) => [
              ...prev,
              {
                content: parsed.content,
                search_query: parsed.search_query ? parsed.search_query : "",
                icon:
                  iconMap[parsed.icon as keyof typeof iconMap] || NotebookPen,
              },
            ]);
          }
        });
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
