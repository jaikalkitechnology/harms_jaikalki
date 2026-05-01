import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, XCircle, ShieldCheck } from "lucide-react";

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
import { examApi, type CertificateVerifyResponse } from "@/lib/api/exam";

export default function CertificateVerifyPage() {
  const [number, setNumber] = useState("");
  const [result, setResult] = useState<CertificateVerifyResponse | null>(null);

  const verify = useMutation({
    mutationFn: () => examApi.verify(number.trim()),
    onSuccess: (r) => setResult(r),
    onError: () => setResult({
      valid: false,
      certificate_number: number,
      employee_name: null,
      title: null,
      issued_date: null,
      expiry_date: null,
      score_percentage: null,
      is_revoked: false,
      revoked_reason: null,
    }),
  });

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Certificate Verification
        </h1>
        <p className="text-sm text-brand-brown-light">
          Paste any Jaikalki certificate number to verify its authenticity.
        </p>
      </div>

      <Card>
        <CardContent className="pt-6 space-y-3">
          <div>
            <Label>Certificate number</Label>
            <Input
              placeholder="JKT/CERT/2026/XXXXXXXX"
              value={number}
              onChange={(e) => setNumber(e.target.value)}
            />
          </div>
          <Button
            disabled={!number.trim() || verify.isPending}
            onClick={() => verify.mutate()}
            className="gap-2"
          >
            <ShieldCheck className="size-4" />
            Verify
          </Button>
        </CardContent>
      </Card>

      {result && (
        <Card
          className={
            result.valid
              ? "border-success"
              : "border-error"
          }
        >
          <CardHeader>
            <div className="flex items-center gap-2">
              {result.valid ? (
                <CheckCircle2 className="size-6 text-success" />
              ) : (
                <XCircle className="size-6 text-error" />
              )}
              <CardTitle>
                {result.valid ? "Valid certificate" : "Not valid"}
              </CardTitle>
            </div>
            <CardDescription className="font-mono">
              {result.certificate_number}
            </CardDescription>
          </CardHeader>
          {result.valid && (
            <CardContent className="space-y-2 text-sm">
              <div>
                <span className="text-brand-brown-light">Holder: </span>
                <span className="font-medium">
                  {result.employee_name ?? "—"}
                </span>
              </div>
              <div>
                <span className="text-brand-brown-light">Title: </span>
                {result.title}
              </div>
              <div>
                <span className="text-brand-brown-light">Issued: </span>
                {result.issued_date}
              </div>
              <div>
                <span className="text-brand-brown-light">Expires: </span>
                {result.expiry_date ?? "no expiry"}
              </div>
              {result.score_percentage && (
                <div>
                  <span className="text-brand-brown-light">Score: </span>
                  {result.score_percentage}%
                </div>
              )}
            </CardContent>
          )}
          {result.is_revoked && (
            <CardContent className="text-sm text-error">
              REVOKED · {result.revoked_reason ?? "no reason given"}
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
