import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AdminLayout() {
  return (
    <div className="min-h-screen flex bg-surface-cream">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 px-4 py-4 md:px-8 md:py-8 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
