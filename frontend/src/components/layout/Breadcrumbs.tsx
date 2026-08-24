import { NavLink } from 'react-router-dom';
import { useLocation } from 'react-router-dom';
import { ChevronRight, Home } from 'lucide-react';
import { Fragment } from 'react';

const routeLabels: Record<string, string> = {
  student: 'Student',
  admin: 'Admin',
  dashboard: 'Dashboard',
  profile: 'My Profile',
  skills: 'Skills',
  resume: 'Resume Management',
  jobs: 'Available Jobs',
  applications: 'My Applications',
  readiness: 'Placement Readiness',
  students: 'Student Management',
  companies: 'Company Management',
  analytics: 'Placement Analytics',
};

export function Breadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  if (segments.length === 0) return null;

  return (
    <nav className="flex items-center gap-1.5 text-sm" aria-label="Breadcrumb">
      <NavLink to="/" className="flex items-center text-muted-foreground hover:text-foreground transition-colors" aria-label="Home">
        <Home className="h-3.5 w-3.5" />
      </NavLink>
      {segments.map((seg, i) => {
        const path = '/' + segments.slice(0, i + 1).join('/');
        const isLast = i === segments.length - 1;
        const label = routeLabels[seg] || seg.charAt(0).toUpperCase() + seg.slice(1);

        return (
          <Fragment key={path}>
            <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
            {isLast ? (
              <span className="font-medium text-foreground">{label}</span>
            ) : (
              <NavLink to={path} className="text-muted-foreground hover:text-foreground transition-colors">
                {label}
              </NavLink>
            )}
          </Fragment>
        );
      })}
    </nav>
  );
}
