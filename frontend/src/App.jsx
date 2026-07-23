import { BrowserRouter, Routes, Route } from "react-router-dom";
import { PlanProvider } from "./PlanContext";
import { ThemeProvider } from "./ThemeContext";
import Navbar from "./components/Navbar";
import NeighborhoodExplorer from "./pages/NeighborhoodExplorer";
import ValuationHelper from "./pages/ValuationHelper";

export default function App() {
  return (
    <ThemeProvider>
      <PlanProvider>
        <BrowserRouter basename={import.meta.env.PROD ? "/imovelmedia" : "/"}>
          <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors duration-300">
            <Navbar />
            <Routes>
              <Route path="/" element={<NeighborhoodExplorer />} />
              <Route path="/avaliar" element={<ValuationHelper />} />
            </Routes>
          </div>
        </BrowserRouter>
      </PlanProvider>
    </ThemeProvider>
  );
}
