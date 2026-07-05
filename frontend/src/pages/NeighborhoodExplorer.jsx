import { useEffect, useState } from "react";
import { DOIS_VIZINHOS_ID, PROPERTY_TYPES, fetchNeighborhoods } from "../api/client";
import { usePlan } from "../PlanContext";

const money = (v) =>
  v == null ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

const dateBR = (v) => (v ? new Date(v).toLocaleDateString("pt-BR") : "—");

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

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-semibold text-slate-800 mb-1">Explorar bairros</h1>
      <p className="text-slate-500 mb-6">
        Mediana de R$/m² e comparáveis por bairro em Dois Vizinhos.
      </p>

      <div className="flex flex-wrap gap-3 mb-6">
        <select
          className="border border-slate-300 rounded-lg px-3 py-2 bg-white text-slate-700"
          value={propertyType}
          onChange={(e) => setPropertyType(e.target.value)}
        >
          {PROPERTY_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {t.label}
            </option>
          ))}
        </select>

        <div className="flex rounded-lg border border-slate-300 overflow-hidden">
          {[
            { value: "venda", label: "Venda" },
            { value: "locacao", label: "Locação" },
          ].map((opt) => (
            <button
              key={opt.value}
              onClick={() => setPurpose(opt.value)}
              className={`px-4 py-2 text-sm font-medium ${
                purpose === opt.value
                  ? "bg-indigo-600 text-white"
                  : "bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <p className="text-slate-500">Carregando…</p>}
      {error && (
        <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          Erro ao buscar dados: {error}
        </p>
      )}

      {data && !loading && (
        <>
          {data.limited && (
            <div className="mb-6 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-amber-800 text-sm">
              Plano gratuito: mostrando {data.neighborhoods_returned} de{" "}
              {data.neighborhoods_total} bairros e {data.comparables_per_neighborhood}{" "}
              comparáveis por bairro.{" "}
              <span className="font-semibold">Assine o Premium para ver tudo.</span>
            </div>
          )}

          {data.neighborhoods.length === 0 && (
            <p className="text-slate-500">Nenhum imóvel encontrado com esses filtros.</p>
          )}

          <div className="grid gap-4">
            {data.neighborhoods.map((n) => (
              <div
                key={n.neighborhood}
                className="border border-slate-200 rounded-xl bg-white overflow-hidden"
              >
                <button
                  onClick={() =>
                    setOpenBairro(openBairro === n.neighborhood ? null : n.neighborhood)
                  }
                  className="w-full flex flex-wrap items-center justify-between gap-4 px-5 py-4 text-left hover:bg-slate-50"
                >
                  <div>
                    <h2 className="font-semibold text-slate-800">{n.neighborhood}</h2>
                    <p className="text-sm text-slate-500">{n.total} imóvel(is)</p>
                  </div>
                  <div className="flex gap-6 text-right">
                    <div>
                      <p className="text-xs text-slate-400 uppercase">Mediana R$/m²</p>
                      <p className="text-lg font-bold text-indigo-600">
                        {n.median_pm2 != null ? money(n.median_pm2) : "sem amostra"}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-slate-400 uppercase">Faixa</p>
                      <p className="text-sm text-slate-600">
                        {money(n.min_pm2)} – {money(n.max_pm2)}
                      </p>
                    </div>
                  </div>
                </button>

                {openBairro === n.neighborhood && (
                  <div className="border-t border-slate-100 px-5 py-4">
                    {n.n_com_m2 < 3 && (
                      <p className="text-xs text-amber-600 mb-3">
                        Amostra pequena (n={n.n_com_m2}) — mediana pouco confiável.
                      </p>
                    )}
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-slate-400 border-b border-slate-100">
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
                        {n.comparables.map((c) => (
                          <tr key={c.source_url} className="border-b border-slate-50">
                            <td className="py-2 pr-2 text-slate-700">{c.title || "—"}</td>
                            <td className="py-2 pr-2 text-slate-500">{c.property_type}</td>
                            <td className="py-2 pr-2 text-right text-slate-500">
                              {c.area_m2 ? `${c.area_m2} m²` : "—"}
                            </td>
                            <td className="py-2 pr-2 text-right text-slate-700">
                              {money(c.price_brl)}
                            </td>
                            <td className="py-2 pr-2 text-right text-slate-700">
                              {money(c.price_per_m2)}
                            </td>
                            <td className="py-2 pr-2 text-slate-500">
                              {dateBR(c.collected_at)}
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
            ))}
          </div>
        </>
      )}
    </div>
  );
}
