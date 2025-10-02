import React from "react";
import { SidebarProvider } from "@/contexts/sidebar-context";
import { ChatProvider } from "@/contexts/chat-context";

const AppContainer = ({ children }: { children: React.ReactNode }) => {
  return (
    <ChatProvider>
      <SidebarProvider defaultLeftOpen={true} defaultRightOpen={true}>
        {children}
      </SidebarProvider>
    </ChatProvider>
  );
};

export default AppContainer;
