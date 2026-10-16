// Company policies — HR uploads policy documents; published ones are
// visible to every employee in the app under More → Documents.
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { FileCheck2, FileUp, Pencil, Plus, Trash2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { PermissionGate } from "@/components/shared/PermissionGate";
import {
  POLICY_CATEGORIES,
  fmtBytes,
  hrDocumentsApi,
  policyCategoryLabel,
  type CompanyPolicy,
  type PolicyCategory,
} from "@/lib/api/hrDocuments";
import { Modal } from "@/features/polish/assets/AssetDialogs";
import {
  Chip,
  Field,
  FormActions,
  SELECT_CLASS,
  errDetail,
  fmtDate,
} from "@/features/employees/profile/ui";

const ACCEPT = "application/pdf,image/jpeg,image/png,image/webp";

export default function PoliciesPage() {
  const { data: policies = [], isLoading } = useQuery({
    queryKey: ["company-policies"],
    queryFn: hrDocumentsApi.policies,
  });
  const [editing, setEditing] = useState<CompanyPolicy | "new" | null>(null);
  const [replacing, setReplacing] = useState<CompanyPolicy | null>(null);

  if (isLoading) return <LoadingScreen />;
  const published = policies.filter((p) => p.is_published).length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileCheck2 className="h-5 w-5" /> Company policies
            </CardTitle>
            <CardDescription className="mt-1">
              Upload policy documents — leave policy, code of conduct, IT policy and so
              on. Published policies are visible to everyone in the app under{" "}
              <strong>More → Documents</strong>, and employees get a notification
              when one is published.
            </CardDescription>
          </div>
          <PermissionGate permission="employee.update">
            <Button className="shrink-0 gap-2" onClick={() => setEditing("new")}>
              <Plus className="size-4" /> Upload policy
            </Button>
          </PermissionGate>
        </CardHeader>
        <CardContent>
          <div className="mb-3 text-sm text-brand-brown-light">
            {policies.length} {policies.length === 1 ? "policy" : "policies"} · {published} published
          </div>
          {policies.length === 0 ? (
            <div className="rounded-lg border border-dashed border-brand-brown-100 px-4 py-8 text-center text-sm text-brand-brown-light">
              No policies yet. Upload the first one and it appears in everyone's app.
            </div>
          ) : (
            <ul className="divide-y divide-brand-brown-50">
              {policies.map((p) => (
                <PolicyRow
                  key={p.id}
                  policy={p}
                  onEdit={() => setEditing(p)}
                  onReplace={() => setReplacing(p)}
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {editing && (
        <PolicyModal
          policy={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
        />
      )}
      {replacing && <ReplaceFileModal policy={replacing} onClose={() => setReplacing(null)} />}
    </div>
  );
}

function PolicyRow({
  policy: p,
  onEdit,
  onReplace,
}: {
  policy: CompanyPolicy;
  onEdit: () => void;
  onReplace: () => void;
}) {
  const qc = useQueryClient();
  const refresh = () => qc.invalidateQueries({ queryKey: ["company-policies"] });
  const publish = useMutation({
    mutationFn: () => hrDocumentsApi.updatePolicy(p.id, { is_published: !p.is_published }),
    onSuccess: (u) => {
      toast.success(u.is_published ? "Published — everyone can see it" : "Unpublished — hidden from employees");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not change")),
  });
  const remove = useMutation({
    mutationFn: () => hrDocumentsApi.deletePolicy(p.id),
    onSuccess: () => {
      toast.success("Policy deleted");
      refresh();
    },
    onError: (e) => toast.error(errDetail(e, "Could not delete")),
  });

  return (
    <li className="flex flex-wrap items-center gap-3 py-3">
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium text-brand-brown-darker">{p.title}</span>
          <Chip tone="gold">{policyCategoryLabel(p.category)}</Chip>
          {p.version && <Chip>{p.version}</Chip>}
          {p.is_published ? <Chip tone="success">Published</Chip> : <Chip tone="warning">Draft</Chip>}
        </div>
        {p.description && (
          <p className="mt-1 line-clamp-2 text-sm text-brand-brown-light">{p.description}</p>
        )}
        <div className="mt-0.5 text-xs text-brand-brown-light">
          {[
            p.effective_date && `Effective ${fmtDate(p.effective_date)}`,
            p.file_name,
            fmtBytes(p.file_size),
            p.updated_at && `Updated ${fmtDate(p.updated_at)}`,
          ]
            .filter(Boolean)
            .join(" · ")}
        </div>
      </div>
      <div className="flex shrink-0 flex-wrap items-center gap-1">
        <Button asChild variant="outline" size="sm">
          <a href={hrDocumentsApi.policyFileUrl(p.id)} target="_blank" rel="noreferrer">
            Open
          </a>
        </Button>
        <PermissionGate permission="employee.update">
          <Button
            variant="outline"
            size="sm"
            disabled={publish.isPending}
            onClick={() => publish.mutate()}
          >
            {p.is_published ? "Unpublish" : "Publish"}
          </Button>
          <Button variant="ghost" size="sm" aria-label="Edit details" title="Edit details" onClick={onEdit}>
            <Pencil className="size-4" />
          </Button>
          <Button variant="ghost" size="sm" aria-label="Upload new version" title="Upload new version" onClick={onReplace}>
            <FileUp className="size-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-error"
            aria-label="Delete policy"
            disabled={remove.isPending}
            onClick={() => {
              if (window.confirm(`Delete "${p.title}"? Employees will no longer see it.`)) remove.mutate();
            }}
          >
            <Trash2 className="size-4" />
          </Button>
        </PermissionGate>
      </div>
    </li>
  );
}

function PolicyModal({ policy, onClose }: { policy: CompanyPolicy | null; onClose: () => void }) {
  const qc = useQueryClient();
  const [title, setTitle] = useState(policy?.title ?? "");
  const [category, setCategory] = useState<PolicyCategory>(policy?.category ?? "hr");
  const [description, setDescription] = useState(policy?.description ?? "");
  const [version, setVersion] = useState(policy?.version ?? "");
  const [effective, setEffective] = useState(policy?.effective_date ?? "");
  const [published, setPublished] = useState(policy?.is_published ?? true);
  const [file, setFile] = useState<File | null>(null);

  const save = useMutation({
    mutationFn: () => {
      const fields = {
        title: title.trim(),
        category,
        description: description.trim(),
        version: version.trim(),
        effective_date: effective || undefined,
        is_published: published,
      };
      return policy
        ? hrDocumentsApi.updatePolicy(policy.id, {
            ...fields,
            description: fields.description || null,
            version: fields.version || null,
            effective_date: effective || null,
          })
        : hrDocumentsApi.createPolicy(fields, file!);
    },
    onSuccess: (p) => {
      toast.success(
        policy ? "Policy updated" : p.is_published ? "Policy published to everyone" : "Policy saved as draft",
      );
      qc.invalidateQueries({ queryKey: ["company-policies"] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not save")),
  });

  return (
    <Modal
      title={policy ? "Edit policy" : "Upload policy"}
      description={policy ? undefined : "PDF, JPG, PNG or WEBP, up to 10 MB."}
      onClose={onClose}
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Title" className="col-span-full">
          <Input
            value={title}
            maxLength={200}
            placeholder="e.g. Leave Policy 2026"
            onChange={(e) => setTitle(e.target.value)}
          />
        </Field>
        <Field label="Category">
          <select
            className={SELECT_CLASS}
            value={category}
            onChange={(e) => setCategory(e.target.value as PolicyCategory)}
          >
            {POLICY_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {policyCategoryLabel(c)}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Version (optional)">
          <Input value={version} maxLength={32} placeholder="v1.0" onChange={(e) => setVersion(e.target.value)} />
        </Field>
        <Field label="Effective from (optional)">
          <Input type="date" value={effective} onChange={(e) => setEffective(e.target.value)} />
        </Field>
        <Field label="Summary (optional)" className="col-span-full">
          <textarea
            className="flex w-full rounded-md border border-input bg-card px-3 py-2 text-sm"
            rows={3}
            maxLength={4000}
            value={description}
            placeholder="What changed, who it applies to…"
            onChange={(e) => setDescription(e.target.value)}
          />
        </Field>
        {!policy && (
          <Field label="File" className="col-span-full">
            <Input type="file" accept={ACCEPT} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </Field>
        )}
        <label className="col-span-full flex items-center gap-2 text-sm">
          <input type="checkbox" checked={published} onChange={(e) => setPublished(e.target.checked)} />
          Published — visible to all employees
        </label>
        <FormActions
          onCancel={onClose}
          onSave={() => save.mutate()}
          saving={save.isPending}
          disabled={title.trim().length < 2 || (!policy && !file)}
          saveLabel={policy ? "Save" : "Upload"}
        />
      </div>
    </Modal>
  );
}

function ReplaceFileModal({ policy, onClose }: { policy: CompanyPolicy; onClose: () => void }) {
  const qc = useQueryClient();
  const [file, setFile] = useState<File | null>(null);
  const [version, setVersion] = useState("");
  const replace = useMutation({
    mutationFn: () => hrDocumentsApi.replacePolicyFile(policy.id, file!, version.trim() || undefined),
    onSuccess: () => {
      toast.success("New version uploaded");
      qc.invalidateQueries({ queryKey: ["company-policies"] });
      onClose();
    },
    onError: (e) => toast.error(errDetail(e, "Could not upload")),
  });
  return (
    <Modal
      title="Upload new version"
      description={`Replaces the document for “${policy.title}”. Employees see the new file straight away.`}
      onClose={onClose}
    >
      <div className="grid gap-4">
        <Field label="File">
          <Input type="file" accept={ACCEPT} onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </Field>
        <Field label="New version label (optional)" help={policy.version ? `Currently ${policy.version}` : undefined}>
          <Input value={version} maxLength={32} placeholder="v2.0" onChange={(e) => setVersion(e.target.value)} />
        </Field>
        <FormActions
          onCancel={onClose}
          onSave={() => replace.mutate()}
          saving={replace.isPending}
          disabled={!file}
          saveLabel="Upload"
        />
      </div>
    </Modal>
  );
}
