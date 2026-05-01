import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { AlertTriangle, ShieldCheck, Trash2, UserPlus } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { justiceApi } from "@/lib/api/justice";

const ROLES = ["presiding_officer", "member", "external_member", "secretary"];

export default function IccPage() {
  const queryClient = useQueryClient();
  const { data: members = [], isLoading } = useQuery({
    queryKey: ["icc-members"],
    queryFn: justiceApi.iccMembers,
  });
  const { data: compliance } = useQuery({
    queryKey: ["icc-compliance"],
    queryFn: justiceApi.iccCompliance,
  });

  const [name, setName] = useState("");
  const [role, setRole] = useState("member");
  const [gender, setGender] = useState("female");
  const [external, setExternal] = useState(false);
  const [contact, setContact] = useState("");
  const [termStart, setTermStart] = useState(
    new Date().toISOString().slice(0, 10),
  );

  const add = useMutation({
    mutationFn: () =>
      justiceApi.addIccMember({
        member_name: name,
        role,
        gender,
        is_external: external,
        contact: contact || undefined,
        term_start: termStart,
      }),
    onSuccess: () => {
      toast.success("Member added");
      setName("");
      setContact("");
      queryClient.invalidateQueries({ queryKey: ["icc-members"] });
      queryClient.invalidateQueries({ queryKey: ["icc-compliance"] });
    },
    onError: () => toast.error("Could not add member"),
  });

  const deactivate = useMutation({
    mutationFn: (id: number) => justiceApi.deactivateIccMember(id),
    onSuccess: () => {
      toast.success("Member deactivated");
      queryClient.invalidateQueries({ queryKey: ["icc-members"] });
      queryClient.invalidateQueries({ queryKey: ["icc-compliance"] });
    },
  });

  if (isLoading) return <LoadingScreen label="Loading ICC…" />;

  return (
    <div className="space-y-6">
      <div>
        <div className="text-[10px] font-mono uppercase tracking-[0.3em] text-brand-gold-dark">
          ★ Phase 8 · Internal Complaints Committee
        </div>
        <h2 className="font-display text-3xl font-bold text-brand-brown-darker">
          ICC <span className="display-em">members</span>
        </h2>
        <p className="mt-1 text-sm text-brand-brown-light">
          POSH Act 2013 requires at least 4 active members, ≥50% women, ≥1
          external member, and a designated Presiding Officer.
        </p>
      </div>

      {compliance && (
        <Card>
          <CardContent className="pt-5 flex items-start gap-3">
            {compliance.compliant ? (
              <ShieldCheck className="h-8 w-8 text-success shrink-0" />
            ) : (
              <AlertTriangle className="h-8 w-8 text-warning shrink-0" />
            )}
            <div>
              <div className="text-sm font-medium">
                {compliance.compliant ? "POSH compliant" : "POSH gap detected"}
              </div>
              <div className="text-sm text-brand-brown-light">
                {compliance.member_count} members ·{" "}
                {compliance.women_count} women ·{" "}
                {compliance.external_count} external ·{" "}
                Presiding Officer:{" "}
                {compliance.has_presiding_officer ? "yes" : "no"}
              </div>
              {!compliance.compliant && (
                <ul className="mt-1 text-sm text-warning list-disc pl-5">
                  {compliance.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Active members</CardTitle>
          <CardDescription>{members.length} on record</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-1">
            {members.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between py-2 border-b border-brand-brown-100/60 last:border-0"
              >
                <div>
                  <div className="font-medium">{m.member_name}</div>
                  <div className="text-xs text-brand-brown-light">
                    {m.role.replace(/_/g, " ")} · {m.gender ?? "—"}
                    {m.is_external && " · external"}
                    {m.contact && ` · ${m.contact}`}
                  </div>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deactivate.mutate(m.id)}
                >
                  <Trash2 className="h-4 w-4 text-error" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add member</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (name) add.mutate();
            }}
            className="grid md:grid-cols-3 gap-3"
          >
            <div className="space-y-1.5 md:col-span-2">
              <Label htmlFor="m-name">Name</Label>
              <Input
                id="m-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="m-role">Role</Label>
              <select
                id="m-role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
              >
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {r.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="m-gender">Gender</Label>
              <select
                id="m-gender"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
              >
                <option value="female">Female</option>
                <option value="male">Male</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="m-term">Term starts</Label>
              <Input
                id="m-term"
                type="date"
                value={termStart}
                onChange={(e) => setTermStart(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="m-contact">Contact</Label>
              <Input
                id="m-contact"
                value={contact}
                onChange={(e) => setContact(e.target.value)}
              />
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="accent-brand-gold-dark"
                checked={external}
                onChange={(e) => setExternal(e.target.checked)}
              />
              External member
            </label>
            <div className="md:col-span-3">
              <Button type="submit" disabled={!name || add.isPending}>
                <UserPlus className="h-4 w-4" />
                Add member
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
