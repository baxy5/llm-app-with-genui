"use client";

import {
  createContext,
  useContext,
  useState,
  ReactNode,
  Dispatch,
  SetStateAction,
} from "react";

interface SidebarContextType {
  leftSidebarOpen: boolean;
  rightSidebarOpen: boolean;
  setLeftSidebarOpen: Dispatch<SetStateAction<boolean>>;
  setRightSidebarOpen: Dispatch<SetStateAction<boolean>>;
  toggleLeftSidebar: () => void;
  toggleRightSidebar: () => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export const useSidebar = (): SidebarContextType => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

interface SidebarProviderProps {
  children: ReactNode;
  defaultLeftOpen?: boolean;
  defaultRightOpen?: boolean;
}

export const SidebarProvider = ({
  children,
  defaultLeftOpen = true,
  defaultRightOpen = true,
}: SidebarProviderProps) => {
  const [leftSidebarOpen, setLeftSidebarOpen] =
    useState<boolean>(defaultLeftOpen);
  const [rightSidebarOpen, setRightSidebarOpen] =
    useState<boolean>(defaultRightOpen);

  const toggleLeftSidebar = () => {
    setLeftSidebarOpen((prev) => !prev);
  };

  const toggleRightSidebar = () => {
    setRightSidebarOpen((prev) => !prev);
  };

  const value: SidebarContextType = {
    leftSidebarOpen,
    rightSidebarOpen,
    setLeftSidebarOpen,
    setRightSidebarOpen,
    toggleLeftSidebar,
    toggleRightSidebar,
  };

  return (
    <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
  );
};
