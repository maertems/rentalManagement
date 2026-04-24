import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppLayout } from "@/components/layout/AppLayout";
import * as authApi from "@/api/authApi";

export const Route = createFileRoute("/_authenticated")({
  beforeLoad: async () => {
    try {
      await authApi.getMe();
    } catch {
      throw redirect({ to: "/login" });
    }
  },
  component: AppLayout,
});
