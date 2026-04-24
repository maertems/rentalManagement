import { useState, type FormEvent } from "react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useCreateOwnerFull } from "@/hooks/useOwners";
import { useUsersList } from "@/hooks/useUsers";
import { getApiErrorMessage } from "@/lib/apiError";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type Mode = "new" | "existing";

export function OwnerFullFormDialog({ open, onOpenChange }: Props) {
  const [submitting, setSubmitting] = useState(false);
  const [mode, setMode] = useState<Mode>("new");
  const createMut = useCreateOwnerFull();
  const usersQuery = useUsersList();

  // New user fields
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [userName, setUserName] = useState("");

  // Existing user field
  const [existingUserId, setExistingUserId] = useState<number | "">("");

  // Owner fields
  const [ownerName, setOwnerName] = useState("");
  const [ownerPhone, setOwnerPhone] = useState("");
  const [ownerAddress, setOwnerAddress] = useState("");
  const [ownerZip, setOwnerZip] = useState("");
  const [ownerCity, setOwnerCity] = useState("");
  const [ownerIban, setOwnerIban] = useState("");

  function resetForm() {
    setMode("new");
    setEmail(""); setPassword(""); setUserName("");
    setExistingUserId("");
    setOwnerName(""); setOwnerPhone("");
    setOwnerAddress(""); setOwnerZip(""); setOwnerCity(""); setOwnerIban("");
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();

    if (mode === "new") {
      if (!email.trim()) { toast.error("L'email est requis"); return; }
      if (!password.trim()) { toast.error("Le mot de passe est requis"); return; }
    } else {
      if (existingUserId === "") { toast.error("Sélectionnez un utilisateur"); return; }
    }
    if (!ownerName.trim()) { toast.error("Le nom du propriétaire est requis"); return; }

    setSubmitting(true);
    try {
      const ownerPayload = {
        name: ownerName.trim() || null,
        // In new-user mode, owner.email mirrors the user's email
        email: mode === "new" ? (email.trim() || null) : null,
        phoneNumber: ownerPhone.trim() || null,
        address: ownerAddress.trim() || null,
        zipCode: ownerZip === "" ? null : Number(ownerZip),
        city: ownerCity.trim() || null,
        iban: ownerIban.trim() || null,
      };

      if (mode === "new") {
        await createMut.mutateAsync({
          user: {
            email: email.trim(),
            password: password.trim(),
            name: userName.trim() || null,
          },
          owner: ownerPayload,
        });
      } else {
        await createMut.mutateAsync({
          existingUserId: Number(existingUserId),
          owner: ownerPayload,
        });
      }

      toast.success("Propriétaire créé");
      resetForm();
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  // Users without an owner (can be linked)
  const availableUsers = (usersQuery.data ?? []).filter((u) => u.ownerId === null);

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) resetForm(); onOpenChange(v); }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Nouveau propriétaire</DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-6">

          {/* Mode toggle */}
          <div>
            <p className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Compte utilisateur
            </p>
            <div className="flex gap-4 mb-4">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="radio"
                  name="userMode"
                  checked={mode === "new"}
                  onChange={() => setMode("new")}
                  className="h-4 w-4"
                />
                Créer un nouvel utilisateur
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="radio"
                  name="userMode"
                  checked={mode === "existing"}
                  onChange={() => setMode("existing")}
                  className="h-4 w-4"
                />
                Utiliser un utilisateur existant
              </label>
            </div>

            {mode === "new" ? (
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="email">Email * <span className="text-xs text-muted-foreground">(utilisé pour le compte et le profil propriétaire)</span></Label>
                  <Input
                    id="email"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="password">Mot de passe *</Label>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="userName">Nom (compte)</Label>
                  <Input
                    id="userName"
                    value={userName}
                    onChange={(e) => setUserName(e.target.value)}
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-1.5">
                <Label htmlFor="existingUser">Utilisateur *</Label>
                <select
                  id="existingUser"
                  value={existingUserId}
                  onChange={(e) => setExistingUserId(e.target.value === "" ? "" : Number(e.target.value))}
                  className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">— Sélectionner un utilisateur —</option>
                  {availableUsers.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name ?? u.email} ({u.email})
                    </option>
                  ))}
                </select>
                {usersQuery.isSuccess && availableUsers.length === 0 && (
                  <p className="text-xs text-muted-foreground">Aucun utilisateur sans propriétaire.</p>
                )}
              </div>
            )}
          </div>

          <div className="border-t" />

          {/* Owner section */}
          <div>
            <p className="mb-3 text-sm font-medium text-muted-foreground uppercase tracking-wide">
              Profil propriétaire
            </p>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="ownerName">Nom *</Label>
                <Input
                  id="ownerName"
                  required
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ownerPhone">Téléphone</Label>
                <Input
                  id="ownerPhone"
                  value={ownerPhone}
                  onChange={(e) => setOwnerPhone(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="ownerAddress">Adresse</Label>
                <Input
                  id="ownerAddress"
                  value={ownerAddress}
                  onChange={(e) => setOwnerAddress(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ownerZip">Code postal</Label>
                <Input
                  id="ownerZip"
                  type="text"
                  inputMode="numeric"
                  value={ownerZip}
                  onChange={(e) => setOwnerZip(e.target.value.replace(/\D/g, ""))}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="ownerCity">Ville</Label>
                <Input
                  id="ownerCity"
                  value={ownerCity}
                  onChange={(e) => setOwnerCity(e.target.value)}
                />
              </div>
              <div className="space-y-1.5 sm:col-span-2">
                <Label htmlFor="ownerIban">IBAN</Label>
                <Input
                  id="ownerIban"
                  value={ownerIban}
                  onChange={(e) => setOwnerIban(e.target.value)}
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => { resetForm(); onOpenChange(false); }}
              disabled={submitting}
            >
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "…" : "Créer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
