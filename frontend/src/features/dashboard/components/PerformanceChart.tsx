import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Card } from "../../../ui/components/Card";
import { colors, spacing } from "../../../ui/theme";

export interface PerformanceChartDataPoint {
  name: string;
  views: number;
  clicks: number;
}

interface PerformanceChartProps {
  data: PerformanceChartDataPoint[];
  loading: boolean;
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  loading,
}) => {
  if (loading) {
    return (
      <div style={{ marginBottom: spacing.lg }}>
        <Card title="Статистика просмотров">
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: 280,
              color: colors.gray[500],
            }}
          >
            Загрузка...
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: spacing.lg }}>
      <Card title="Статистика просмотров">
        <div style={{ height: 280 }}>
          {data.length === 0 ? (
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                alignItems: "center",
                height: "100%",
                color: colors.gray[500],
              }}
            >
              Нет данных. Обновите статистику с платформ.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip
                  formatter={(value: number | undefined) =>
                    (value ?? 0).toLocaleString("ru-RU")}
                  contentStyle={{
                    backgroundColor: colors.white,
                    border: `1px solid ${colors.gray[200]}`,
                    borderRadius: 8,
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="views"
                  stroke="#6366f1"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Просмотры"
                />
                <Line
                  type="monotone"
                  dataKey="clicks"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                  name="Клики"
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </Card>
    </div>
  );
};
