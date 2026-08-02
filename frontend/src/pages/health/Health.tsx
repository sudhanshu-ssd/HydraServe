import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../../api/health';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Clock, Database, CheckCircle2, XCircle, Box } from 'lucide-react';

export function Health() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: healthApi.check,
    refetchInterval: 10000, // Refresh every 10s
  });

  if (isLoading) {
    return (
      <div className="h-[calc(100vh-6rem)] flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="h-[calc(100vh-6rem)] flex items-center justify-center">
        <Card className="w-[400px] border-destructive/20 bg-destructive/5 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <XCircle className="h-5 w-5" /> Gateway Offline
            </CardTitle>
            <CardDescription>Could not connect to the HydraServe backend.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const formatUptime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">System Health</h2>
        <p className="text-muted-foreground">Real-time gateway status</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Gateway Status</CardTitle>
            {data.status === 'ok' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            ) : (
              <XCircle className="h-4 w-4 text-destructive" />
            )}
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{data.status}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Version: {data.version}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-white/[0.04]">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <Clock className="h-4 w-4 text-amber-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatUptime(data.uptime_seconds)}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Since {new Date(data.timestamp).toLocaleTimeString()}
            </p>
          </CardContent>
        </Card>
      </div>

      <h3 className="text-xl font-semibold mt-8 mb-4">Dependencies</h3>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Object.entries(data.services).map(([service, status]) => (
          <Card key={service} className="bg-card/30 backdrop-blur-sm border-white/[0.02]">
            <CardHeader className="flex flex-row items-center gap-4 py-4">
              <div className={`p-2 rounded-lg ${status === 'ok' ? 'bg-emerald-500/10' : 'bg-destructive/10'}`}>
                {service.toLowerCase().includes('database') || service.toLowerCase().includes('postgres') ? (
                  <Database className={`h-5 w-5 ${status === 'ok' ? 'text-emerald-500' : 'text-destructive'}`} />
                ) : (
                  <Box className={`h-5 w-5 ${status === 'ok' ? 'text-emerald-500' : 'text-destructive'}`} />
                )}
              </div>
              <div className="flex-1">
                <CardTitle className="text-base capitalize">{service}</CardTitle>
                <CardDescription className={status === 'ok' ? 'text-emerald-500/70' : 'text-destructive/70'}>
                  {status === 'ok' ? 'Operational' : 'Degraded'}
                </CardDescription>
              </div>
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}
