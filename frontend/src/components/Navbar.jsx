import { NavLink } from "react-router-dom";
import { Building2, Compass, Calculator, Moon, Sun, Sparkles, MapPin } from "lucide-react";
import { usePlan } from "../PlanContext";
import { useTheme } from "../ThemeContext";

export default function Navbar() {
  const { plan, setPlan } = usePlan();
  const { theme, toggleTheme } = useTheme();

  const linkClass = ({ isActive }) =>
    `flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
      isActive
        ? "bg-gradient-to-r from-brand-600 to-brand-500 text-white shadow-md shadow-brand-600/20"
        : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
    }`;

  return (
    <nav className="sticky top-0 z-50 border-b border-slate-200/70 dark:border-slate-800/70 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-accent-500 text-white shadow-md shadow-brand-600/25">
            <Building2 className="h-5 w-5" />
          </span>
          <div className="leading-tight">
            <p className="font-bold text-slate-800 dark:text-white tracking-tight">
              MediaImóvel
            </p>
            <p className="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500">
              <MapPin className="h-3 w-3" /> Dois Vizinhos
            </p>
          </div>
        </div>

        <div className="hidden sm:flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            <Compass className="h-4 w-4" />
            Explorar bairros
          </NavLink>
          <NavLink to="/avaliar" className={linkClass}>
            <Calculator className="h-4 w-4" />
            Avaliar imóvel
          </NavLink>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            aria-label="Alternar tema"
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <div className="flex rounded-lg border border-slate-200 dark:border-slate-700 overflow-hidden text-xs">
            {["free", "premium"].map((p) => (
              <button
                key={p}
                onClick={() => setPlan(p)}
                className={`flex items-center gap-1 px-3 py-1.5 font-medium capitalize transition-colors ${
                  plan === p
                    ? "bg-gradient-to-r from-slate-800 to-slate-700 text-white dark:from-brand-600 dark:to-accent-600"
                    : "bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400"
                }`}
              >
                {p === "premium" && <Sparkles className="h-3 w-3" />}
                {p}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="sm:hidden flex items-center gap-1 px-6 pb-3">
        <NavLink to="/" end className={linkClass}>
          <Compass className="h-4 w-4" />
          Bairros
        </NavLink>
        <NavLink to="/avaliar" className={linkClass}>
          <Calculator className="h-4 w-4" />
          Avaliar
        </NavLink>
      </div>
    </nav>
  );
}
