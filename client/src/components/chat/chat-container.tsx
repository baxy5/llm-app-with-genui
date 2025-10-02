"use client";
import { useChat } from "@/contexts/chat-context";
import { useSidebar } from "@/contexts/sidebar-context";
import { IChatMessagesResponse } from "@/schemas/api-responses";
import { ECBasicOption } from "echarts/types/dist/shared";
import { MenuIcon, SidebarIcon } from "lucide-react";
import { useEffect } from "react";
import { Conversation, ConversationContent } from "../ai-elements/conversation";
import { Message, MessageContent } from "../ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputToolbar,
  PromptInputTools,
} from "../ai-elements/prompt-input";
import { Response } from "../ai-elements/response";
import ChartContainer from "../artifacts/chart-container";
import { Button } from "../ui/button";

const ChatContainer = ({
  mess,
  slug,
}: {
  mess?: IChatMessagesResponse[];
  slug?: string;
}) => {
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
              <Message
                key={i}
                from={message.type as "user" | "assistant" | "system"}
              >
                <MessageContent>
                  {(() => {
                    switch (message.type) {
                      case "assistant":
                        return message.option ? (
                          <>
                            <Response>{message.content}</Response>
                            <ChartContainer
                              option={message.option as ECBasicOption}
                            />
                          </>
                        ) : (
                          <Response>{message.content}</Response>
                        );
                      case "user":
                        return <p>{message.content}</p>;
                    }
                  })()}
                </MessageContent>
              </Message>
            ))}
          </ConversationContent>
        </Conversation>

        {/* Input Area */}
        <div className="p-4 border-t border-border bg-background">
          <PromptInput onSubmit={handleSubmit}>
            <PromptInputBody className="">
              <PromptInputTextarea
                onChange={(e) => setCurrentMessage(e.target.value)}
                placeholder="Type your message..."
                className="resize-none"
                value={currentMessage}
              />
              <PromptInputToolbar className="p-2">
                <PromptInputTools></PromptInputTools>
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
