import { NavLink } from "react-router-dom";
import { usePlan } from "../PlanContext";

export default function Navbar() {
  const { plan, setPlan } = usePlan();

  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-lg text-sm font-medium ${
      isActive ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-100"
    }`;

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="max-w-5xl mx-auto px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-800">MediaImóvel</span>
          <span className="text-xs text-slate-400">Dois Vizinhos</span>
        </div>
        <div className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            Explorar bairros
          </NavLink>
          <NavLink to="/avaliar" className={linkClass}>
            Avaliar imóvel
          </NavLink>
        </div>
        <div className="flex rounded-lg border border-slate-300 overflow-hidden text-xs">
          {["free", "premium"].map((p) => (
            <button
              key={p}
              onClick={() => setPlan(p)}
              className={`px-3 py-1.5 font-medium capitalize ${
                plan === p ? "bg-slate-800 text-white" : "bg-white text-slate-500"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
}
