import { NavLink } from 'react-router-dom';
import { Compass, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { studentNav, staffNav, type NavSection } from '@/lib/navigation';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

type SidebarProps = {
  role: 'student' | 'staff';
  open: boolean;
  onClose: () => void;
  collapsed: boolean;
};

export function Sidebar({ role, open, onClose, collapsed }: SidebarProps) {
  const sections: NavSection[] = role === 'student' ? studentNav : staffNav;

  return (
    <>
      {/* Mobile overlay */}
      <div
        className={cn(
          'fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity lg:hidden',
          open ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
        onClick={onClose}
      />

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-card transition-all duration-300 ease-in-out',
          // Desktop width reacts to collapsed; mobile always full expanded width
          collapsed
            ? 'lg:w-[var(--sidebar-width-collapsed)]'
            : 'lg:w-[var(--sidebar-width)]',
          'w-[var(--sidebar-width)]',
          // Mobile slide-in/out
          open ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0'
        )}
        data-collapsed={collapsed}
      >
        {/* Logo */}
        <div className={cn('flex h-16 shrink-0 items-center border-b', collapsed ? 'justify-center px-2' : 'px-4')}>
          <NavLink
            to="/"
            onClick={onClose}
            className={cn(
              'flex items-center text-primary',
              collapsed ? 'mx-auto' : 'gap-2.5'
            )}
          >
            <div className={cn(
              'flex shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/30',
              collapsed ? 'h-10 w-10' : 'h-9 w-9'
            )}>
              <Compass className={cn(collapsed ? 'h-5.5 w-5.5' : 'h-5 w-5')} />
            </div>
            {!collapsed && (
              <div className="leading-tight text-foreground">
                <p className="text-sm font-bold tracking-tight">Career Compass</p>
                <p className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                  AI Platform
                </p>
              </div>
            )}
          </NavLink>
          <Button
            variant="ghost"
            size="icon"
            className={cn('lg:hidden', collapsed && 'hidden')}
            onClick={onClose}
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Nav sections */}
        <ScrollArea className={cn('flex-1 py-4', collapsed ? 'px-2' : 'px-3')}>
          <nav className={cn(collapsed ? 'space-y-4' : 'space-y-6')}>
            {sections.map((section) => (
              <div key={section.title}>
                {!collapsed && (
                  <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                    {section.title}
                  </p>
                )}
                {!collapsed && section.title === 'Menu' && <div className="mt-0" />}
                {collapsed && section.title !== sections[0].title && (
                  <div className="mx-auto my-3 h-px w-8 bg-border" />
                )}
                <div className={cn(collapsed ? 'space-y-1.5' : 'space-y-1', collapsed && 'mt-0')}>
                  {section.items.map((item) => (
                    <SidebarLink
                      key={item.to}
                      item={item}
                      collapsed={collapsed}
                      onClose={onClose}
                    />
                  ))}
                </div>
              </div>
            ))}
          </nav>
        </ScrollArea>

        {/* Footer — hidden when collapsed to keep the rail clean */}
        {!collapsed && (
          <div className="shrink-0 border-t p-4">
            <div className="rounded-lg bg-gradient-to-br from-primary/10 to-primary/5 p-3">
              <p className="text-xs font-semibold">Need help?</p>
              <p className="mt-0.5 text-[11px] text-muted-foreground">
                Check our career resources
              </p>
              <Button variant="outline" size="sm" className="mt-2 w-full text-xs">
                View Resources
              </Button>
            </div>
          </div>
        )}
      </aside>
    </>
  );
}

type SidebarLinkProps = {
  item: NavSection['items'][number];
  collapsed: boolean;
  onClose: () => void;
};

function SidebarLink({ item, collapsed, onClose }: SidebarLinkProps) {
  const link = (
    <NavLink
      to={item.to}
      onClick={onClose}
      className={({ isActive }) =>
        cn(
          'group relative flex items-center rounded-xl text-sm font-medium transition-all duration-200',
          collapsed
            ? 'mx-auto h-11 w-11 justify-center'
            : 'gap-3 px-3 py-2.5',
          isActive
            ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/30'
            : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
        )
      }
    >
      {({ isActive }) => (
        <>
          {collapsed && isActive && (
            <span className="absolute -left-0.5 top-1/2 h-6 w-1 -translate-y-1/2 rounded-r-full bg-primary" />
          )}
          <item.icon className={cn('shrink-0', collapsed ? 'h-5 w-5' : 'h-4.5 w-4.5')} />
          {!collapsed && (
            <>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <Badge className="h-5 px-1.5 text-[10px] font-semibold" variant="secondary">
                  {item.badge}
                </Badge>
              )}
            </>
          )}
        </>
      )}
    </NavLink>
  );

  if (!collapsed) return link;

  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right" sideOffset={16}>
        {item.label}
      </TooltipContent>
    </Tooltip>
  );
}
