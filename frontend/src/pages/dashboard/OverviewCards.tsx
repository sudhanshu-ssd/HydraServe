import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Activity, Key, LayoutDashboard, Zap, Clock, ShieldCheck, Database } from 'lucide-react';
import type { DashboardOverview } from '../../types';

interface OverviewCardsProps {
  data?: DashboardOverview;
  isLoading: boolean;
}

export function OverviewCards({ data, isLoading }: OverviewCardsProps) {
  const cards = [
    {
      title: 'Total Projects',
      value: data?.projects || 0,
      icon: LayoutDashboard,
      color: 'text-blue-500',
    },
    {
      title: 'Active API Keys',
      value: data?.api_keys || 0,
      icon: Key,
      color: 'text-amber-500',
    },
    {
      title: 'Requests Today',
      value: data?.requests_today || 0,
      icon: Activity,
      color: 'text-emerald-500',
    },
    {
      title: 'Tokens Today',
      value: data?.tokens_today || 0,
      icon: Zap,
      color: 'text-purple-500',
    },
    {
      title: 'Avg Latency',
      value: `${data?.avg_latency?.toFixed(2) || 0}s`,
      icon: Clock,
      color: 'text-pink-500',
    },
    {
      title: 'Cache Hit Rate',
      value: `${(data?.cache_hit_rate || 0).toFixed(1)}%`,
      icon: Database,
      color: 'text-cyan-500',
    },
    {
      title: 'Success Rate',
      value: `${(data?.success_rate || 0).toFixed(1)}%`,
      icon: ShieldCheck,
      color: 'text-green-500',
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">
      {cards.map((card, i) => (
        <Card key={i} className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
            <card.icon className={`h-4 w-4 ${card.color}`} />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-7 w-16 animate-pulse rounded-md bg-white/10" />
            ) : (
              <div className="text-2xl font-bold">{card.value}</div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
