import { useEffect, useState, type FormEvent } from "react";
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
import { useCreateUser, useUpdateUser } from "@/hooks/useUsers";
import { useOwnersList } from "@/hooks/useOwners";
import { getApiErrorMessage } from "@/lib/apiError";
import type { User } from "@/api/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  user: User | null; // null = create
}

export function UserFormDialog({ open, onOpenChange, user }: Props) {
  const isEdit = user !== null;
  const createMut = useCreateUser();
  const updateMut = useUpdateUser();
  const ownersQuery = useOwnersList();

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [isWithdraw, setIsWithdraw] = useState(false);
  const [ownerId, setOwnerId] = useState<number | "">("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      if (user) {
        setEmail(user.email ?? "");
        setUsername(user.username ?? "");
        setName(user.name ?? "");
        setPassword("");
        setIsAdmin(!!user.isAdmin);
        setIsWithdraw(!!user.isWithdraw);
        setOwnerId(user.ownerId ?? "");
      } else {
        setEmail("");
        setUsername("");
        setName("");
        setPassword("");
        setIsAdmin(false);
        setIsWithdraw(false);
        setOwnerId("");
      }
      setSubmitting(false);
    }
  }, [open, user]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) {
      toast.error("L'email est requis");
      return;
    }
    if (!isEdit && !password) {
      toast.error("Le mot de passe est requis");
      return;
    }
    setSubmitting(true);
    try {
      const payload: Parameters<typeof createMut.mutateAsync>[0] = {
        email: email.trim(),
        username: username.trim() || null,
        name: name.trim() || null,
        isAdmin: isAdmin ? 1 : 0,
        isWithdraw: isWithdraw ? 1 : 0,
        ownerId: ownerId === "" ? null : Number(ownerId),
      };
      if (password) payload.password = password;

      if (isEdit && user) {
        await updateMut.mutateAsync({ id: user.id, input: payload });
        toast.success("Utilisateur modifié");
      } else {
        await createMut.mutateAsync(payload);
        toast.success("Utilisateur créé");
      }
      onOpenChange(false);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isEdit ? "Modifier l'utilisateur" : "Nouvel utilisateur"}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="uemail">Email *</Label>
            <Input
              id="uemail"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="uusername">Nom d'utilisateur</Label>
            <Input
              id="uusername"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="uname">Nom complet</Label>
            <Input
              id="uname"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="upassword">
              Mot de passe {isEdit ? "(laisser vide pour ne pas changer)" : "*"}
            </Label>
            <Input
              id="upassword"
              type="password"
              value={password}
              required={!isEdit}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="uownerId">Propriétaire associé</Label>
            <select
              id="uownerId"
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value === "" ? "" : Number(e.target.value))}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="">— Aucun propriétaire —</option>
              {(ownersQuery.data?.rows ?? []).map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name ?? `#${o.id}`}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={isAdmin}
                onChange={(e) => setIsAdmin(e.target.checked)}
              />
              <span>Administrateur</span>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={isWithdraw}
                onChange={(e) => setIsWithdraw(e.target.checked)}
              />
              <span>Accès virement (withdraw)</span>
            </label>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
            >
              Annuler
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "…" : "Enregistrer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
