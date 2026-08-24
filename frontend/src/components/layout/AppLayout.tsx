import { useEffect, useState } from 'react';
import { Sidebar } from './Sidebar';
import { TopNavbar } from './TopNavbar';
import { TooltipProvider } from '@/components/ui/tooltip';
import { useSidebarCollapse } from '@/lib/use-sidebar-collapse';

type AppLayoutProps = {
  role: 'student' | 'admin';
  userName: string;
  userRole: string;
  avatarText: string;
  children: React.ReactNode;
};

export function AppLayout({ role, userName, userRole, avatarText, children }: AppLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { collapsed, toggleCollapsed } = useSidebarCollapse();

  useEffect(() => {
    const onResize = () => {
      if (window.innerWidth >= 1024) setSidebarOpen(false);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <TooltipProvider delayDuration={200}>
        <Sidebar
        role={role}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        collapsed={collapsed}
      />
      <div
        className="transition-[padding] duration-300 ease-in-out lg:pl-[var(--sidebar-width)] data-[collapsed=true]:lg:pl-[var(--sidebar-width-collapsed)]"
        data-collapsed={collapsed}
      >
        <TopNavbar
          onMenuClick={() => setSidebarOpen(true)}
          onToggleCollapse={toggleCollapsed}
          collapsed={collapsed}
          userName={userName}
          userRole={userRole}
          avatarText={avatarText}
        />
        <main className="min-h-[calc(100vh-4rem)]">{children}</main>
      </div>
      </TooltipProvider>
    </div>
  );
}
