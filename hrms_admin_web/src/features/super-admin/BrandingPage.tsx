import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Save } from "lucide-react";

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
import { superAdminApi, type Branding } from "@/lib/api/super-admin";

export default function BrandingPage() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["branding"],
    queryFn: superAdminApi.getBranding,
  });
  const [draft, setDraft] = useState<Partial<Branding>>({});

  useEffect(() => {
    if (data) setDraft(data);
  }, [data]);

  const save = useMutation({
    mutationFn: () => superAdminApi.updateBranding(draft),
    onSuccess: () => {
      toast.success("Branding saved");
      qc.invalidateQueries({ queryKey: ["branding"] });
    },
    onError: () => toast.error("Save failed"),
  });

  if (isLoading || !data) return <LoadingScreen />;

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <Card>
        <CardHeader>
          <CardTitle>White-labeling</CardTitle>
          <CardDescription>
            Applied across the admin web, email templates, and (where wired)
            the mobile app.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {(
            [
              ["company_name", "Company name"],
              ["logo_url", "Logo URL"],
              ["favicon_url", "Favicon URL"],
              ["primary_color", "Primary color"],
              ["secondary_color", "Secondary color"],
              ["font_family", "Font family"],
              ["login_background_url", "Login background URL"],
              ["custom_domain", "Custom domain"],
            ] as const
          ).map(([k, label]) => (
            <div key={k}>
              <Label>{label}</Label>
              <Input
                value={(draft[k] as string | null) ?? ""}
                onChange={(e) => setDraft({ ...draft, [k]: e.target.value })}
              />
            </div>
          ))}
          <div className="flex gap-2">
            <Button onClick={() => save.mutate()}>
              <Save className="h-4 w-4 mr-1" /> Save
            </Button>
            <Button variant="outline" onClick={() => setDraft(data)}>
              Reset
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Live preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="rounded-lg p-6 border"
            style={{
              backgroundColor: "#fff",
              fontFamily: draft.font_family ?? "Inter",
              borderColor: (draft.primary_color as string) ?? "#1f2937",
            }}
          >
            <div className="flex items-center gap-3 mb-4">
              {draft.logo_url ? (
                <img
                  src={draft.logo_url}
                  alt="logo"
                  className="h-10 w-10 object-contain rounded"
                />
              ) : (
                <div
                  className="h-10 w-10 rounded flex items-center justify-center text-white font-bold"
                  style={{
                    backgroundColor:
                      (draft.primary_color as string) ?? "#1f2937",
                  }}
                >
                  {(draft.company_name ?? "J").charAt(0)}
                </div>
              )}
              <div className="font-semibold">{draft.company_name}</div>
            </div>
            <button
              className="px-4 py-2 rounded text-white text-sm"
              style={{
                backgroundColor:
                  (draft.primary_color as string) ?? "#1f2937",
              }}
            >
              Primary action
            </button>{" "}
            <button
              className="px-4 py-2 rounded text-white text-sm ml-2"
              style={{
                backgroundColor:
                  (draft.secondary_color as string) ?? "#b45309",
              }}
            >
              Secondary action
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
