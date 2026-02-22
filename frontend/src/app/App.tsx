import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { ContentGenerationPage } from "@/pages/ContentGenerationPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { ProductContentPage } from "@/pages/ProductContentPage";
import { ProductDetailsPage } from "@/pages/ProductDetailsPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/products/:id" element={<ProductDetailsPage />} />
          <Route path="/products/:id/generate" element={<ContentGenerationPage />} />
          <Route path="/products/:id/content" element={<ProductContentPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
