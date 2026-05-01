import { useQuery } from "@tanstack/react-query";
import { Crown, Flame, Medal } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { LoadingScreen } from "@/components/shared/LoadingScreen";
import { lmsApi } from "@/lib/api/lms";

const TIER_COLOR: Record<string, string> = {
  bronze: "text-amber-700",
  silver: "text-slate-500",
  gold: "text-brand-gold-dark",
  platinum: "text-info",
};

export default function LeaderboardPage() {
  const { data: rows = [], isLoading } = useQuery({
    queryKey: ["lms-leaderboard"],
    queryFn: lmsApi.leaderboard,
  });

  if (isLoading) return <LoadingScreen label="Loading leaderboard…" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-brand-brown-darker">
          Learning Leaderboard
        </h1>
        <p className="text-sm text-brand-brown-light">
          Top learners by points across the company.
        </p>
      </div>

      {rows.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-brand-brown-light">
            No learning activity yet.
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Top {rows.length} learners</CardTitle>
            <CardDescription>
              Bronze · Silver · Gold · Platinum tiers · streak bonuses for daily
              activity
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead className="bg-brand-brown-50/40 text-left">
                <tr>
                  <th className="px-4 py-3 w-12">#</th>
                  <th className="px-4 py-3">Employee</th>
                  <th className="px-4 py-3 text-right">Points</th>
                  <th className="px-4 py-3 text-right">Courses</th>
                  <th className="px-4 py-3">Streak</th>
                  <th className="px-4 py-3">Level</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr
                    key={r.employee_id}
                    className="border-t border-brand-brown-50"
                  >
                    <td className="px-4 py-3">
                      {i === 0 ? (
                        <Crown className="size-4 text-brand-gold-dark" />
                      ) : i < 3 ? (
                        <Medal className="size-4 text-brand-gold-dark" />
                      ) : (
                        i + 1
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <div className="font-medium">{r.name}</div>
                      <div className="text-xs text-brand-brown-light">
                        {r.employee_code}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right font-semibold">
                      {r.points}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {r.courses_completed}
                    </td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1">
                        <Flame className="size-4 text-warning" />
                        {r.streak_days}d
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`uppercase font-semibold text-xs ${TIER_COLOR[r.level] ?? ""}`}
                      >
                        {r.level}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
