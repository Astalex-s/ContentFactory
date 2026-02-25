import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { PageContainer } from "../ui/layout/PageContainer";
import { Button } from "../ui/components/Button";
import { Card } from "../ui/components/Card";
import { Alert } from "../ui/components/Alert";
import { spacing, colors } from "../ui/theme";
import { api } from "../services/api";

interface ImportReport {
  imported: number;
  errors: string[];
}

export function ImportProductsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleImport = async () => {
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const response = await api.post<ImportReport>("/products/import-from-marketplace");
      setReport(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Ошибка импорта продуктов");
    } finally {
      setLoading(false);
    }
  };

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
            Импорт продуктов
          </h1>
          <Button variant="secondary" onClick={() => navigate("/products")}>
            Назад к продуктам
          </Button>
        </div>
        <p style={{ color: colors.gray[500], margin: 0 }}>
          Импорт продуктов из маркетплейса с автоматической генерацией описаний
        </p>
      </div>

      <Card>
        <div style={{ textAlign: "center", padding: spacing.xl }}>
          <div
            style={{
              width: 80,
              height: 80,
              borderRadius: "50%",
              backgroundColor: colors.primary[100],
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto",
              marginBottom: spacing.lg,
              fontSize: 40,
            }}
          >
            📦
          </div>
          <h2 style={{ marginBottom: spacing.md, fontSize: 20, fontWeight: 600 }}>
            Импорт из маркетплейса
          </h2>
          <p
            style={{
              color: colors.gray[500],
              marginBottom: spacing.xl,
              maxWidth: 500,
              margin: "0 auto",
            }}
          >
            Система автоматически импортирует 5 продуктов из маркетплейса,
            сгенерирует описания с помощью AI и сохранит их в базу данных.
          </p>

          {error && (
            <Alert variant="error" style={{ marginBottom: spacing.lg }}>
              {error}
            </Alert>
          )}

          {report && (
            <Alert
              variant={report.errors.length > 0 ? "warning" : "success"}
              style={{ marginBottom: spacing.lg, textAlign: "left" }}
            >
              <div style={{ fontWeight: 600, marginBottom: spacing.sm }}>
                Импортировано продуктов: {report.imported}
              </div>
              {report.errors.length > 0 && (
                <div>
                  <div style={{ fontWeight: 600, marginTop: spacing.md, marginBottom: spacing.sm }}>
                    Ошибки:
                  </div>
                  <ul style={{ margin: 0, paddingLeft: spacing.lg }}>
                    {report.errors.map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </Alert>
          )}

          <Button
            variant="primary"
            size="lg"
            onClick={handleImport}
            disabled={loading}
            style={{ minWidth: 200 }}
          >
            {loading ? "Импорт..." : "Начать импорт"}
          </Button>

          {loading && (
            <p style={{ color: colors.gray[500], marginTop: spacing.md, fontSize: 14 }}>
              Это может занять несколько минут...
            </p>
          )}
        </div>
      </Card>
    </PageContainer>
  );
}
