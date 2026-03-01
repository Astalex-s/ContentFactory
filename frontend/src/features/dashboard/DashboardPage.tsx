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
  const { stats, error: statsError, refetch: refetchStats } = useDashboard();
  const [products, setProducts] = useState<Product[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);

  const loadProducts = async () => {
    setProductsLoading(true);
    try {
      const result = await productsService.getProducts({ page: 1, page_size: 10 });
      setProducts(result.items);
    } catch (e) {
      console.error("Failed to load products", e);
    } finally {
      setProductsLoading(false);
    }
  };

  useEffect(() => {
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

  const emptyStats = {
    pipeline: {
      imported: 0,
      text_generated: 0,
      media_generated: 0,
      scheduled: 0,
      published: 0,
      with_analytics: 0,
    },
    alerts: {
      products_no_content: 0,
      publication_failed: 0,
      low_ctr_count: 0,
      ai_errors_count: 0,
    },
  };

  return (
    <PageContainer>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.lg }}>
        <h1 style={{ margin: 0 }}>Обзор</h1>
        <button
          type="button"
          onClick={() => { loadProducts(); refetchStats(); }}
          style={{
            padding: "8px 16px",
            background: "transparent",
            border: "1px solid #d1d5db",
            borderRadius: 8,
            cursor: "pointer",
            fontSize: 14,
            color: "#374151",
          }}
        >
          ↻ Обновить
        </button>
      </div>

      {statsError && (
        <div
          style={{
            padding: spacing.md,
            marginBottom: spacing.lg,
            background: "#fef2f2",
            border: "1px solid #fecaca",
            borderRadius: 8,
            color: "#b91c1c",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: spacing.md,
          }}
        >
          <span>Ошибка загрузки статистики: {statsError}</span>
          <button
            type="button"
            onClick={() => refetchStats()}
            style={{
              padding: "6px 12px",
              background: "#dc2626",
              color: "white",
              border: "none",
              borderRadius: 6,
              cursor: "pointer",
            }}
          >
            Обновить
          </button>
        </div>
      )}

      {/* Block 2: Content Pipeline */}
      {(stats || statsError) && (
        <div style={{ marginBottom: spacing.lg }}>
          <ContentPipeline stats={(stats ?? emptyStats).pipeline} />
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
        {(stats || statsError) && <AlertsPanel alerts={(stats ?? emptyStats).alerts} />}
        <AIRecommendations recommendations={recommendations} loading={recommendationsLoading} />
      </div>
    </PageContainer>
  );
};
