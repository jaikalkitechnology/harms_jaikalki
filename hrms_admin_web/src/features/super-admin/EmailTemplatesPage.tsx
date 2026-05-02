import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Mail, Plus, Save, Send, Trash2 } from "lucide-react";

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
import { superAdminApi, type EmailTemplate } from "@/lib/api/super-admin";

export default function EmailTemplatesPage() {
  const { data = [], isLoading } = useQuery({
    queryKey: ["email-templates"],
    queryFn: superAdminApi.listEmailTemplates,
  });
  const [activeId, setActiveId] = useState<number | null>(null);
  const active = (data as EmailTemplate[]).find((t) => t.id === activeId) ?? null;

  if (isLoading) return <LoadingScreen />;

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="md:col-span-1 space-y-3">
        <NewTemplate />
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5" /> Templates
            </CardTitle>
            <CardDescription>{data.length} templates</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            {(data as EmailTemplate[]).map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveId(t.id)}
                className={`w-full text-left px-4 py-2 border-b border-brand-brown-50 hover:bg-brand-brown-50 ${
                  activeId === t.id ? "bg-brand-brown-50" : ""
                }`}
              >
                <div className="text-sm font-medium">{t.name}</div>
                <div className="text-xs text-brand-brown-light font-mono">
                  {t.code} · {t.is_active ? "active" : "draft"}
                </div>
              </button>
            ))}
          </CardContent>
        </Card>
      </div>

      <div className="md:col-span-2">
        {active ? (
          <Editor key={active.id} template={active} />
        ) : (
          <Card>
            <CardContent className="py-12 text-center text-brand-brown-light">
              Select a template to edit
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function NewTemplate() {
  const qc = useQueryClient();
  const [draft, setDraft] = useState({
    code: "",
    name: "",
    subject: "",
    body_html: "",
  });
  const create = useMutation({
    mutationFn: () =>
      superAdminApi.createEmailTemplate({
        ...draft,
        variables: [],
        is_active: true,
      }),
    onSuccess: () => {
      toast.success("Template created");
      setDraft({ code: "", name: "", subject: "", body_html: "" });
      qc.invalidateQueries({ queryKey: ["email-templates"] });
    },
    onError: () => toast.error("Could not create template"),
  });
  return (
    <Card>
      <CardHeader>
        <CardTitle>New template</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <Input
          placeholder="code (e.g. welcome_email)"
          value={draft.code}
          onChange={(e) => setDraft({ ...draft, code: e.target.value })}
        />
        <Input
          placeholder="Name"
          value={draft.name}
          onChange={(e) => setDraft({ ...draft, name: e.target.value })}
        />
        <Input
          placeholder="Subject"
          value={draft.subject}
          onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
        />
        <textarea
          placeholder="<p>HTML body…</p>"
          rows={4}
          className="w-full border border-brand-brown-50 rounded p-2 text-sm font-mono"
          value={draft.body_html}
          onChange={(e) => setDraft({ ...draft, body_html: e.target.value })}
        />
        <Button
          disabled={
            !draft.code || !draft.name || !draft.subject || !draft.body_html
          }
          onClick={() => create.mutate()}
        >
          <Plus className="h-4 w-4 mr-1" /> Create
        </Button>
      </CardContent>
    </Card>
  );
}

function Editor({ template }: { template: EmailTemplate }) {
  const qc = useQueryClient();
  const [draft, setDraft] = useState<EmailTemplate>(template);
  const [testEmail, setTestEmail] = useState("");
  const [testVars, setTestVars] = useState("{}");

  useEffect(() => setDraft(template), [template.id]);

  const save = useMutation({
    mutationFn: () =>
      superAdminApi.updateEmailTemplate(template.id, {
        name: draft.name,
        subject: draft.subject,
        body_html: draft.body_html,
        body_text: draft.body_text,
        variables: draft.variables ?? [],
        is_active: draft.is_active,
      }),
    onSuccess: () => {
      toast.success("Saved");
      qc.invalidateQueries({ queryKey: ["email-templates"] });
    },
  });
  const remove = useMutation({
    mutationFn: () => superAdminApi.deleteEmailTemplate(template.id),
    onSuccess: () => {
      toast.success("Deleted");
      qc.invalidateQueries({ queryKey: ["email-templates"] });
    },
  });
  const test = useMutation({
    mutationFn: () =>
      superAdminApi.testEmailTemplate(template.id, {
        to_email: testEmail,
        sample_variables: (() => {
          try {
            return JSON.parse(testVars);
          } catch {
            return {};
          }
        })(),
      }),
    onSuccess: () => toast.success("Test sent"),
    onError: () => toast.error("Test failed"),
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>{template.name}</CardTitle>
          <CardDescription className="font-mono">
            {template.code}
          </CardDescription>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              if (confirm(`Delete "${template.name}"?`)) remove.mutate();
            }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button size="sm" onClick={() => save.mutate()}>
            <Save className="h-4 w-4 mr-1" /> Save
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <Label>Subject</Label>
          <Input
            value={draft.subject}
            onChange={(e) => setDraft({ ...draft, subject: e.target.value })}
          />
        </div>
        <div>
          <Label>HTML body (use {"{{variable}}"} placeholders)</Label>
          <textarea
            rows={10}
            className="w-full border border-brand-brown-50 rounded p-2 text-sm font-mono"
            value={draft.body_html}
            onChange={(e) =>
              setDraft({ ...draft, body_html: e.target.value })
            }
          />
        </div>
        <div>
          <Label>Plain-text body (optional)</Label>
          <textarea
            rows={3}
            className="w-full border border-brand-brown-50 rounded p-2 text-sm"
            value={draft.body_text ?? ""}
            onChange={(e) =>
              setDraft({ ...draft, body_text: e.target.value })
            }
          />
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={draft.is_active}
            onChange={(e) =>
              setDraft({ ...draft, is_active: e.target.checked })
            }
          />{" "}
          Active
        </label>

        <div className="border-t border-brand-brown-50 pt-3">
          <div className="font-medium text-sm mb-2">Send test</div>
          <div className="grid md:grid-cols-2 gap-2">
            <Input
              placeholder="recipient@example.com"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
            />
            <Input
              placeholder='{"name":"Alice"}'
              value={testVars}
              onChange={(e) => setTestVars(e.target.value)}
            />
          </div>
          <Button
            className="mt-2"
            disabled={!testEmail}
            onClick={() => test.mutate()}
          >
            <Send className="h-4 w-4 mr-1" /> Send test
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
