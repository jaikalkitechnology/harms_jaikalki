import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bell, Check, CheckCheck, Send } from "lucide-react";

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
import { launchApi } from "@/lib/api/launch";
import { employeesApi } from "@/lib/api/employees";
import { fmtIst } from "@/lib/datetime";

const ROLE_CODES = [
  "super_admin",
  "director",
  "hr",
  "admin",
  "manager",
  "employee",
  "trainer",
  "field",
  "intern",
];

type Audience = "all" | "role" | "department" | "users";

export default function NotificationsPage() {
  const qc = useQueryClient();

  const [audience, setAudience] = useState<Audience>("all");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [sendPush, setSendPush] = useState(true);
  const [roleCode, setRoleCode] = useState("");
  const [departmentId, setDepartmentId] = useState<number | "">("");
  const [userIds, setUserIds] = useState<number[]>([]);

  const { data: items = [], isLoading } = useQuery({
    queryKey: ["my-notifications"],
    queryFn: () => launchApi.myNotifications(false),
  });
  const { data: employees = [] } = useQuery({
    queryKey: ["employees-all"],
    queryFn: () => employeesApi.list(),
  });

  const markRead = useMutation({
    mutationFn: (id: number) => launchApi.markRead(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });
  const markAll = useMutation({
    mutationFn: () => launchApi.markAllRead(),
    onSuccess: (n) => {
      toast.success(`${n} marked as read`);
      qc.invalidateQueries({ queryKey: ["my-notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });

  const broadcast = useMutation({
    mutationFn: () =>
      launchApi.broadcast({
        audience,
        title,
        body: body || null,
        send_push: sendPush,
        role_codes: audience === "role" && roleCode ? [roleCode] : undefined,
        department_id:
          audience === "department" && departmentId !== ""
            ? Number(departmentId)
            : undefined,
        user_ids: audience === "users" ? userIds : undefined,
      }),
    onSuccess: (r) => {
      toast.success(`Sent to ${r.sent} of ${r.queued} recipients`);
      setTitle("");
      setBody("");
      setUserIds([]);
      qc.invalidateQueries({ queryKey: ["my-notifications"] });
    },
    onError: (e: any) =>
      toast.error(e?.response?.data?.detail ?? "Could not broadcast"),
  });

  const canSend =
    !!title.trim() &&
    (audience !== "role" || !!roleCode) &&
    (audience !== "department" || departmentId !== "") &&
    (audience !== "users" || userIds.length > 0);

  if (isLoading) return <LoadingScreen label="Loading notifications…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Notifications
          </h1>
          <p className="text-sm text-brand-brown-light">
            Compose and broadcast in-app + push notifications, or read your
            inbox.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => markAll.mutate()}
          disabled={markAll.isPending}
          className="gap-2"
        >
          <CheckCheck className="size-4" />
          Mark all read
        </Button>
      </div>

      {/* Compose card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Send className="size-4 text-brand-gold-dark" /> Send notification
          </CardTitle>
          <CardDescription>
            Stored as in-app + delivered via FCM push to active devices when
            "Also send push" is enabled.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2">
          <div>
            <Label>Audience</Label>
            <select
              value={audience}
              onChange={(e) => setAudience(e.target.value as Audience)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="all">Everyone</option>
              <option value="role">By role</option>
              <option value="department">By department</option>
              <option value="users">Specific employees</option>
            </select>
          </div>
          {audience === "role" && (
            <div>
              <Label>Role *</Label>
              <select
                value={roleCode}
                onChange={(e) => setRoleCode(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="">— Select —</option>
                {ROLE_CODES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>
          )}
          {audience === "department" && (
            <div>
              <Label>Department ID *</Label>
              <Input
                type="number"
                value={departmentId}
                onChange={(e) =>
                  setDepartmentId(e.target.value ? Number(e.target.value) : "")
                }
              />
            </div>
          )}
          {audience === "users" && (
            <div className="md:col-span-2">
              <Label>Recipients (employees mapped to user accounts) *</Label>
              <select
                multiple
                value={userIds.map(String)}
                onChange={(e) =>
                  setUserIds(
                    Array.from(e.target.selectedOptions).map((o) =>
                      Number(o.value),
                    ),
                  )
                }
                className="flex w-full min-h-[140px] rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                {employees
                  .filter((emp) => (emp as any).user_id)
                  .map((emp) => (
                    <option key={emp.id} value={String((emp as any).user_id)}>
                      {emp.employee_code} · {emp.first_name} {emp.last_name}
                    </option>
                  ))}
              </select>
              <p className="text-[11px] text-brand-brown-light mt-1">
                Cmd/Ctrl-click to select multiple. Only employees with linked
                user accounts can receive notifications.
              </p>
            </div>
          )}
          <div className="md:col-span-2">
            <Label>Title *</Label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Office holiday on Friday"
            />
          </div>
          <div className="md:col-span-2">
            <Label>Body</Label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={3}
              className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Details of the announcement…"
            />
          </div>
          <label className="flex items-center gap-2 text-sm md:col-span-2">
            <input
              type="checkbox"
              checked={sendPush}
              onChange={(e) => setSendPush(e.target.checked)}
            />
            Also send push (FCM) to recipients' active devices
          </label>
          <div className="md:col-span-2 flex justify-end">
            <Button
              disabled={!canSend || broadcast.isPending}
              onClick={() => broadcast.mutate()}
              className="gap-2"
            >
              <Send className="size-4" /> Send
            </Button>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-base font-semibold text-brand-brown-darker mb-2">
          Your inbox · {items.length} item{items.length === 1 ? "" : "s"}
        </h2>
        {items.length === 0 ? (
          <Card>
            <CardContent className="py-10 text-center text-brand-brown-light">
              <Bell className="mx-auto size-8 mb-2" />
              You're all caught up.
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-2">
            {items.map((n) => (
              <Card
                key={n.id}
                className={
                  n.read_at ? "opacity-70" : "border-brand-gold-dark"
                }
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">{n.title}</CardTitle>
                    {!n.read_at && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1"
                        onClick={() => markRead.mutate(n.id)}
                      >
                        <Check className="size-3" />
                        Read
                      </Button>
                    )}
                  </div>
                  <CardDescription className="text-xs">
                    {n.type} · {fmtIst(n.created_at)}
                  </CardDescription>
                </CardHeader>
                {n.body && (
                  <CardContent className="text-sm text-brand-brown-darker">
                    {n.body}
                  </CardContent>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
