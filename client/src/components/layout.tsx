import AppContainer from "./app-container";
import LeftSideBar from "./left-sidebar";
import RightSidebar from "./right-sidebar";

const Layout = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <main className="flex h-screen max-w-[1440px] m-auto bg-background overflow-hidden">
      <AppContainer>
        <LeftSideBar />
        {children}
        <RightSidebar />
      </AppContainer>
    </main>
  );
};

export default Layout;
