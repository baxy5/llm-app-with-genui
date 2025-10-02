"use client";
import { useChat } from "@/contexts/chat-context";
import { useSidebar } from "@/contexts/sidebar-context";
import { cn } from "@/lib/utils";
import { CirclePlus, X, XIcon } from "lucide-react";
import Link from "next/link";
import { Button } from "./ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";

const LeftSideBar = () => {
  const { leftSidebarOpen, setLeftSidebarOpen } = useSidebar();
  const { chatSessions, sessionId, deleteChatSession } = useChat();
  return (
    <>
      <div
        className={cn(
          "relative border-r border-border bg-background transition-all duration-300 z-30",
          // Desktop behavior
          "hidden md:block",
          leftSidebarOpen ? "md:w-64" : "md:w-0 md:overflow-hidden",
          // Mobile behavior - overlay
          leftSidebarOpen &&
            "fixed inset-y-0 left-0 w-64 md:relative md:inset-auto"
        )}
      >
        <Collapsible open={leftSidebarOpen} onOpenChange={setLeftSidebarOpen}>
          <CollapsibleContent className="h-full">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Chat History</h2>
                <CollapsibleTrigger asChild>
                  <Button
                    className="cursor-pointer"
                    variant="ghost"
                    size="sm"
                    aria-label="Close chat sessions panel"
                  >
                    <XIcon className="h-4 w-4" />
                    <span className="sr-only">Close chat sessions panel</span>
                  </Button>
                </CollapsibleTrigger>
              </div>
              {/* Placeholder for chat sessions list */}
              <div className="grid gap-2">
                <Link href={`/`}>
                  <div className="flex items-center gap-2 p-2 font-bold rounded-lg bg-secondary/50 border border-border text-xs text-black hover:bg-secondary">
                    <CirclePlus size={16} />
                    Create new chat
                  </div>
                </Link>
                {chatSessions.length === 0 ? (
                  <div className="p-2 rounded-lg bg-muted text-muted-foreground text-xs animate-pulse border border-dashed border-border/50">
                    Loading chat sessions...
                  </div>
                ) : (
                  chatSessions.map((c) => (
                    <div
                      key={c.session_id}
                      className={`group flex items-center justify-between p-2 font-bold rounded-lg bg-secondary/50 border border-dashed border-border/50 text-xs hover:bg-secondary ${
                        c.session_id.toString() === sessionId
                          ? "text-black"
                          : "text-muted-foreground"
                      }`}
                    >
                      <Link href={`/c/${c.session_id}`}>
                        <p>{c.title}</p>
                      </Link>
                      <X
                        className="opacity-0 cursor-pointer group-hover:opacity-100"
                        size={16}
                        onClick={() =>
                          deleteChatSession(c.session_id.toString())
                        }
                      />
                    </div>
                  ))
                )}
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>
      </div>
    </>
  );
};

export default LeftSideBar;
