import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Upload, ClipboardList, LogOut, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { ReactNode } from 'react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, exact: true },
  { to: '/ingest', label: 'Ingest', icon: Upload, exact: false },
  { to: '/review', label: 'Review', icon: ClipboardList, exact: false },
];

export default function Layout({ children }: { children: ReactNode }) {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-[#f5f7f4]">
      {/* Sidebar */}
      <aside className="w-56 shrink-0 bg-white border-r border-[#e8ede6] flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-2 px-5 py-5 border-b border-[#e8ede6]">
          <Sparkles className="w-4 h-4 text-[#336443]" />
          <span
            className="text-base font-semibold text-[#1f2a1d] tracking-tight"
            style={{ fontFamily: '"Neue Haas Grotesk Display Pro 55 Roman", "Helvetica Neue", sans-serif' }}
          >
            OriginESG
          </span>
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 px-3 py-4 flex-1">
          {navItems.map(({ to, label, icon: Icon, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-[#eef4ec] text-[#1f2a1d]'
                    : 'text-[#4b5b47] hover:bg-[#f5f7f4] hover:text-[#1f2a1d]'
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="px-3 py-4 border-t border-[#e8ede6]">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium text-[#4b5b47] hover:bg-[#f5f7f4] hover:text-[#1f2a1d] transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
