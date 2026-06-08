import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { Download, FileText } from "lucide-react";

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
import {
  letterTemplatesApi,
  type LetterGenerateOptions,
  type LetterTemplate,
} from "@/lib/api/letterTemplates";

interface Props {
  employeeId: number;
  employeeCode: string;
}

export function LettersDocsCard({ employeeId, employeeCode }: Props) {
  const { data = [] } = useQuery({
    queryKey: ["letter-templates"],
    queryFn: () => letterTemplatesApi.list(false),
  });

  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [opts, setOpts] = useState<LetterGenerateOptions>({});
  const [busy, setBusy] = useState(false);

  const selected = useMemo<LetterTemplate | undefined>(
    () =>
      (data as LetterTemplate[]).find((t) => t.id === selectedId) ??
      undefined,
    [data, selectedId],
  );

  async function download() {
    if (!selected) return;
    setBusy(true);
    try {
      const blob = await letterTemplatesApi.generate(
        employeeId,
        selected.id,
        opts,
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${selected.code}_${employeeCode}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Letter generated");
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response
          ?.data?.detail ?? "Could not generate letter";
      toast.error(detail);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" /> Letters &amp; Documents
        </CardTitle>
        <CardDescription>
          Generate any HR letter on the Jaikalki letterhead. Edit the
          templates from the <strong>Letters</strong> tab in the sidebar.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <Label>Template</Label>
          <select
            value={selectedId ?? ""}
            onChange={(e) =>
              setSelectedId(
                e.target.value ? Number(e.target.value) : null,
              )
            }
            className="w-full bg-transparent border border-brand-brown-50 rounded-md px-3 py-2 text-sm"
          >
            <option value="">Select a letter…</option>
            {(data as LetterTemplate[]).map((t) => (
              <option key={t.id} value={t.id}>
                {t.name}
              </option>
            ))}
          </select>
        </div>

        {selected && (
          <div className="grid sm:grid-cols-2 gap-3">
            <div>
              <Label>Letter no. (optional)</Label>
              <Input
                value={opts.letter_no ?? ""}
                onChange={(e) =>
                  setOpts({ ...opts, letter_no: e.target.value })
                }
                placeholder="JKT/HR/OL/042/2026"
              />
            </div>
            <div>
              <Label>Date (optional)</Label>
              <Input
                value={opts.on_date ?? ""}
                onChange={(e) =>
                  setOpts({ ...opts, on_date: e.target.value })
                }
                placeholder="08 Jun 2026"
              />
            </div>
            {(selected.category === "experience" ||
              selected.body.includes("{{last_working_date}}")) && (
              <div>
                <Label>Last working date</Label>
                <Input
                  value={opts.last_working_date ?? ""}
                  onChange={(e) =>
                    setOpts({
                      ...opts,
                      last_working_date: e.target.value,
                    })
                  }
                  placeholder="31 Mar 2026"
                />
              </div>
            )}
            {(selected.body.includes("{{ctc_amount}}") ||
              selected.category === "offer" ||
              selected.category === "appointment" ||
              selected.category === "increment") && (
              <>
                <div>
                  <Label>CTC amount (figures)</Label>
                  <Input
                    value={opts.ctc_amount ?? ""}
                    onChange={(e) =>
                      setOpts({ ...opts, ctc_amount: e.target.value })
                    }
                    placeholder="6,00,000"
                  />
                </div>
                <div>
                  <Label>CTC amount (words)</Label>
                  <Input
                    value={opts.ctc_amount_words ?? ""}
                    onChange={(e) =>
                      setOpts({
                        ...opts,
                        ctc_amount_words: e.target.value,
                      })
                    }
                    placeholder="Six Lakh Only"
                  />
                </div>
              </>
            )}
          </div>
        )}

        <div className="flex justify-end">
          <Button
            onClick={download}
            disabled={!selected || busy}
            variant="default"
          >
            <Download className="h-4 w-4 mr-1" />
            {busy ? "Generating…" : "Generate PDF"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
