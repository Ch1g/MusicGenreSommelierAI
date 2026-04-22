import { observer } from "mobx-react-lite";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { StoreProvider, useStores } from "@/stores/context";
import { RootStore } from "@/stores/root.store";
import { HomePage } from "@/pages/HomePage/HomePage";
import { ProfilePage } from "@/pages/ProfilePage/ProfilePage";

const store = new RootStore();

const ProtectedRoute = observer(({ children }: { children: React.ReactNode }) => {
  const { auth } = useStores();
  if (!auth.isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
});

const AppRoutes = observer(() => (
  <Routes>
    <Route path="/" element={<HomePage />} />
    <Route
      path="/profile"
      element={
        <ProtectedRoute>
          <ProfilePage />
        </ProtectedRoute>
      }
    />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
));

export function App() {
  return (
    <StoreProvider store={store}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </StoreProvider>
  );
}
