import React from "react";
import { Card } from "../../../ui/components/Card";
import { Button } from "../../../ui/components/Button";
import { colors, spacing, radius } from "../../../ui/theme";

interface Recommendation {
  id: string;
  title: string;
  description: string;
  confidence: number;
}

interface AIRecommendationsProps {
  recommendations: Recommendation[];
  loading?: boolean;
}

export const AIRecommendations: React.FC<AIRecommendationsProps> = ({ recommendations, loading }) => {
  return (
    <Card title="AI Рекомендации">
      <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
        {loading ? (
          <div style={{ color: colors.gray[500], textAlign: "center", padding: spacing.md }}>
            Загрузка рекомендаций...
          </div>
        ) : recommendations.length === 0 ? (
          <div style={{ color: colors.gray[500], textAlign: "center", padding: spacing.md }}>
            Рекомендации пока недоступны
          </div>
        ) : (
          recommendations.map((rec) => (
            <div
              key={rec.id}
              style={{
                padding: spacing.md,
                backgroundColor: colors.gray[50],
                borderRadius: radius.md,
                border: `1px solid ${colors.gray[200]}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: spacing.xs }}>
                <div style={{ fontWeight: 600, fontSize: "14px" }}>{rec.title}</div>
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: 600,
                    color: colors.primary[600],
                    backgroundColor: colors.primary[100],
                    padding: "2px 6px",
                    borderRadius: radius.sm,
                  }}
                >
                  {rec.confidence}%
                </div>
              </div>
              <div style={{ fontSize: "13px", color: colors.gray[700], marginBottom: spacing.sm }}>
                {rec.description}
              </div>
              <Button size="sm" variant="outline" fullWidth>
                Применить
              </Button>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};
