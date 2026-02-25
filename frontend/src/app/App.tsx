import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppLayout } from "../ui/layout/AppLayout";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import AnalyticsPage from "../pages/AnalyticsPage";
import { ContentGenerationPage } from "../pages/ContentGenerationPage";
import { ProductContentPage } from "../pages/ProductContentPage";
import { ProductDetailsPage } from "../pages/ProductDetailsPage";
import { ProductsListPage } from "../pages/ProductsListPage";
import { ContentPage } from "../pages/ContentPage";
import { PublishingPage } from "../pages/PublishingPage";
import { CreatorsPage } from "../pages/CreatorsPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ImportProductsPage } from "../pages/ImportProductsPage";
import { GenerateContentPage } from "../pages/GenerateContentPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/products" element={<ProductsListPage />} />
          <Route path="/products/import" element={<ImportProductsPage />} />
          <Route path="/products/:id" element={<ProductDetailsPage />} />
          <Route path="/products/:id/generate" element={<ContentGenerationPage />} />
          <Route path="/products/:id/content" element={<ProductContentPage />} />
          <Route path="/content" element={<ContentPage />} />
          <Route path="/content/generate" element={<GenerateContentPage />} />
          <Route path="/publishing" element={<PublishingPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/creators" element={<CreatorsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
