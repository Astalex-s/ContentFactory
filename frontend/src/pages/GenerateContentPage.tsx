import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Select } from "../ui/components/Select";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { api } from "../services/api";
import { productsService, type Product } from "../services/products";

interface GenerateRequest {
  platform: string;
  tone: string;
  content_text_type: string;
}

interface GeneratedVariant {
  id: string;
  content_type: string;
  content_text?: string;
  file_path?: string;
}

interface GenerateResponse {
  product_id: string;
  generated_variants: GeneratedVariant[];
}

export function GenerateContentPage() {
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [platform, setPlatform] = useState<string>("tiktok");
  const [tone, setTone] = useState<string>("emotional");
  const [contentTextType, setContentTextType] = useState<string>("short_post");
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadProducts = async () => {
      try {
        const data = await productsService.getProducts({ page: 1, page_size: 100 });
        setProducts(data.items);
        if (data.items.length > 0) {
          setSelectedProductId(data.items[0].id);
        }
      } catch (err) {
        console.error("Failed to load products", err);
      } finally {
        setLoadingProducts(false);
      }
    };
    loadProducts();
  }, []);

  const handleGenerate = async () => {
    if (!selectedProductId) {
      setError("Выберите продукт");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const requestBody: GenerateRequest = {
        platform,
        tone,
        content_text_type: contentTextType,
      };

      const response = await api.post<GenerateResponse>(
        `/content/generate/${selectedProductId}`,
        requestBody
      );
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка генерации контента");
    } finally {
      setLoading(false);
    }
  };

  const selectedProduct = products.find((p) => p.id === selectedProductId);

  return (
    <PageContainer>
      <div style={{ marginBottom: spacing.lg }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: spacing.md,
          }}
        >
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 700 }}>
            Генерация контента
          </h1>
          <Button variant="secondary" onClick={() => navigate("/content")}>
            К списку контента
          </Button>
        </div>
        <p style={{ color: colors.gray[500], margin: 0 }}>
          Автоматическая генерация контента для продукта с помощью AI
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: spacing.lg }}>
        <Card title="Настройки генерации">
          <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
            <Select
              label="Продукт"
              value={selectedProductId}
              onChange={(e) => setSelectedProductId(e.target.value)}
              disabled={loadingProducts}
            >
              {loadingProducts ? (
                <option>Загрузка...</option>
              ) : products.length === 0 ? (
                <option>Нет доступных продуктов</option>
              ) : (
                products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name}
                  </option>
                ))
              )}
            </Select>

            <Select
              label="Платформа"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              <option value="tiktok">TikTok</option>
              <option value="youtube">YouTube</option>
              <option value="vk">VK</option>
            </Select>

            <Select
              label="Тон"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
            >
              <option value="emotional">Эмоциональный</option>
              <option value="professional">Профессиональный</option>
              <option value="casual">Неформальный</option>
              <option value="humorous">Юмористический</option>
            </Select>

            <Select
              label="Тип контента"
              value={contentTextType}
              onChange={(e) => setContentTextType(e.target.value)}
            >
              <option value="short_post">Короткий пост</option>
              <option value="long_post">Длинный пост</option>
              <option value="story">История</option>
              <option value="description">Описание</option>
            </Select>

            {error && (
              <Alert variant="error" style={{ marginTop: spacing.md }}>
                {error}
              </Alert>
            )}

            <Button
              variant="primary"
              onClick={handleGenerate}
              disabled={loading || !selectedProductId || loadingProducts}
              style={{ marginTop: spacing.md }}
            >
              {loading ? "Генерация..." : "Сгенерировать контент"}
            </Button>

            {loading && (
              <p style={{ color: colors.gray[500], fontSize: 14, textAlign: "center" }}>
                Генерация может занять до минуты...
              </p>
            )}
          </div>
        </Card>

        <Card title="Информация о продукте">
          {selectedProduct ? (
            <div>
              <div style={{ marginBottom: spacing.md }}>
                <div style={{ fontWeight: 600, marginBottom: spacing.xs }}>
                  Название:
                </div>
                <div style={{ color: colors.gray[700] }}>{selectedProduct.name}</div>
              </div>
              <div style={{ marginBottom: spacing.md }}>
                <div style={{ fontWeight: 600, marginBottom: spacing.xs }}>
                  Категория:
                </div>
                <div style={{ color: colors.gray[700] }}>{selectedProduct.category}</div>
              </div>
              <div style={{ marginBottom: spacing.md }}>
                <div style={{ fontWeight: 600, marginBottom: spacing.xs }}>
                  Цена:
                </div>
                <div style={{ color: colors.gray[700] }}>{selectedProduct.price} ₽</div>
              </div>
              {selectedProduct.description && (
                <div>
                  <div style={{ fontWeight: 600, marginBottom: spacing.xs }}>
                    Описание:
                  </div>
                  <div
                    style={{
                      color: colors.gray[700],
                      maxHeight: 200,
                      overflow: "auto",
                      fontSize: 14,
                    }}
                  >
                    {selectedProduct.description}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ color: colors.gray[500], textAlign: "center", padding: spacing.xl }}>
              Выберите продукт для просмотра информации
            </div>
          )}
        </Card>
      </div>

      {result && (
        <Card
          title="Результат генерации"
          style={{ marginTop: spacing.lg }}
        >
          <Alert variant="success" style={{ marginBottom: spacing.lg }}>
            Успешно сгенерировано вариантов: {result.generated_variants.length}
          </Alert>

          <div style={{ display: "flex", flexDirection: "column", gap: spacing.lg }}>
            {result.generated_variants.map((variant, idx) => (
              <div
                key={variant.id}
                style={{
                  padding: spacing.md,
                  backgroundColor: colors.gray[50],
                  borderRadius: 8,
                  border: `1px solid ${colors.gray[200]}`,
                }}
              >
                <div
                  style={{
                    fontWeight: 600,
                    marginBottom: spacing.sm,
                    color: colors.gray[900],
                  }}
                >
                  Вариант {idx + 1} ({variant.content_type})
                </div>
                {variant.content_text && (
                  <div
                    style={{
                      whiteSpace: "pre-wrap",
                      color: colors.gray[700],
                      fontSize: 14,
                      lineHeight: 1.6,
                    }}
                  >
                    {variant.content_text}
                  </div>
                )}
                {variant.file_path && (
                  <div style={{ color: colors.gray[500], fontSize: 14, marginTop: spacing.sm }}>
                    📎 Файл: {variant.file_path}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: spacing.lg, textAlign: "center" }}>
            <Button variant="secondary" onClick={() => navigate("/content")}>
              Перейти к списку контента
            </Button>
          </div>
        </Card>
      )}
    </PageContainer>
  );
}
