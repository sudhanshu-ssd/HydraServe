import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '../../api/projects';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { FolderKanban, Plus, Edit2, Trash2 } from 'lucide-react';
import { ProjectDialog } from './ProjectDialog';
import { ApiKeys } from './ApiKeys';
import type { Project } from '../../types';

export function Projects() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  });

  const deleteMutation = useMutation({
    mutationFn: projectsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setSelectedProjectId(null);
    },
  });

  const handleEdit = (p: Project) => {
    setEditingProject(p);
    setDialogOpen(true);
  };

  const handleCreate = () => {
    setEditingProject(null);
    setDialogOpen(true);
  };

  return (
    <div className="flex flex-col md:flex-row gap-6 h-[calc(100vh-6rem)]">
      {/* Left sidebar - Project List */}
      <div className="w-full md:w-1/3 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Projects</h2>
            <p className="text-sm text-muted-foreground">Manage your workspaces</p>
          </div>
          <Button onClick={handleCreate} size="sm" className="bg-primary hover:bg-primary/90">
            <Plus className="mr-2 h-4 w-4" /> New
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Card key={i} className="bg-card/30 border-white/[0.04] h-24 animate-pulse" />
              ))}
            </div>
          ) : (
            projects?.map((p) => (
              <Card
                key={p.project_id}
                className={`cursor-pointer transition-colors border-white/[0.04] ${
                  selectedProjectId === p.project_id
                    ? 'bg-primary/10 border-primary/30'
                    : 'bg-card/50 hover:bg-white/[0.02]'
                }`}
                onClick={() => setSelectedProjectId(p.project_id)}
              >
                <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between">
                  <div className="flex items-center gap-2">
                    <FolderKanban className="h-4 w-4 text-primary" />
                    <CardTitle className="text-base">{p.name}</CardTitle>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        handleEdit(p);
                      }}
                    >
                      <Edit2 className="h-3 w-3 text-muted-foreground" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 hover:bg-destructive/10 hover:text-destructive"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        if (confirm('Are you sure you want to delete this project?')) {
                          deleteMutation.mutate(p.project_id);
                        }
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-0">
                  <CardDescription className="line-clamp-2 text-xs">
                    {p.description || 'No description provided'}
                  </CardDescription>
                </CardContent>
              </Card>
            ))
          )}
          {projects?.length === 0 && !isLoading && (
            <div className="text-center py-12 text-muted-foreground bg-card/20 rounded-lg border border-dashed border-white/[0.1]">
              No projects found. Create one to get started.
            </div>
          )}
        </div>
      </div>

      {/* Right panel - API Keys for selected project */}
      <div className="w-full md:w-2/3">
        {selectedProjectId ? (
          <div className="h-full flex flex-col">
            <h3 className="text-xl font-bold tracking-tight mb-2">Project Details</h3>
            <ApiKeys projectId={selectedProjectId} />
          </div>
        ) : (
          <div className="h-full flex items-center justify-center border border-dashed border-white/[0.1] rounded-xl bg-card/10">
            <div className="text-center text-muted-foreground space-y-2">
              <FolderKanban className="h-10 w-10 mx-auto opacity-20" />
              <p>Select a project from the list to view its API keys</p>
            </div>
          </div>
        )}
      </div>

      <ProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        project={editingProject}
      />
    </div>
  );
}
