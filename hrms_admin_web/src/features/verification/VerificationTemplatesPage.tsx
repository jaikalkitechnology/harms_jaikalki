import { useQuery } from "@tanstack/react-query";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { verificationApi } from "@/lib/api/verification";

export default function VerificationTemplatesPage() {
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["verification-templates"],
    queryFn: verificationApi.templates,
  });

  if (isLoading) return <LoadingScreen label="Loading templates…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Verification Templates
        </h1>
        <p className="text-sm text-brand-brown-light">
          JSON-driven templates power the field employee's dynamic form.
          The full no-code editor ships in Phase 11.5; until then, templates
          are seeded or created via API.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {templates.map((t) => (
          <Card key={t.id}>
            <CardHeader>
              <CardTitle className="text-base">{t.name}</CardTitle>
              <CardDescription className="font-mono text-xs">
                {t.code} · {t.type} · SLA {t.sla_hours}h
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {t.description && (
                <p className="text-brand-brown-light">{t.description}</p>
              )}
              <div>
                <div className="text-xs font-semibold uppercase text-brand-gold-dark">
                  Fields ({t.fields.length})
                </div>
                <ul className="mt-1 space-y-1">
                  {t.fields.map((f) => (
                    <li key={f.key} className="text-xs flex items-center gap-1">
                      <span className="font-mono">{f.key}</span>
                      <span className="text-brand-brown-light">
                        ({f.field_type})
                      </span>
                      {f.required && (
                        <span className="text-error">*</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
              {t.photo_requirements && t.photo_requirements.length > 0 && (
                <div>
                  <div className="text-xs font-semibold uppercase text-brand-gold-dark">
                    Photos ({t.photo_requirements.length})
                  </div>
                  <ul className="mt-1 space-y-1">
                    {t.photo_requirements.map((p) => (
                      <li key={p.key} className="text-xs">
                        {p.label}
                        {p.required && <span className="text-error">*</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {t.signature_required && (
                <div className="text-xs text-brand-gold-dark">
                  Signature required
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
