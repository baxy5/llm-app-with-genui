"use client";
import { useChat } from "@/contexts/chat-context";
import { useSidebar } from "@/contexts/sidebar-context";
import { cn } from "@/lib/utils";
import { XIcon } from "lucide-react";
import {
  ChainOfThought,
  ChainOfThoughtContent,
  ChainOfThoughtHeader,
  ChainOfThoughtSearchResult,
  ChainOfThoughtSearchResults,
  ChainOfThoughtStep,
} from "./ai-elements/chain-of-thought";
import { Button } from "./ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "./ui/collapsible";

const RightSidebar = () => {
  const { rightSidebarOpen, setRightSidebarOpen } = useSidebar();
  const { cot } = useChat();
  return (
    <div
      className={cn(
        "relative border-l border-border bg-background transition-all duration-300 z-30",
        // Desktop behavior
        "hidden md:block",
        rightSidebarOpen ? "md:w-96" : "md:w-0 md:overflow-hidden",
        // Mobile behavior - overlay
        rightSidebarOpen &&
          "fixed inset-y-0 right-0 w-64 md:relative md:inset-auto"
      )}
    >
      <Collapsible open={rightSidebarOpen} onOpenChange={setRightSidebarOpen}>
        <CollapsibleContent className="h-full">
          <div className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Steps</h2>
              <CollapsibleTrigger asChild>
                <Button
                  className="cursor-pointer"
                  variant="ghost"
                  size="sm"
                  aria-label="Close cot panel"
                >
                  <XIcon className="h-4 w-4" />
                  <span className="sr-only">Close settings panel</span>
                </Button>
              </CollapsibleTrigger>
            </div>
            {/* Placeholder for future features */}
            <div className="space-y-2">
              {cot.length > 0 && (
                <div className="p-3 rounded-lg bg-secondary/50 border border-border/50 text-sm">
                  <ChainOfThought defaultOpen>
                    <ChainOfThoughtHeader className="font-semibold text-xl cursor-pointer">
                      Agent workflow
                    </ChainOfThoughtHeader>
                    <ChainOfThoughtContent>
                      {cot.map((c, i) =>
                        c.content ? (
                          <ChainOfThoughtStep
                            key={i}
                            icon={c.icon}
                            label={c.content}
                            status="complete"
                          >
                            <ChainOfThoughtSearchResults>
                              <ChainOfThoughtSearchResult>
                                {c.search_query}
                              </ChainOfThoughtSearchResult>
                            </ChainOfThoughtSearchResults>
                          </ChainOfThoughtStep>
                        ) : null
                      )}
                    </ChainOfThoughtContent>
                  </ChainOfThought>
                </div>
              )}
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
};

export default RightSidebar;
