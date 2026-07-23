import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  MapPin,
  TrendingUp,
  Building2,
  ExternalLink,
  Calendar,
  SlidersHorizontal,
  ChevronDown,
  Home,
  BarChart3,
} from "lucide-react";
import { DOIS_VIZINHOS_ID, PROPERTY_TYPES, fetchNeighborhoods } from "../api/client";
import { usePlan } from "../PlanContext";
import NeighborhoodMap from "../components/NeighborhoodMap";
import { NeighborhoodCardSkeleton } from "../components/Skeleton";

const money = (v) =>
  v == null ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const dateBR = (v) => (v ? new Date(v).toLocaleDateString("pt-BR") : "—");

function Hero({ totalImoveis, totalBairros }) {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand-700 via-brand-600 to-accent-600 px-8 py-12 mb-8 shadow-xl shadow-brand-900/20">
      <div className="absolute -top-16 -right-16 h-64 w-64 rounded-full bg-white/10 animate-float" />
      <div
        className="absolute -bottom-20 -left-10 h-56 w-56 rounded-full bg-accent-300/20 animate-float"
        style={{ animationDelay: "1.5s" }}
      />
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.07]"
        aria-hidden="true"
      >
        <defs>
          <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse">
            <path d="M32 0H0V32" fill="none" stroke="white" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      <div className="relative">
        <div className="flex items-center gap-2 mb-3 text-brand-100 text-sm font-medium">
          <Home className="h-4 w-4" />
          Dois Vizinhos · PR
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-2">
          Explorar bairros
        </h1>
        <p className="text-brand-100 max-w-xl mb-6">
          Mediana de R$/m² e comparáveis reais coletados nas imobiliárias da região —
          atualizado a cada rodada de coleta.
        </p>
        <div className="flex flex-wrap gap-3">
          <span className="flex items-center gap-2 rounded-xl bg-white/15 backdrop-blur px-4 py-2 text-white text-sm font-medium">
            <Building2 className="h-4 w-4" /> {totalImoveis} imóveis
          </span>
          <span className="flex items-center gap-2 rounded-xl bg-white/15 backdrop-blur px-4 py-2 text-white text-sm font-medium">
            <MapPin className="h-4 w-4" /> {totalBairros} bairros
          </span>
        </div>
      </div>
    </div>
  );
}

export default function NeighborhoodExplorer() {
  const { plan } = usePlan();
  const [propertyType, setPropertyType] = useState("");
  const [purpose, setPurpose] = useState("venda");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openBairro, setOpenBairro] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchNeighborhoods({ municipalityId: DOIS_VIZINHOS_ID, propertyType, purpose, plan })
      .then((res) => {
        setData(res);
        setOpenBairro(res.neighborhoods[0]?.neighborhood ?? null);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [propertyType, purpose, plan]);

  const totalImoveis = data?.neighborhoods.reduce((sum, n) => sum + n.total, 0) ?? 0;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Hero totalImoveis={totalImoveis} totalBairros={data?.neighborhoods_total ?? 0} />

      <div className="flex flex-wrap items-center gap-3 mb-6">
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2">
          <SlidersHorizontal className="h-4 w-4 text-slate-400" />
          <select
            className="bg-transparent text-slate-700 dark:text-slate-200 focus:outline-none"
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
          >
            {PROPERTY_TYPES.map((t) => (
              <option key={t.value} value={t.value} className="dark:bg-slate-900">
                {t.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex rounded-xl border border-slate-200 dark:border-slate-700 overflow-hidden">
          {[
            { value: "venda", label: "Venda" },
            { value: "locacao", label: "Locação" },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPurpose(opt.value)}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                purpose === opt.value
                  ? "bg-gradient-to-r from-brand-600 to-brand-500 text-white"
                  : "bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="grid gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <NeighborhoodCardSkeleton key={i} />
          ))}
        </div>
      )}

      {error && (
        <p className="text-red-600 bg-red-50 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-900 rounded-xl px-4 py-3">
          Erro ao buscar dados: {error}
        </p>
      )}

      {data && !loading && (
        <>
          {data.limited && (
            <div className="mb-6 rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 px-4 py-3 text-amber-800 dark:text-amber-300 text-sm">
              Plano gratuito: mostrando {data.neighborhoods_returned} de{" "}
              {data.neighborhoods_total} bairros e {data.comparables_per_neighborhood}{" "}
              comparáveis por bairro.{" "}
              <span className="font-semibold">Assine o Premium para ver tudo.</span>
            </div>
          )}

          {data.neighborhoods.length === 0 && (
            <p className="text-slate-500 dark:text-slate-400">
              Nenhum imóvel encontrado com esses filtros.
            </p>
          )}

          <div className="mb-6">
            <NeighborhoodMap
              neighborhoods={data.neighborhoods}
              activeBairro={openBairro}
              onSelect={setOpenBairro}
            />
          </div>

          <div className="grid gap-4">
            {data.neighborhoods.map((n, i) => {
              const isOpen = openBairro === n.neighborhood;
              return (
                <motion.div
                  key={n.neighborhood}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`rounded-2xl bg-white dark:bg-slate-900 overflow-hidden border transition-shadow ${
                    isOpen
                      ? "border-brand-300 dark:border-brand-700 shadow-lg shadow-brand-600/10"
                      : "border-slate-200 dark:border-slate-800 hover:shadow-md"
                  }`}
                >
                  <button
                    onClick={() => setOpenBairro(isOpen ? null : n.neighborhood)}
                    className="w-full flex flex-wrap items-center justify-between gap-4 px-5 py-4 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400">
                        <MapPin className="h-5 w-5" />
                      </span>
                      <div>
                        <h2 className="font-semibold text-slate-800 dark:text-slate-100">
                          {n.neighborhood}
                        </h2>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {n.total} imóvel(is)
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="flex items-center justify-end gap-1 text-[11px] text-slate-400 uppercase tracking-wide">
                          <TrendingUp className="h-3 w-3" /> Mediana R$/m²
                        </p>
                        <p className="text-lg font-bold bg-gradient-to-r from-brand-600 to-accent-600 bg-clip-text text-transparent">
                          {n.median_pm2 != null ? money(n.median_pm2) : "sem amostra"}
                        </p>
                      </div>
                      <div className="hidden sm:block text-right">
                        <p className="text-[11px] text-slate-400 uppercase tracking-wide">
                          Faixa
                        </p>
                        <p className="text-sm text-slate-600 dark:text-slate-300">
                          {money(n.min_pm2)} – {money(n.max_pm2)}
                        </p>
                      </div>
                      <ChevronDown
                        className={`h-4 w-4 text-slate-400 transition-transform ${
                          isOpen ? "rotate-180" : ""
                        }`}
                      />
                    </div>
                  </button>

                  <AnimatePresence initial={false}>
                    {isOpen && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25, ease: "easeInOut" }}
                        className="overflow-hidden"
                      >
                        <div className="border-t border-slate-100 dark:border-slate-800 px-5 py-4">
                          {n.n_com_m2 < 3 && (
                            <p className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 mb-3">
                              <BarChart3 className="h-3.5 w-3.5" />
                              Amostra pequena (n={n.n_com_m2}) — mediana pouco confiável.
                            </p>
                          )}
                          <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead>
                                <tr className="text-left text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">
                                  <th className="py-2 font-medium">Título</th>
                                  <th className="py-2 font-medium">Tipo</th>
                                  <th className="py-2 font-medium text-right">Área</th>
                                  <th className="py-2 font-medium text-right">Preço</th>
                                  <th className="py-2 font-medium text-right">R$/m²</th>
                                  <th className="py-2 font-medium">Coletado</th>
                                  <th className="py-2 font-medium"></th>
                                </tr>
                              </thead>
                              <tbody>
                                {n.comparables.map((c, idx) => (
                                  <tr
                                    key={c.source_url}
                                    className={`border-b border-slate-50 dark:border-slate-800/60 ${
                                      idx % 2 === 1 ? "bg-slate-50/60 dark:bg-slate-800/20" : ""
                                    }`}
                                  >
                                    <td className="py-2 pr-2 text-slate-700 dark:text-slate-200">
                                      {c.title || "—"}
                                    </td>
                                    <td className="py-2 pr-2 text-slate-500 dark:text-slate-400">
                                      {c.property_type}
                                    </td>
                                    <td className="py-2 pr-2 text-right text-slate-500 dark:text-slate-400">
                                      {c.area_m2 ? `${c.area_m2} m²` : "—"}
                                    </td>
                                    <td className="py-2 pr-2 text-right text-slate-700 dark:text-slate-200">
                                      {money(c.price_brl)}
                                    </td>
                                    <td className="py-2 pr-2 text-right font-medium text-brand-700 dark:text-brand-400">
                                      {money(c.price_per_m2)}
                                    </td>
                                    <td className="py-2 pr-2 text-slate-500 dark:text-slate-400">
                                      <span className="flex items-center gap-1">
                                        <Calendar className="h-3 w-3" />
                                        {dateBR(c.collected_at)}
                                      </span>
                                    </td>
                                    <td className="py-2 text-right">
                                      <a
                                        href={c.source_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="inline-flex items-center gap-1 text-brand-600 dark:text-brand-400 hover:underline"
                                      >
                                        ver anúncio <ExternalLink className="h-3 w-3" />
                                      </a>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
