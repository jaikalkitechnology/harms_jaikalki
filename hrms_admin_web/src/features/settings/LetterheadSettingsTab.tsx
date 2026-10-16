// Settings → Letterhead: the header, footer and logo printed on every
// letter generated from a template.
import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Eye, ImageUp, RotateCcw, Save } from "lucide-react";

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
import { apiClient } from "@/lib/api/client";
import {
  hrDocumentsApi,
  openBlob,
  type Letterhead,
  type LetterheadUpdate,
} from "@/lib/api/hrDocuments";

function errDetail(e: unknown, fallback: string): string {
  return (
    (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? fallback
  );
}

const TEXTAREA =
  "flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm";

const toDraft = (l: Letterhead): Required<LetterheadUpdate> => ({
  company_name: l.company_name,
  cin: l.cin,
  gst: l.gst,
  phone: l.phone,
  email: l.email,
  website: l.website,
  regd_office: l.regd_office,
  corporate_office: l.corporate_office,
  footer_note: l.footer_note,
  show_watermark: l.show_watermark,
  show_corner_accents: l.show_corner_accents,
});

export function LetterheadSettingsTab() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["letterhead"], queryFn: hrDocumentsApi.letterhead });
  const [draft, setDraft] = useState<Required<LetterheadUpdate> | null>(null);
  const [previewing, setPreviewing] = useState(false);

  useEffect(() => {
    if (data) setDraft(toDraft(data));
  }, [data]);

  const save = useMutation({
    mutationFn: () => hrDocumentsApi.updateLetterhead(draft!),
    onSuccess: (l) => {
      qc.setQueryData(["letterhead"], l);
      toast.success("Letterhead saved — new letters use it");
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  if (!data || !draft) {
    return <p className="text-sm text-brand-brown-light">Loading…</p>;
  }

  const set = <K extends keyof LetterheadUpdate>(k: K, v: Required<LetterheadUpdate>[K]) =>
    setDraft({ ...draft, [k]: v });
  const dirty = JSON.stringify(draft) !== JSON.stringify(toDraft(data));

  async function preview() {
    setPreviewing(true);
    try {
      openBlob(await hrDocumentsApi.preview(draft!));
    } catch (e) {
      toast.error(errDetail(e, "Could not build the preview"));
    } finally {
      setPreviewing(false);
    }
  }

  const text = (k: keyof LetterheadUpdate, label: string, placeholder?: string) => (
    <div className="space-y-1.5">
      <Label htmlFor={`lh-${k}`}>{label}</Label>
      <Input
        id={`lh-${k}`}
        value={String(draft[k] ?? "")}
        placeholder={placeholder}
        onChange={(e) => set(k, e.target.value as never)}
      />
    </div>
  );

  return (
    <div className="grid items-start gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Header &amp; footer</CardTitle>
          <CardDescription>
            Printed on every letter created from a template — offer, appointment,
            confirmation, experience and the rest. Letters already issued keep the
            letterhead they were made with.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
              Header
            </h3>
            {text("company_name", "Company name")}
            <div className="grid gap-3 sm:grid-cols-2">
              {text("cin", "CIN", "Leave blank to hide")}
              {text("gst", "GST", "Leave blank to hide")}
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {text("phone", "Phone")}
              {text("email", "Email")}
              {text("website", "Website")}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="lh-regd">Registered office</Label>
              <textarea
                id="lh-regd"
                rows={2}
                maxLength={300}
                className={TEXTAREA}
                value={draft.regd_office}
                onChange={(e) => set("regd_office", e.target.value)}
              />
              <p className="text-xs text-brand-brown-light">
                Shown under the header line, after “Regd. Office:”.
              </p>
            </div>
          </section>

          <section className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-brand-gold-dark">
              Footer
            </h3>
            <div className="space-y-1.5">
              <Label htmlFor="lh-corp">Office address block (bottom right)</Label>
              <textarea
                id="lh-corp"
                rows={6}
                maxLength={400}
                className={TEXTAREA}
                value={draft.corporate_office}
                onChange={(e) => set("corporate_office", e.target.value)}
              />
              <p className="text-xs text-brand-brown-light">
                One line per row; the first line is printed in bold. Up to 7 lines.
              </p>
            </div>
            {text("footer_note", "Footer note (bottom left)", "Jaikalki Technology Pvt Ltd · Confidential")}
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={draft.show_watermark}
                  onChange={(e) => set("show_watermark", e.target.checked)}
                />
                Faint logo watermark in the middle of the page
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={draft.show_corner_accents}
                  onChange={(e) => set("show_corner_accents", e.target.checked)}
                />
                Brown corner accents
              </label>
            </div>
          </section>

          <div className="flex flex-wrap justify-end gap-2 border-t border-brand-brown-50 pt-4">
            <Button variant="outline" className="gap-2" onClick={preview} disabled={previewing}>
              <Eye className="size-4" /> {previewing ? "Preparing…" : "Preview"}
            </Button>
            <Button
              variant="outline"
              disabled={!dirty || save.isPending}
              onClick={() => setDraft(toDraft(data))}
            >
              Discard
            </Button>
            <Button
              className="gap-2"
              disabled={!dirty || save.isPending || !draft.company_name.trim()}
              onClick={() => save.mutate()}
            >
              <Save className="size-4" /> {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>

      <LogoCard letterhead={data} />
    </div>
  );
}

function LogoCard({ letterhead }: { letterhead: Letterhead }) {
  const qc = useQueryClient();
  const custom = letterhead.has_custom_logo;
  // Fetched through the API client so the auth cookie goes along.
  const { data: logoSrc } = useQuery({
    queryKey: ["letterhead-logo", custom],
    enabled: custom,
    queryFn: async () => {
      const res = await apiClient.get(hrDocumentsApi.logoUrl(), { responseType: "blob" });
      return URL.createObjectURL(res.data as Blob);
    },
  });
  useEffect(() => () => {
    if (logoSrc) URL.revokeObjectURL(logoSrc);
  }, [logoSrc]);

  const done = (l: Letterhead, msg: string) => {
    qc.setQueryData(["letterhead"], l);
    qc.invalidateQueries({ queryKey: ["letterhead-logo"] });
    toast.success(msg);
  };
  const upload = useMutation({
    mutationFn: (f: File) => hrDocumentsApi.uploadLogo(f),
    onSuccess: (l) => done(l, "Logo updated"),
    onError: (e) => toast.error(errDetail(e, "Could not upload the logo")),
  });
  const reset = useMutation({
    mutationFn: hrDocumentsApi.resetLogo,
    onSuccess: (l) => done(l, "Back to the standard Jaikalki logo"),
    onError: (e) => toast.error(errDetail(e, "Could not reset")),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Logo</CardTitle>
        <CardDescription>
          Top-left of the header, and the faint watermark. PNG with a transparent
          background works best; up to 2 MB.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid h-36 place-items-center rounded-xl border border-dashed border-brand-brown-100 bg-white p-3">
          {custom ? (
            logoSrc ? (
              <img src={logoSrc} alt="Letterhead logo" className="max-h-full max-w-full object-contain" />
            ) : (
              <span className="text-xs text-brand-brown-light">Loading…</span>
            )
          ) : (
            <span className="px-4 text-center text-sm text-brand-brown-light">
              Standard Jaikalki logo
            </span>
          )}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" className="gap-2" disabled={upload.isPending}>
            <label className="cursor-pointer">
              <ImageUp className="size-4" />
              {upload.isPending ? "Uploading…" : custom ? "Replace logo" : "Upload logo"}
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) upload.mutate(f);
                  e.target.value = "";
                }}
              />
            </label>
          </Button>
          {custom && (
            <Button
              variant="ghost"
              className="gap-2"
              disabled={reset.isPending}
              onClick={() => reset.mutate()}
            >
              <RotateCcw className="size-4" /> Use standard logo
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
