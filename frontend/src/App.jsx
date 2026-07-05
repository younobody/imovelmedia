import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PlanProvider } from "./PlanContext";
import Navbar from "./components/Navbar";
import NeighborhoodExplorer from "./pages/NeighborhoodExplorer";
import ValuationHelper from "./pages/ValuationHelper";

export default function App() {
  return (
    <PlanProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-slate-50">
          <Navbar />
          <Routes>
            <Route path="/" element={<NeighborhoodExplorer />} />
            <Route path="/avaliar" element={<ValuationHelper />} />
          </Routes>
        </div>
      </BrowserRouter>
    </PlanProvider>
  );
}
