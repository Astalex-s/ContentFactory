import React from "react";
import { Card } from "../../../ui/components/Card";
import { colors, spacing } from "../../../ui/theme";
import { DashboardPipeline } from "../types";

interface ContentPipelineProps {
  stats: DashboardPipeline;
}

export const ContentPipeline: React.FC<ContentPipelineProps> = ({ stats }) => {
  const steps = [
    { label: "Импортировано", value: stats.imported, color: colors.gray[500] },
    { label: "Текст готов", value: stats.text_generated, color: colors.primary[500] },
    { label: "Медиа готово", value: stats.media_generated, color: colors.primary[600] },
    { label: "Запланировано", value: stats.scheduled, color: colors.warning },
    { label: "Опубликовано", value: stats.published, color: colors.success },
    { label: "Аналитика", value: stats.with_analytics, color: colors.primary[600] },
  ];

  return (
    <Card title="Воронка контента">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: spacing.sm,
          overflowX: "auto",
          paddingBottom: spacing.sm,
        }}
      >
        {steps.map((step, index) => (
          <div
            key={step.label}
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              minWidth: "80px",
              position: "relative",
              flex: 1,
            }}
          >
            <div
              style={{
                fontSize: "24px",
                fontWeight: 700,
                color: step.color,
                marginBottom: spacing.xs,
              }}
            >
              {step.value}
            </div>
            <div
              style={{
                fontSize: "12px",
                color: colors.gray[500],
                textAlign: "center",
              }}
            >
              {step.label}
            </div>
            {index < steps.length - 1 && (
              <div
                style={{
                  position: "absolute",
                  right: "-50%",
                  top: "30%",
                  width: "100%",
                  height: "2px",
                  backgroundColor: colors.gray[200],
                  zIndex: -1,
                  display: "none", // Hidden for now, can be enabled for desktop
                }}
              />
            )}
          </div>
        ))}
      </div>
    </Card>
  );
};
