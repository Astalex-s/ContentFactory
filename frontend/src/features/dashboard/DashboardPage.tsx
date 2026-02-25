import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../../ui/layout/PageContainer";
import { spacing } from "../../ui/theme";
import { useDashboard } from "./hooks/useDashboard";
import { ContentPipeline } from "./components/ContentPipeline";
import { AlertsPanel } from "./components/AlertsPanel";
import { ProductsTable } from "./components/ProductsTable";
import { PerformanceChart } from "./components/PerformanceChart";
import { AIRecommendations } from "./components/AIRecommendations";
import { productsService } from "../../services/products";
import { Product } from "../../types/product";
import { api } from "../../services/api";

interface Recommendation {
  id: string;
  title: string;
  description: string;
  confidence: number;
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { stats, error: statsError } = useDashboard();
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);

  useEffect(() => {
    const loadProducts = async () => {
      setProductsLoading(true);
      try {
        // Load recent products for the table
        const result = await productsService.getProducts({ page: 1, page_size: 5 });
        setProducts(result.items);
      } catch (e) {
        console.error("Failed to load products", e);
      } finally {
        setProductsLoading(false);
      }
    };
    loadProducts();
  }, []);

  useEffect(() => {
    const loadRecommendations = async () => {
      setRecommendationsLoading(true);
      try {
        const response = await api.get<{ recommendations: Recommendation[] }>("/dashboard/recommendations");
        setRecommendations(response.data.recommendations);
      } catch (e) {
        console.error("Failed to load recommendations", e);
      } finally {
        setRecommendationsLoading(false);
      }
    };
    loadRecommendations();
  }, []);

  const handleViewProduct = (id: string) => {
    navigate(`/products/${id}`);
  };

  const handleGenerateContent = (id: string) => {
    navigate(`/products/${id}/generate`);
  };

  if (statsError) {
    return <PageContainer>Error loading dashboard: {statsError}</PageContainer>;
  }

  return (
    <PageContainer>
      <h1 style={{ marginBottom: spacing.lg }}>Обзор</h1>

      {/* Block 2: Content Pipeline */}
      {stats && (
        <div style={{ marginBottom: spacing.lg }}>
          <ContentPipeline stats={stats.pipeline} />
        </div>
      )}

      {/* Block 1: Products Overview */}
      <div style={{ marginBottom: spacing.lg }}>
        <ProductsTable
          products={products}
          loading={productsLoading}
          onView={handleViewProduct}
          onGenerate={handleGenerateContent}
        />
      </div>

      {/* Block 3: Performance Analytics */}
      <div style={{ marginBottom: spacing.lg }}>
        <PerformanceChart data={[]} loading={false} />
      </div>

      {/* Block 4: Alerts & Block 5: AI Recommendations */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: spacing.lg,
          marginBottom: spacing.lg,
        }}
      >
        {stats && <AlertsPanel alerts={stats.alerts} />}
        <AIRecommendations recommendations={recommendations} loading={recommendationsLoading} />
      </div>
    </PageContainer>
  );
};
