import { Link } from "@tanstack/react-router";
import { Home, Users, Building, UserCircle, Shield, Settings, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  to: string;
  label: string;
  icon: typeof Home;
  adminOnly?: boolean;
}

const items: NavItem[] = [
  { to: "/", label: "Accueil", icon: Home },
  { to: "/owners", label: "Propriétaires", icon: UserCircle, adminOnly: true },
  { to: "/places", label: "Biens", icon: Building },
  { to: "/tenants", label: "Locataires", icon: Users },
  { to: "/users", label: "Utilisateurs", icon: Shield, adminOnly: true },
];

export function AppSidebar() {
  const { user } = useAuth();
  const isAdmin = user?.isAdmin === 1;

  return (
    <aside className="flex h-full w-56 flex-col border-r bg-card">
      <div className="px-4 py-4 text-lg font-semibold">Rental</div>
      <nav className="flex-1 space-y-1 px-2">
        {items
          .filter((item) => !item.adminOnly || isAdmin)
          .map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              activeOptions={{ exact: to === "/" }}
              className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              activeProps={{
                className: cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm",
                  "bg-accent text-accent-foreground font-medium",
                ),
              }}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}

        {/* Separator before personal links */}
        <div className="my-2 border-t" />

        <Link
          to="/profile"
          className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          activeProps={{
            className: cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm",
              "bg-accent text-accent-foreground font-medium",
            ),
          }}
        >
          <User className="h-4 w-4" />
          Mes infos
        </Link>

        <Link
          to="/settings"
          className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          activeProps={{
            className: cn(
              "flex items-center gap-2 rounded-md px-3 py-2 text-sm",
              "bg-accent text-accent-foreground font-medium",
            ),
          }}
        >
          <Settings className="h-4 w-4" />
          Paramètres
        </Link>
      </nav>
    </aside>
  );
}
