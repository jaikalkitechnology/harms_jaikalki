import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router-dom";
import { Toaster } from "sonner";
import { router } from "@/router";
import { ErrorBoundary } from "@/components/shared/ErrorBoundary";
import { useAuthStore } from "@/store/auth";
import { useThemeStore } from "@/store/theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

export default function App() {
  const checkAuth = useAuthStore((s) => s.checkAuth);
  const initTheme = useThemeStore((s) => s.init);
  const themeEffective = useThemeStore((s) => s.effective);

  useEffect(() => {
    initTheme();
    checkAuth();
  }, [checkAuth, initTheme]);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster
          theme={themeEffective}
          position="top-right"
          toastOptions={{
            classNames: {
              toast: "font-body",
              title: "font-medium",
            },
          }}
        />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
