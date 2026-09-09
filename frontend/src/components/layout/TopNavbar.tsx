import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, Moon, Sun, Settings, LogOut, User, ChevronDown, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Breadcrumbs } from './Breadcrumbs';
import { useTheme } from '@/lib/use-theme';
import { useAuth } from '@/features/auth/context/AuthContext';
import { studentService } from '@/features/student/services/student.service';

type TopNavbarProps = {
  onMenuClick: () => void;
  onToggleCollapse: () => void;
  collapsed: boolean;
  userName: string;
  userRole: string;
  avatarText: string;
};

export function TopNavbar({
  onMenuClick,
  onToggleCollapse,
  collapsed,
  userName,
  userRole,
  avatarText,
}: TopNavbarProps) {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const [profileName, setProfileName] = useState('');

  useEffect(() => {
    if (user?.role === 'student') {
      studentService.getMyProfile()
        .then((p) => setProfileName(p.full_name || user.email))
        .catch(console.error);
    }
  }, [user]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const finalUserName = profileName || userName;
  const finalAvatarText = profileName ? profileName.substring(0, 2).toUpperCase() : avatarText;

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-card/80 px-4 backdrop-blur-lg md:px-6">
      {/* Mobile: open drawer */}
      <Button variant="ghost" size="icon" className="lg:hidden" onClick={onMenuClick} aria-label="Open menu">
        <Menu className="h-5 w-5" />
      </Button>

      {/* Desktop: collapse / expand sidebar */}
      <Button
        variant="ghost"
        size="icon"
        className="hidden lg:flex"
        onClick={onToggleCollapse}
        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <PanelLeftOpen className="h-5 w-5" /> : <PanelLeftClose className="h-5 w-5" />}
      </Button>

      <div className="hidden md:block">
        <Breadcrumbs />
      </div>

      {/* Search */}
      <div className="relative ml-auto hidden w-64 md:block lg:w-80">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search jobs, companies, skills..."
          className="pl-9 bg-secondary/50 border-transparent focus-visible:border-input"
          aria-label="Search"
        />
      </div>

      <div className="ml-auto flex items-center gap-1 md:ml-0">
        <Button variant="ghost" size="icon" onClick={toggleTheme} className="text-muted-foreground" aria-label="Toggle theme">
          {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </Button>

        <Button variant="ghost" size="icon" className="relative text-muted-foreground" aria-label="Notifications">
          <Bell className="h-5 w-5" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-primary ring-2 ring-card" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2 hover:bg-secondary">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">
                  {finalAvatarText}
                </AvatarFallback>
              </Avatar>
              <div className="hidden text-left lg:block">
                <p className="text-sm font-medium leading-tight">{finalUserName}</p>
                <p className="text-[11px] text-muted-foreground">{userRole}</p>
              </div>
              <ChevronDown className="hidden h-4 w-4 text-muted-foreground lg:block" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/student/profile')}>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout} className="text-rose-600 focus:text-rose-600">
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
