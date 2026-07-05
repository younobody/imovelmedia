const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const DOIS_VIZINHOS_ID = 1;

export const PROPERTY_TYPES = [
  { value: "", label: "Todos os tipos" },
  { value: "casa", label: "Casa" },
  { value: "terreno", label: "Terreno" },
  { value: "apartamento", label: "Apartamento" },
  { value: "sobrado", label: "Sobrado" },
  { value: "area-rural", label: "Área rural" },
  { value: "sala-comercial", label: "Sala comercial" },
  { value: "chacara", label: "Chácara" },
  { value: "terreno-comercial", label: "Terreno comercial" },
  { value: "sitio", label: "Sítio" },
  { value: "barracao", label: "Barracão" },
  { value: "ponto-comercial", label: "Ponto comercial" },
];

async function request(path, options) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Erro ${res.status} ao chamar ${path}`);
  }
  return res.json();
}

export function fetchNeighborhoods({ municipalityId, propertyType, purpose, plan }) {
  const params = new URLSearchParams({ municipality_id: municipalityId, purpose, plan });
  if (propertyType) params.set("property_type", propertyType);
  return request(`/neighborhoods?${params.toString()}`);
}

export function fetchValuation({ municipalityId, propertyType, neighborhood, areaM2, plan }) {
  return request("/valuate", {
    method: "POST",
    body: JSON.stringify({
      municipality_id: municipalityId,
      property_type: propertyType,
      neighborhood: neighborhood || null,
      area_m2: areaM2,
      plan,
    }),
  });
}
