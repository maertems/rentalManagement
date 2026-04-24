import { useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMyProfile, useSendTestEmail } from "@/hooks/useProfile";
import { useOwnerParams, useUpdateOwnerParams } from "@/hooks/useParams";
import { useTenantsList } from "@/hooks/useTenants";
import { getApiErrorMessage } from "@/lib/apiError";

function SettingsPage() {
  const { data: profile } = useMyProfile();
  const ownerId = profile?.owner?.id ?? null;

  const { data: params, isLoading } = useOwnerParams(ownerId);
  const updateMut = useUpdateOwnerParams();
  const sendTestMut = useSendTestEmail();

  const { data: tenants } = useTenantsList({ active: 1 });

  const [rentReceiptDay, setRentReceiptDay] = useState("");

  // Test email state
  const [testTenantId, setTestTenantId] = useState<string>(""); // "" = tous
  const [testMonth, setTestMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });

  useEffect(() => {
    if (params) {
      setRentReceiptDay(params.rentReceiptDay != null ? String(params.rentReceiptDay) : "");
    }
  }, [params]);

  async function handleSave() {
    if (!ownerId) return;
    const day = rentReceiptDay ? Number(rentReceiptDay) : null;
    if (day !== null && (day < 1 || day > 31 || !Number.isInteger(day))) {
      toast.error("Le jour doit être compris entre 1 et 31");
      return;
    }
    try {
      await updateMut.mutateAsync({ ownerId, input: { rentReceiptDay: day } });
      toast.success("Paramètres enregistrés");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  async function handleTestEmail() {
    if (!testMonth) {
      toast.error("Sélectionnez un mois");
      return;
    }
    try {
      const result = await sendTestMut.mutateAsync({
        tenant_id: testTenantId ? Number(testTenantId) : null,
        month: testMonth,
      });
      const sentCount = result.sent.length;
      const skippedCount = result.skipped.length;
      if (sentCount > 0) {
        toast.success(`${sentCount} email(s) envoyé(s) : ${result.sent.join(", ")}`);
      }
      if (skippedCount > 0) {
        for (const s of result.skipped) {
          toast.warning(`${s.name} ignoré : ${s.reason}`);
        }
      }
      if (sentCount === 0 && skippedCount === 0) {
        toast.info("Aucun locataire à traiter");
      }
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Paramètres" />

      <div className="max-w-md rounded-md border p-6 space-y-6">
        <h3 className="text-sm font-semibold">Génération des quittances</h3>

        {isLoading || !ownerId ? (
          <p className="text-sm text-muted-foreground">Chargement…</p>
        ) : (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="rentReceiptDay">Jour du mois</Label>
              <Input
                id="rentReceiptDay"
                type="number"
                min={1}
                max={31}
                className="max-w-[120px]"
                value={rentReceiptDay}
                onChange={(e) => setRentReceiptDay(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Jour auquel le cron génère les quittances chaque mois (1–31).
                Si le mois est plus court, le dernier jour du mois est utilisé.
                Par défaut : 25.
              </p>
            </div>

            <Button onClick={() => void handleSave()} disabled={updateMut.isPending}>
              {updateMut.isPending ? "…" : "Enregistrer"}
            </Button>
          </div>
        )}
      </div>

      <div className="max-w-md rounded-md border p-6 space-y-6">
        <h3 className="text-sm font-semibold">Test d'envoi d'email</h3>
        <p className="text-xs text-muted-foreground">
          Simule le cron : crée la quittance (avis d'échéance) si elle n'existe pas encore pour le mois choisi,
          génère le PDF, et envoie l'email si la case "avis d'échéance" est cochée pour le locataire.
          L'email est envoyé à votre adresse (pas au locataire). Préfixe [TEST] dans l'objet.
        </p>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="testTenant">Locataire</Label>
            <select
              id="testTenant"
              value={testTenantId}
              onChange={(e) => setTestTenantId(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm"
            >
              <option value="">Tous les locataires actifs</option>
              {(tenants ?? []).map((t) => (
                <option key={t.id} value={t.id}>
                  {[t.firstName, t.name].filter(Boolean).join(" ") || `#${t.id}`}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="testMonth">Mois</Label>
            <Input
              id="testMonth"
              type="month"
              value={testMonth}
              onChange={(e) => setTestMonth(e.target.value)}
              className="max-w-[180px]"
            />
          </div>

          <Button
            onClick={() => void handleTestEmail()}
            disabled={sendTestMut.isPending || !ownerId}
            variant="outline"
          >
            {sendTestMut.isPending ? "Envoi…" : "Envoyer le test"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/settings")({
  component: SettingsPage,
});
