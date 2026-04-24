import { LogOut } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/useAuth";

export function AppHeader() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  async function handleLogout() {
    await logout();
    queryClient.clear();
    void navigate({ to: "/login" });
  }

  return (
    <header className="flex h-14 items-center justify-between border-b bg-card px-6">
      <div className="text-sm text-muted-foreground">
        Gestion locative
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-muted-foreground">
          {user?.email}
          {user?.isAdmin === 1 && (
            <span className="ml-2 rounded bg-primary px-1.5 py-0.5 text-xs text-primary-foreground">
              admin
            </span>
          )}
        </span>
        <Button variant="ghost" size="sm" onClick={() => void handleLogout()}>
          <LogOut className="mr-1 h-4 w-4" />
          Déconnexion
        </Button>
      </div>
    </header>
  );
}
