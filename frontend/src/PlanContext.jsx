import { createContext, useContext, useState } from "react";

const PlanContext = createContext(null);

export function PlanProvider({ children }) {
  const [plan, setPlan] = useState("free");
  return (
    <PlanContext.Provider value={{ plan, setPlan }}>{children}</PlanContext.Provider>
  );
}

export function usePlan() {
  return useContext(PlanContext);
}
