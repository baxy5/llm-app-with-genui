"use client";
import { useChat } from "@/contexts/chat-context";
import { useSidebar } from "@/contexts/sidebar-context";
import { IChatMessagesResponse } from "@/schemas/api-responses";
import { ECBasicOption } from "echarts/types/dist/shared";
import { MenuIcon, SidebarIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Conversation, ConversationContent } from "../ai-elements/conversation";
import { Message, MessageContent } from "../ai-elements/message";
import {
  PromptInput,
  PromptInputActionAddAttachments,
  PromptInputActionMenu,
  PromptInputActionMenuContent,
  PromptInputActionMenuTrigger,
  PromptInputAttachment,
  PromptInputAttachments,
  PromptInputBody,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from "../ai-elements/prompt-input";
import { Response } from "../ai-elements/response";
import ChartContainer from "../artifacts/chart-container";
import DynamicRenderer from "../artifacts/DynamicRenderer";
import { Button } from "../ui/button";

const ChatContainer = ({
  mess,
  slug,
}: {
  mess?: IChatMessagesResponse[];
  slug?: string;
}) => {
  const [mounted, setMounted] = useState(false);

  const {
    leftSidebarOpen,
    setLeftSidebarOpen,
    rightSidebarOpen,
    setRightSidebarOpen,
  } = useSidebar();

  const {
    messages,
    setMessages,
    currentMessage,
    setCurrentMessage,
    isLoading,
    handleSubmit,
    setSessionId,
  } = useChat();

  useEffect(() => {
    if (mess) {
      setMessages(mess);
    }
  }, [mess, setMessages]);

  useEffect(() => {
    if (slug !== undefined) {
      setSessionId(slug);
    }
  }, [setSessionId, slug]);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="flex-1 flex flex-col min-w-0">
      {/* Header with sidebar toggles */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-background">
        <div className="flex items-center gap-2">
          <Button
            className="cursor-pointer"
            variant="ghost"
            size="sm"
            aria-label="Toggle chat sessions panel"
            onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
          >
            <MenuIcon className="h-4 w-4" />
            <span className="sr-only">Toggle chat sessions panel</span>
          </Button>
          <h1 className="text-xl font-semibold">AI Chat</h1>
        </div>

        <Button
          className="cursor-pointer"
          variant="ghost"
          size="sm"
          aria-label="Toggle settings panel"
          onClick={() => setRightSidebarOpen(!rightSidebarOpen)}
        >
          <SidebarIcon className="h-4 w-4" />
          <span className="sr-only">Toggle settings panel</span>
        </Button>
      </div>

      {/* Chat Interface */}
      <div className="flex-1 flex flex-col min-h-0">
        <Conversation className="flex-1 min-h-0">
          <ConversationContent className="space-y-6">
            {messages.map((message, i) => (
              <Message key={i} from={message.type as "user" | "assistant"}>
                <MessageContent>
                  {isLoading &&
                    message.type === "assistant" &&
                    !message.content &&
                    !message.component &&
                    !message.option && (
                      <div
                        className="flex items-center gap-1"
                        aria-live="polite"
                        aria-busy="true"
                      >
                        <span className="animate-bounce [animation-delay:0ms] h-2 w-2 rounded-full bg-[#0a0a0a]" />
                        <span className="animate-bounce [animation-delay:200ms] h-2 w-2 rounded-full bg-[#0a0a0a]" />
                        <span className="animate-bounce [animation-delay:400ms] h-2 w-2 rounded-full bg-[#0a0a0a]" />
                        <span className="sr-only">Assistant is typing...</span>
                      </div>
                    )}
                  {(() => {
                    if (message.type === "assistant") {
                      if (message.component) {
                        const components = Array.isArray(message.component)
                          ? message.component
                          : [message.component];
                        return (
                          <>
                            {components.map((ui, i) => (
                              <DynamicRenderer
                                key={i}
                                descriptor={ui.component}
                              />
                            ))}
                          </>
                        );
                      }
                      if (message.option) {
                        return (
                          <>
                            <Response>{message.content}</Response>
                            <ChartContainer
                              option={message.option as ECBasicOption}
                            />
                          </>
                        );
                      }
                      return <Response>{message.content}</Response>;
                    }
                    if (message.type === "user") {
                      return <p>{message.content}</p>;
                    }
                    return null;
                  })()}
                </MessageContent>
              </Message>
            ))}
          </ConversationContent>
        </Conversation>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-background">
          <PromptInput onSubmit={handleSubmit}>
            <PromptInputBody>
              <PromptInputAttachments>
                {(attachment) => <PromptInputAttachment data={attachment} />}
              </PromptInputAttachments>
              <PromptInputTextarea
                onChange={(e) => setCurrentMessage(e.target.value)}
                placeholder="Type your message..."
                className="resize-none"
                value={currentMessage}
              />
              <PromptInputToolbar className="p-2">
                <PromptInputTools>
                  {mounted && (
                    <>
                      <PromptInputActionMenu>
                        <PromptInputActionMenuTrigger className="cursor-pointer" />
                        <PromptInputActionMenuContent>
                          <PromptInputActionAddAttachments className="cursor-pointer" />
                        </PromptInputActionMenuContent>
                      </PromptInputActionMenu>
                    </>
                  )}
                </PromptInputTools>
                <PromptInputSubmit
                  className="cursor-pointer"
                  aria-label="Send message"
                  status={isLoading ? "submitted" : "ready"}
                />
              </PromptInputToolbar>
            </PromptInputBody>
          </PromptInput>
        </div>
      </div>
    </div>
  );
};

export default ChatContainer;
