import { createFileRoute, redirect } from "@tanstack/react-router";
import { LoginForm } from "@/features/auth/LoginForm";
import * as authApi from "@/api/authApi";

export const Route = createFileRoute("/login")({
  beforeLoad: async () => {
    try {
      await authApi.getMe();
      throw redirect({ to: "/" });
    } catch (err) {
      // not logged in — stay on /login
      if (err && typeof err === "object" && "redirect" in err) throw err;
      return;
    }
  },
  component: LoginForm,
});
