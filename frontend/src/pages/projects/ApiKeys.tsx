import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../../api/projects';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table';
import { Copy, Plus, Trash2, Key } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';

export function ApiKeys({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const [newKey, setNewKey] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState('hydraserve-001');

  const { data: keys, isLoading } = useQuery({
    queryKey: ['projects', projectId, 'keys'],
    queryFn: () => projectsApi.listKeys(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (data: {name: string}) => projectsApi.createKey(projectId, data),
    onSuccess: (data) => {
      setNewKey(data.api_key);
      setNewKeyName('hydraserve-001');
      setIsCreateDialogOpen(false);
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'keys'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (keyId: number) => projectsApi.deleteKey(projectId, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'keys'] });
    },
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // Could add a toast notification here
  };

  return (
    <Card className="bg-card border-white/[0.08] mt-6">
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Manage API keys for this project</CardDescription>
        </div>
        <Button onClick={() => setIsCreateDialogOpen(true)} disabled={createMutation.isPending} size="sm">
          <Plus className="mr-2 h-4 w-4" /> Generate New Key
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="h-24 flex items-center justify-center">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-white/[0.04]">
                <TableHead>Key Name</TableHead>
                <TableHead>Created At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {keys?.map((k) => (
                <TableRow key={k.api_key_id} className="border-white/[0.04]">
                  <TableCell className="font-medium">{k.name}</TableCell>
                  <TableCell>{new Date(k.api_key_created_at).toLocaleDateString()}</TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(k.api_key_id)}
                      disabled={deleteMutation.isPending}
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {keys?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={3} className="h-32 text-center">
                    <div className="flex flex-col items-center justify-center space-y-3">
                      <div className="rounded-full bg-primary/10 p-3">
                        <Key className="h-6 w-6 text-primary" />
                      </div>
                      <div className="text-sm text-muted-foreground max-w-[250px]">
                        API keys authenticate your requests to HydraServe. Create one to get started.
                      </div>
                      <Button onClick={() => setIsCreateDialogOpen(true)} variant="outline" size="sm" className="mt-2">
                        Create API Key
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}

        {keys && keys.length > 0 && (
          <div className="mt-8 pt-6 border-t border-white/[0.04]">
            <h4 className="text-sm font-medium mb-3">How to use your API key</h4>
            <div className="bg-black/50 border border-white/[0.08] rounded-md p-4 font-mono text-xs text-muted-foreground overflow-x-auto">
              <span className="text-emerald-400">curl</span> https://hydraserve.in/chat \ <br/>
              &nbsp;&nbsp;-H <span className="text-amber-300">"Authorization: Bearer YOUR_API_KEY"</span> \ <br/>
              &nbsp;&nbsp;-H <span className="text-amber-300">"Content-Type: application/json"</span> \ <br/>
              &nbsp;&nbsp;-d <span className="text-blue-300">'{'{'}</span> <br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-300">"model"</span>: <span className="text-amber-300">"mock-llm"</span>, <br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-300">"prompt"</span>: <span className="text-amber-300">"Hello HydraServe"</span> <br/>
              &nbsp;&nbsp;<span className="text-blue-300">{'}'}'</span>
            </div>
          </div>
        )}
      </CardContent>

      <Dialog open={!!newKey} onOpenChange={() => setNewKey(null)}>
        <DialogContent className="bg-card border-white/[0.08] sm:max-w-[550px]">
          <DialogHeader>
            <DialogTitle>API Key Generated</DialogTitle>
            <DialogDescription className="font-medium mt-2">
              Please copy this key now. For security reasons, you will not be able to see it again. Store it securely in your environment variables (e.g. <code className="bg-black/50 px-1 py-0.5 rounded text-xs border border-white/10">HYDRA_API_KEY</code>).
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2 mt-2 p-3 rounded-md bg-black/50 border border-white/10 font-mono text-sm break-all">
            <span className="flex-1 select-all text-primary">{newKey}</span>
            <Button variant="ghost" size="sm" onClick={() => newKey && copyToClipboard(newKey)}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="mt-4">
            <p className="text-xs text-muted-foreground mb-2">Example usage:</p>
            <div className="bg-black/50 border border-white/[0.08] rounded-md p-4 font-mono text-xs text-muted-foreground overflow-x-auto relative group">
              <Button 
                variant="ghost" 
                size="icon" 
                className="absolute top-2 right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => {
                  const cmd = `curl https://hydraserve.in/chat \\\n  -H "Authorization: Bearer ${newKey}" \\\n  -H "Content-Type: application/json" \\\n  -d '{"model": "mock-llm", "prompt": "Hello HydraServe"}'`;
                  copyToClipboard(cmd);
                }}
              >
                <Copy className="h-3 w-3" />
              </Button>
              <span className="text-emerald-400">curl</span> https://hydraserve.in/chat \ <br/>
              &nbsp;&nbsp;-H <span className="text-amber-300">"Authorization: Bearer {newKey}"</span> \ <br/>
              &nbsp;&nbsp;-H <span className="text-amber-300">"Content-Type: application/json"</span> \ <br/>
              &nbsp;&nbsp;-d <span className="text-blue-300">'{'{'}</span> <br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-300">"model"</span>: <span className="text-amber-300">"mock-llm"</span>, <br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-blue-300">"prompt"</span>: <span className="text-amber-300">"Hello HydraServe"</span> <br/>
              &nbsp;&nbsp;<span className="text-blue-300">{'}'}'</span>
            </div>
          </div>

          <DialogFooter className="mt-6">
            <Button onClick={() => setNewKey(null)}>I've copied it</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="bg-card border-white/[0.08]">
          <DialogHeader>
            <DialogTitle>Create New API Key</DialogTitle>
            <DialogDescription>
              Enter a name to identify this API key.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Key Name</Label>
            <Input 
               value={newKeyName} 
               onChange={(e) => setNewKeyName(e.target.value)} 
               placeholder="e.g. Production Key"
               className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>Cancel</Button>
            <Button onClick={() => createMutation.mutate({ name: newKeyName })} disabled={createMutation.isPending || !newKeyName}>
              {createMutation.isPending ? "Generating..." : "Generate Key"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}
