import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calculator,
  Ruler,
  MapPin,
  Home,
  Sparkles,
  BarChart3,
  ExternalLink,
  Loader2,
  Gauge,
} from "lucide-react";
import {
  DOIS_VIZINHOS_ID,
  PROPERTY_TYPES,
  fetchNeighborhoods,
  fetchValuation,
} from "../api/client";
import { usePlan } from "../PlanContext";

const money = (v) =>
  v == null ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const VALUATION_TYPES = PROPERTY_TYPES.filter((t) => t.value !== "");

function Hero() {
  return (
    <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-accent-600 via-brand-600 to-brand-800 px-8 py-10 mb-8 shadow-xl shadow-brand-900/20">
      <div className="absolute -top-10 -left-10 h-48 w-48 rounded-full bg-white/10 animate-float" />
      <div
        className="absolute -bottom-16 -right-16 h-56 w-56 rounded-full bg-accent-300/20 animate-float"
        style={{ animationDelay: "2s" }}
      />
      <div className="relative">
        <div className="flex items-center gap-2 mb-3 text-brand-100 text-sm font-medium">
          <Calculator className="h-4 w-4" /> Estimativa baseada em dados reais
        </div>
        <h1 className="text-3xl sm:text-4xl font-bold text-white tracking-tight mb-2">
          Avaliar imóvel
        </h1>
        <p className="text-brand-100 max-w-xl">
          Estimativa de preço a partir dos comparáveis coletados nas imobiliárias de Dois
          Vizinhos.
        </p>
      </div>
    </div>
  );
}

export default function ValuationHelper() {
  const { plan } = usePlan();
  const [propertyType, setPropertyType] = useState("terreno");
  const [neighborhood, setNeighborhood] = useState("");
  const [areaM2, setAreaM2] = useState("");
  const [bairros, setBairros] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    setNeighborhood("");
    fetchNeighborhoods({
      municipalityId: DOIS_VIZINHOS_ID,
      propertyType,
      purpose: "venda",
      plan,
    })
      .then((res) => setBairros(res.neighborhoods.map((n) => n.neighborhood)))
      .catch(() => setBairros([]));
  }, [propertyType, plan]);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetchValuation({
        municipalityId: DOIS_VIZINHOS_ID,
        propertyType,
        neighborhood,
        areaM2: parseFloat(areaM2),
        plan,
      });
      setResult(res);
    } catch (e2) {
      setError(e2.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Hero />

      <form
        onSubmit={handleSubmit}
        className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 grid gap-5 sm:grid-cols-2 shadow-sm"
      >
        <label className="text-sm font-medium text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1.5 mb-1.5">
            <Home className="h-3.5 w-3.5 text-brand-500" /> Tipo
          </span>
          <select
            className="w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 dark:text-slate-100 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
          >
            {VALUATION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm font-medium text-slate-600 dark:text-slate-300">
          <span className="flex items-center gap-1.5 mb-1.5">
            <MapPin className="h-3.5 w-3.5 text-brand-500" /> Bairro (opcional)
          </span>
          <select
            className="w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 dark:text-slate-100 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
            value={neighborhood}
            onChange={(e) => setNeighborhood(e.target.value)}
          >
            <option value="">Qualquer bairro (média do município)</option>
            {bairros.map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm font-medium text-slate-600 dark:text-slate-300 sm:col-span-2">
          <span className="flex items-center gap-1.5 mb-1.5">
            <Ruler className="h-3.5 w-3.5 text-brand-500" /> Área (m²)
          </span>
          <input
            type="number"
            min="1"
            step="0.01"
            required
            className="w-full border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 dark:text-slate-100 rounded-xl px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 transition"
            value={areaM2}
            onChange={(e) => setAreaM2(e.target.value)}
            placeholder="ex.: 500"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="sm:col-span-2 flex items-center justify-center gap-2 bg-gradient-to-r from-brand-600 to-accent-600 hover:from-brand-700 hover:to-accent-700 disabled:opacity-50 text-white font-medium rounded-xl px-4 py-3 shadow-md shadow-brand-600/25 transition-all active:scale-[0.98]"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Avaliando…
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" /> Avaliar
            </>
          )}
        </button>
      </form>

      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="mt-6 text-red-600 bg-red-50 dark:bg-red-950/40 dark:text-red-300 border border-red-200 dark:border-red-900 rounded-xl px-4 py-3"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
            className="mt-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-sm"
          >
            {!result.reliable && (
              <p className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400 mb-3">
                <Gauge className="h-3.5 w-3.5" />
                Amostra pequena (n={result.sample_size}) — estimativa pouco confiável.
              </p>
            )}
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">
              Base do cálculo: {result.basis} · {result.sample_size} comparável(is)
            </p>
            <p className="text-4xl sm:text-5xl font-bold bg-gradient-to-r from-brand-600 to-accent-600 bg-clip-text text-transparent mb-2">
              {money(result.estimated_price)}
            </p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              Banda de confiança: {money(result.confidence_band.low)} –{" "}
              {money(result.confidence_band.high)} · mediana{" "}
              {money(result.price_per_m2_median)}/m²
            </p>

            <h3 className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-200 mb-3">
              <BarChart3 className="h-4 w-4 text-brand-500" />
              Comparáveis usados ({result.comparables_returned})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-slate-400 dark:text-slate-500 border-b border-slate-100 dark:border-slate-800">
                    <th className="py-2 font-medium">Título</th>
                    <th className="py-2 font-medium">Bairro</th>
                    <th className="py-2 font-medium text-right">Área</th>
                    <th className="py-2 font-medium text-right">Preço</th>
                    <th className="py-2 font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {result.comparables.map((c, idx) => (
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
                        {c.neighborhood}
                      </td>
                      <td className="py-2 pr-2 text-right text-slate-500 dark:text-slate-400">
                        {c.area_m2 ? `${c.area_m2} m²` : "—"}
                      </td>
                      <td className="py-2 pr-2 text-right text-slate-700 dark:text-slate-200">
                        {money(c.price_brl)}
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
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
