import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { cn } from '../lib/utils';
import {
  LayoutDashboard,
  FolderKanban,
  MessageSquare,
  Activity,
  LogOut,
  Menu,
  X,
  Zap
} from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { userApi } from '../api/user';
import { useMutation } from '@tanstack/react-query';

const navItems = [
  { label: 'Dashboard', href: '/', icon: LayoutDashboard },
  { label: 'Projects', href: '/projects', icon: FolderKanban },
  { label: 'Playground', href: '/playground', icon: MessageSquare },
  { label: 'Health', href: '/health', icon: Activity },
];

export function DashboardLayout() {
  const { username, profilePic, logout, refreshProfile } = useAuth();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const uploadMutation = useMutation({
    mutationFn: (file: File) => userApi.uploadProfilePic(file),
    onSuccess: () => {
      refreshProfile();
      setProfileOpen(false);
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Upload failed");
    }
  });

  const deleteMutation = useMutation({
    mutationFn: () => userApi.deleteProfilePic(),
    onSuccess: () => {
      refreshProfile();
      setProfileOpen(false);
    },
  });

  const getImageUrl = (url: string | null) => {
    if (!url || url.endsWith('None')) return null;
    if (url.startsWith('s3://')) {
      const bucketAndPath = url.replace('s3://', '');
      const [bucket, ...pathParts] = bucketAndPath.split('/');
      return `https://${bucket}.s3.amazonaws.com/${pathParts.join('/')}`;
    }
    return url;
  };

  const avatarUrl = getImageUrl(profilePic);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      uploadMutation.mutate(e.target.files[0]);
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-white/[0.06] bg-card/80 backdrop-blur-xl transition-transform duration-300 lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Brand */}
        <div className="flex h-16 items-center gap-2.5 border-b border-white/[0.06] px-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600">
            <Zap className="h-4 w-4 text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-foreground">HydraServe</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href || 
              (item.href !== '/' && location.pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                to={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-white/[0.04] hover:text-foreground'
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="border-t border-white/[0.06] p-4">
          <div className="flex items-center justify-between">
            <button 
              onClick={() => setProfileOpen(true)}
              className="flex flex-1 items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-white/[0.04]"
            >
              <div className="flex h-8 w-8 overflow-hidden items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-xs font-semibold text-primary">
                {avatarUrl ? (
                  <img src={avatarUrl} alt={username || 'User'} className="h-full w-full object-cover" />
                ) : (
                  username?.charAt(0).toUpperCase() || 'U'
                )}
              </div>
              <span className="text-sm font-medium text-foreground truncate max-w-[100px]">{username}</span>
            </button>
            <button
              onClick={logout}
              className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-white/[0.04] hover:text-foreground shrink-0"
              title="Sign out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile header */}
        <header className="flex h-16 items-center border-b border-white/[0.06] px-4 lg:hidden">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-muted-foreground hover:bg-white/[0.04]"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      <Dialog open={profileOpen} onOpenChange={setProfileOpen}>
        <DialogContent className="bg-card/95 backdrop-blur-xl border-white/[0.08] sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Profile Settings</DialogTitle>
            <DialogDescription>
              Upload a new profile picture or remove your existing one. Maximum size: 5MB.
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-4 py-4">
            <div className="flex items-center justify-center">
              <div className="flex h-24 w-24 overflow-hidden items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-3xl font-semibold text-primary">
                {avatarUrl ? (
                  <img src={avatarUrl} alt={username || 'User'} className="h-full w-full object-cover" />
                ) : (
                  username?.charAt(0).toUpperCase() || 'U'
                )}
              </div>
            </div>
            <div className="flex gap-2 justify-center">
              <div className="relative">
                <Button variant="outline" disabled={uploadMutation.isPending}>
                  {uploadMutation.isPending ? "Uploading..." : "Upload New"}
                </Button>
                <input 
                  type="file" 
                  accept="image/jpeg,image/png,image/gif,image/webp"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={handleFileChange}
                  disabled={uploadMutation.isPending}
                />
              </div>
              <Button 
                variant="destructive" 
                onClick={() => deleteMutation.mutate()} 
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? "Removing..." : "Remove"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
