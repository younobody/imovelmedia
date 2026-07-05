import { useEffect, useState } from "react";
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
      <h1 className="text-2xl font-semibold text-slate-800 mb-1">Avaliar imóvel</h1>
      <p className="text-slate-500 mb-6">
        Estimativa de preço a partir dos comparáveis coletados em Dois Vizinhos.
      </p>

      <form onSubmit={handleSubmit} className="bg-white border border-slate-200 rounded-xl p-5 grid gap-4 sm:grid-cols-2">
        <label className="text-sm text-slate-600">
          Tipo
          <select
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2"
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

        <label className="text-sm text-slate-600">
          Bairro (opcional)
          <select
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2"
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

        <label className="text-sm text-slate-600 sm:col-span-2">
          Área (m²)
          <input
            type="number"
            min="1"
            step="0.01"
            required
            className="mt-1 w-full border border-slate-300 rounded-lg px-3 py-2"
            value={areaM2}
            onChange={(e) => setAreaM2(e.target.value)}
            placeholder="ex.: 500"
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="sm:col-span-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium rounded-lg px-4 py-2"
        >
          {loading ? "Avaliando…" : "Avaliar"}
        </button>
      </form>

      {error && (
        <p className="mt-6 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {result && (
        <div className="mt-6 bg-white border border-slate-200 rounded-xl p-6">
          {!result.reliable && (
            <p className="text-xs text-amber-600 mb-3">
              Amostra pequena (n={result.sample_size}) — estimativa pouco confiável.
            </p>
          )}
          <p className="text-sm text-slate-500 mb-1">
            Base do cálculo: {result.basis} · {result.sample_size} comparável(is)
          </p>
          <p className="text-4xl font-bold text-indigo-600 mb-2">
            {money(result.estimated_price)}
          </p>
          <p className="text-sm text-slate-500 mb-6">
            Banda de confiança: {money(result.confidence_band.low)} –{" "}
            {money(result.confidence_band.high)} · mediana{" "}
            {money(result.price_per_m2_median)}/m²
          </p>

          <h3 className="font-semibold text-slate-700 mb-2">
            Comparáveis usados ({result.comparables_returned})
          </h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 border-b border-slate-100">
                <th className="py-2 font-medium">Título</th>
                <th className="py-2 font-medium">Bairro</th>
                <th className="py-2 font-medium text-right">Área</th>
                <th className="py-2 font-medium text-right">Preço</th>
                <th className="py-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {result.comparables.map((c) => (
                <tr key={c.source_url} className="border-b border-slate-50">
                  <td className="py-2 pr-2 text-slate-700">{c.title || "—"}</td>
                  <td className="py-2 pr-2 text-slate-500">{c.neighborhood}</td>
                  <td className="py-2 pr-2 text-right text-slate-500">
                    {c.area_m2 ? `${c.area_m2} m²` : "—"}
                  </td>
                  <td className="py-2 pr-2 text-right text-slate-700">
                    {money(c.price_brl)}
                  </td>
                  <td className="py-2 text-right">
                    <a
                      href={c.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-indigo-600 hover:underline"
                    >
                      ver anúncio
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
