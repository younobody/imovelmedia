import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";

const PARQUE = { lat: -25.7322852, lng: -53.0776012, name: "Parque de Exposições" };

const money = (v) =>
  v == null ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });

// Escala sequencial simples (claro -> escuro) na cor da marca, por faixa de preco.
function colorFor(pm2, min, max) {
  if (pm2 == null || min == null || max == null || max === min) return "#60a5fa";
  const t = (pm2 - min) / (max - min);
  const stops = ["#93c5fd", "#3b82f6", "#1d4ed8", "#172554"];
  const idx = Math.min(stops.length - 1, Math.floor(t * stops.length));
  return stops[idx];
}

export default function NeighborhoodMap({ neighborhoods, activeBairro, onSelect }) {
  const withCoords = neighborhoods.filter((n) => n.avg_lat != null && n.avg_lng != null);
  if (withCoords.length === 0) return null;

  const prices = withCoords.map((n) => n.median_pm2).filter((v) => v != null);
  const min = prices.length ? Math.min(...prices) : null;
  const max = prices.length ? Math.max(...prices) : null;
  const maxTotal = Math.max(...withCoords.map((n) => n.total), 1);

  return (
    <div className="relative overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm animate-slide-up">
      <MapContainer
        center={[PARQUE.lat, PARQUE.lng]}
        zoom={13}
        scrollWheelZoom={false}
        style={{ height: "340px", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <CircleMarker
          center={[PARQUE.lat, PARQUE.lng]}
          radius={9}
          pathOptions={{ color: "#0d9488", fillColor: "#14b8a6", fillOpacity: 0.9, weight: 2 }}
        >
          <Popup>
            <strong>{PARQUE.name}</strong>
            <br />
            Ponto de referência (seus lotes ficam aqui)
          </Popup>
        </CircleMarker>

        {withCoords.map((n) => {
          const radius = 6 + 10 * Math.sqrt(n.total / maxTotal);
          const color = colorFor(n.median_pm2, min, max);
          const isActive = n.neighborhood === activeBairro;
          return (
            <CircleMarker
              key={n.neighborhood}
              center={[n.avg_lat, n.avg_lng]}
              radius={radius}
              eventHandlers={{ click: () => onSelect?.(n.neighborhood) }}
              pathOptions={{
                color: isActive ? "#f59e0b" : "white",
                weight: isActive ? 3 : 1.5,
                fillColor: color,
                fillOpacity: 0.85,
              }}
            >
              <Popup>
                <strong>{n.neighborhood}</strong>
                <br />
                {n.total} imóvel(is) · mediana{" "}
                {n.median_pm2 != null ? `${money(n.median_pm2)}/m²` : "sem amostra"}
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className="absolute bottom-3 right-3 z-[1000] flex items-center gap-2 rounded-lg bg-white/90 dark:bg-slate-900/90 backdrop-blur px-3 py-1.5 text-[11px] text-slate-600 dark:text-slate-300 shadow">
        <span className="h-2.5 w-2.5 rounded-full bg-[#93c5fd]" /> menor R$/m²
        <span className="h-2.5 w-2.5 rounded-full bg-[#172554] ml-2" /> maior R$/m²
      </div>
    </div>
  );
}
