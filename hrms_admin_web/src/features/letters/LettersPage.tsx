import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FileText, Plus, Save, Trash2, X } from "lucide-react";

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
import {
  letterTemplatesApi,
  type LetterTemplate,
  type LetterTemplateCreate,
} from "@/lib/api/letterTemplates";

const CATEGORIES = [
  "offer",
  "appointment",
  "confirmation",
  "experience",
  "increment",
  "termination",
  "warning",
  "policy",
  "other",
];

export default function LettersPage() {
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["letter-templates"],
    queryFn: () => letterTemplatesApi.list(true),
  });
  const { data: hints = [] } = useQuery({
    queryKey: ["letter-placeholders"],
    queryFn: letterTemplatesApi.placeholders,
  });

  const [editing, setEditing] = useState<LetterTemplate | null>(null);
  const [showNew, setShowNew] = useState(false);

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" /> Letters &amp; Documents
            </CardTitle>
            <CardDescription>
              HR letter templates. Use{" "}
              <code className="font-mono text-xs">{`{{placeholder}}`}</code>{" "}
              markers — they're substituted from the employee record
              when the letter is generated from the employee&apos;s
              profile page. The Jaikalki letterhead is applied
              automatically to every PDF.
            </CardDescription>
          </div>
          <Button onClick={() => setShowNew(true)} className="shrink-0">
            <Plus className="h-4 w-4 mr-1" /> New template
          </Button>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <table className="w-full text-sm min-w-[720px]">
            <thead className="text-left text-brand-brown-light">
              <tr>
                <th className="py-2 px-4">Name</th>
                <th>Code</th>
                <th>Category</th>
                <th>Status</th>
                <th className="text-right pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(data as LetterTemplate[]).map((t) => (
                <tr key={t.id} className="border-t border-brand-brown-50">
                  <td className="py-2 px-4 font-medium text-brand-brown-darker">
                    {t.name}
                  </td>
                  <td className="font-mono text-xs">{t.code}</td>
                  <td className="capitalize">{t.category}</td>
                  <td>
                    <span
                      className={`text-xs font-mono uppercase tracking-[0.15em] ${
                        t.is_active
                          ? "text-success"
                          : "text-brand-brown-light"
                      }`}
                    >
                      {t.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="text-right pr-4 whitespace-nowrap">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditing(t)}
                    >
                      Edit
                    </Button>{" "}
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        if (confirm(`Delete "${t.name}"?`)) {
                          letterTemplatesApi
                            .remove(t.id)
                            .then(() => {
                              toast.success("Template removed");
                              qc.invalidateQueries({
                                queryKey: ["letter-templates"],
                              });
                            })
                            .catch(() => toast.error("Could not delete"));
                        }
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr>
                  <td
                    colSpan={5}
                    className="text-center py-6 text-brand-brown-light"
                  >
                    No templates yet
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {editing && (
        <TemplateEditor
          template={editing}
          hints={hints}
          onClose={() => setEditing(null)}
          onSaved={() => {
            qc.invalidateQueries({ queryKey: ["letter-templates"] });
            setEditing(null);
          }}
        />
      )}
      {showNew && (
        <TemplateEditor
          template={null}
          hints={hints}
          onClose={() => setShowNew(false)}
          onSaved={() => {
            qc.invalidateQueries({ queryKey: ["letter-templates"] });
            setShowNew(false);
          }}
        />
      )}
    </div>
  );
}

function TemplateEditor({
  template,
  hints,
  onClose,
  onSaved,
}: {
  template: LetterTemplate | null;
  hints: Array<{ key: string; description: string }>;
  onClose: () => void;
  onSaved: () => void;
}) {
  const isNew = template === null;
  const [draft, setDraft] = useState<LetterTemplateCreate>(
    template
      ? {
          code: template.code,
          name: template.name,
          category: template.category,
          subject: template.subject ?? "",
          body: template.body,
          is_active: template.is_active,
          placeholders: template.placeholders ?? "",
        }
      : {
          code: "",
          name: "",
          category: "other",
          subject: "",
          body: "",
          is_active: true,
          placeholders: "",
        },
  );

  const save = useMutation({
    mutationFn: async () => {
      if (isNew) {
        await letterTemplatesApi.create(draft);
      } else if (template) {
        await letterTemplatesApi.update(template.id, {
          name: draft.name,
          category: draft.category,
          subject: draft.subject,
          body: draft.body,
          is_active: draft.is_active,
          placeholders: draft.placeholders,
        });
      }
    },
    onSuccess: () => {
      toast.success(isNew ? "Template added" : "Template saved");
      onSaved();
    },
    onError: () => toast.error("Could not save"),
  });

  const usedHints = useMemo(() => {
    return hints.filter((h) =>
      draft.body.includes(`{{${h.key}}}`) ||
      (draft.subject ?? "").includes(`{{${h.key}}}`),
    );
  }, [hints, draft.body, draft.subject]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <Card className="w-full max-w-3xl max-h-[92vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>
              {isNew ? "New letter template" : `Edit · ${template?.name}`}
            </CardTitle>
            <CardDescription>
              Insert <code className="font-mono text-xs">{`{{first_name}}`}</code>,{" "}
              <code className="font-mono text-xs">{`{{employee_code}}`}</code> etc.
              anywhere in the subject or body — they&apos;ll be filled in at
              generation time.
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid sm:grid-cols-3 gap-3">
            <div>
              <Label>Code</Label>
              <Input
                value={draft.code}
                onChange={(e) =>
                  setDraft({ ...draft, code: e.target.value })
                }
                disabled={!isNew}
                placeholder="offer_letter"
              />
            </div>
            <div>
              <Label>Name</Label>
              <Input
                value={draft.name}
                onChange={(e) =>
                  setDraft({ ...draft, name: e.target.value })
                }
                placeholder="Offer Letter"
              />
            </div>
            <div>
              <Label>Category</Label>
              <select
                value={draft.category}
                onChange={(e) =>
                  setDraft({ ...draft, category: e.target.value })
                }
                className="w-full bg-transparent border border-brand-brown-50 rounded-md px-3 py-2 text-sm"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <Label>Subject (optional, supports placeholders)</Label>
            <Input
              value={draft.subject ?? ""}
              onChange={(e) =>
                setDraft({ ...draft, subject: e.target.value })
              }
              placeholder="Subject: Offer of Employment"
            />
          </div>

          <div>
            <Label>Body</Label>
            <textarea
              rows={18}
              value={draft.body}
              onChange={(e) =>
                setDraft({ ...draft, body: e.target.value })
              }
              className="w-full bg-transparent border border-brand-brown-50 rounded-md p-3 text-sm font-mono leading-relaxed"
              placeholder="Dear {{first_name}}, ..."
            />
          </div>

          <details className="text-xs">
            <summary className="cursor-pointer text-brand-gold-dark font-mono uppercase tracking-[0.2em]">
              Available placeholders ({hints.length})
            </summary>
            <div className="mt-2 grid grid-cols-2 sm:grid-cols-3 gap-1.5">
              {hints.map((h) => {
                const used = usedHints.includes(h);
                return (
                  <code
                    key={h.key}
                    className={
                      "rounded border px-2 py-1 text-[11px] " +
                      (used
                        ? "border-brand-gold-dark text-brand-gold-dark"
                        : "border-brand-brown-50 text-brand-brown-light")
                    }
                    title={h.description}
                  >{`{{${h.key}}}`}</code>
                );
              })}
            </div>
          </details>

          <label className="flex items-center gap-2 text-xs">
            <input
              type="checkbox"
              checked={draft.is_active ?? true}
              onChange={(e) =>
                setDraft({ ...draft, is_active: e.target.checked })
              }
            />
            Active (employees and HR can generate this letter)
          </label>

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={() => save.mutate()}
              disabled={save.isPending || !draft.name || !draft.body || !draft.code}
            >
              <Save className="h-4 w-4 mr-1" />
              {save.isPending ? "Saving…" : "Save"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
