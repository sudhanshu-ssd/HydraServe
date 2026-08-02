import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../../api/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { OverviewCards } from './OverviewCards';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export function Dashboard() {
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardApi.getOverview,
  });

  const { data: reqTrend } = useQuery({
    queryKey: ['dashboard', 'reqTrend'],
    queryFn: dashboardApi.getRequestTrend,
  });

  const { data: tokTrend } = useQuery({
    queryKey: ['dashboard', 'tokTrend'],
    queryFn: dashboardApi.getTokenTrend,
  });

  const { data: modelUsage } = useQuery({
    queryKey: ['dashboard', 'modelUsage'],
    queryFn: dashboardApi.getModelUsage,
  });

  const { data: history } = useQuery({
    queryKey: ['dashboard', 'history'],
    queryFn: dashboardApi.getRequestHistory,
  });

  return (
    <div className="flex-1 space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Overview of your gateway performance</p>
      </div>

      <OverviewCards data={overview} isLoading={overviewLoading} />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader>
            <CardTitle>Request & Token Trends</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={reqTrend || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="day" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #ffffff15', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="requests" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Requests" />
                <Line type="monotone" dataKey="tokens" data={tokTrend || []} stroke="#f59e0b" strokeWidth={2} dot={false} name="Tokens" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="col-span-3 bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader>
            <CardTitle>Model Usage</CardTitle>
          </CardHeader>
          <CardContent className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={modelUsage || []} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" horizontal={false} />
                <XAxis type="number" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis type="category" dataKey="model" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} width={100} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #ffffff15', borderRadius: '8px' }}
                />
                <Bar dataKey="requests" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
        <CardHeader>
          <CardTitle>Recent Requests</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-muted-foreground">
              <thead className="text-xs uppercase bg-white/[0.02] text-foreground">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Time</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Latency</th>
                  <th className="px-4 py-3">Tokens</th>
                  <th className="px-4 py-3 rounded-tr-lg">Status</th>
                </tr>
              </thead>
              <tbody>
                {history?.map((log, i) => (
                  <tr key={i} className="border-b border-white/[0.04] hover:bg-white/[0.01]">
                    <td className="px-4 py-3">{new Date(log.request_time).toLocaleString()}</td>
                    <td className="px-4 py-3 font-medium text-foreground">{log.model}</td>
                    <td className="px-4 py-3">{log.provider}</td>
                    <td className="px-4 py-3">{log.latency.toFixed(2)}s</td>
                    <td className="px-4 py-3">{log.tokens}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        log.status === 'success' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-destructive/10 text-destructive'
                      }`}>
                        {log.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {history?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      No recent requests found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
