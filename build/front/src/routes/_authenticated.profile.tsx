import { useState, useEffect, type FormEvent } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";

import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMyProfile, useUpdateMyProfile } from "@/hooks/useProfile";
import { getApiErrorMessage } from "@/lib/apiError";

function ProfilePage() {
  const { data, isLoading } = useMyProfile();
  const updateMut = useUpdateMyProfile();

  // User form state
  const [userName, setUserName] = useState("");
  const [userUsername, setUserUsername] = useState("");
  const [submittingUser, setSubmittingUser] = useState(false);

  // Owner form state
  const [ownerName, setOwnerName] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [ownerPhone, setOwnerPhone] = useState("");
  const [ownerAddress, setOwnerAddress] = useState("");
  const [ownerZip, setOwnerZip] = useState<number | "">("");
  const [ownerCity, setOwnerCity] = useState("");
  const [ownerIban, setOwnerIban] = useState("");
  const [submittingOwner, setSubmittingOwner] = useState(false);

  useEffect(() => {
    if (data?.user) {
      setUserName(data.user.name ?? "");
      setUserUsername(data.user.username ?? "");
      if (data.owner) {
        setOwnerName(data.owner.name ?? "");
        setOwnerEmail(data.owner.email ?? "");
        setOwnerPhone(data.owner.phoneNumber ?? "");
        setOwnerAddress(data.owner.address ?? "");
        setOwnerZip(data.owner.zipCode ?? "");
        setOwnerCity(data.owner.city ?? "");
        setOwnerIban(data.owner.iban ?? "");
      }
    }
  }, [data]);

  async function submitUser(e: FormEvent) {
    e.preventDefault();
    setSubmittingUser(true);
    try {
      await updateMut.mutateAsync({
        user: {
          name: userName.trim() || null,
          username: userUsername.trim() || null,
        },
      });
      toast.success("Compte mis à jour");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmittingUser(false);
    }
  }

  async function submitOwner(e: FormEvent) {
    e.preventDefault();
    setSubmittingOwner(true);
    try {
      await updateMut.mutateAsync({
        owner: {
          name: ownerName.trim() || null,
          email: ownerEmail.trim() || null,
          phoneNumber: ownerPhone.trim() || null,
          address: ownerAddress.trim() || null,
          zipCode: ownerZip === "" ? null : Number(ownerZip),
          city: ownerCity.trim() || null,
          iban: ownerIban.trim() || null,
        },
      });
      toast.success("Profil propriétaire mis à jour");
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setSubmittingOwner(false);
    }
  }

  if (isLoading) return <p className="p-4 text-muted-foreground">Chargement…</p>;

  return (
    <div className="space-y-4">
      <PageHeader title="Mes informations" />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* User section */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Mon compte</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={submitUser} className="space-y-4">
              <div className="space-y-1.5">
                <Label>Email</Label>
                <Input value={data?.user?.email ?? ""} disabled className="bg-muted" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="userName">Nom</Label>
                <Input
                  id="userName"
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="userUsername">Nom d'utilisateur</Label>
                <Input
                  id="userUsername"
                  value={userUsername}
                  onChange={(e) => setUserUsername(e.target.value)}
                />
              </div>
              <Button type="submit" disabled={submittingUser}>
                {submittingUser ? "…" : "Enregistrer"}
              </Button>
            </form>
          </CardContent>
        </Card>

        {/* Owner section — only shown if user has an owner profile */}
        {data?.owner && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Mon profil propriétaire</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={submitOwner} className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5 sm:col-span-2">
                  <Label htmlFor="ownerName">Nom</Label>
                  <Input
                    id="ownerName"
                    value={ownerName}
                    onChange={(e) => setOwnerName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="ownerEmail">Email</Label>
                  <Input
                    id="ownerEmail"
                    type="email"
                    value={ownerEmail}
                    onChange={(e) => setOwnerEmail(e.target.value)}
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
                    onChange={(e) =>
                      setOwnerZip(e.target.value === "" ? "" : Number(e.target.value.replace(/\D/g, "")))
                    }
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
                <div className="sm:col-span-2">
                  <Button type="submit" disabled={submittingOwner}>
                    {submittingOwner ? "…" : "Enregistrer"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export const Route = createFileRoute("/_authenticated/profile")({
  component: ProfilePage,
});
