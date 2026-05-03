import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Bell, Check, CheckCheck } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { launchApi } from "@/lib/api/launch";
import { fmtIst } from "@/lib/datetime";

export default function NotificationsPage() {
  const qc = useQueryClient();
  const { data: items = [], isLoading } = useQuery({
    queryKey: ["my-notifications"],
    queryFn: () => launchApi.myNotifications(false),
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

  if (isLoading) return <LoadingScreen label="Loading notifications…" />;

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-brand-brown-darker">
            Notifications
          </h1>
          <p className="text-sm text-brand-brown-light">
            {items.length} item{items.length === 1 ? "" : "s"}.
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
  );
}
