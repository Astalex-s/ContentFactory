import React from "react";
import {
  BarChart,
  Bar,
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
import type { AggregatedStats, DailyMetrics, TopContent } from "../../analytics/api";

interface AnalyticsOverviewProps {
  stats: AggregatedStats | null;
  topContent: TopContent[];
  statsByDate?: DailyMetrics[];
  loading: boolean;
}

const formatChartDate = (dateStr: string) => {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
  } catch {
    return dateStr;
  }
};

const chartDataFromTopContent = (topContent: TopContent[]) =>
  topContent.map((item) => ({
    name: item.content_id.slice(0, 8),
    views: item.views,
    clicks: item.clicks,
    ctr: item.ctr,
  }));

export const AnalyticsOverview: React.FC<AnalyticsOverviewProps> = ({
  stats,
  topContent,
  statsByDate = [],
  loading,
}) => {
  const chartData = chartDataFromTopContent(topContent);
  const timeSeriesData = (statsByDate ?? []).map((d) => ({
    name: formatChartDate(d.date),
    date: d.date,
    views: d.total_views,
    clicks: d.total_clicks,
  }));

  if (loading && !stats) {
    return (
      <div style={{ padding: spacing.xl, textAlign: "center", color: colors.gray[500] }}>
        Загрузка аналитики...
      </div>
    );
  }

  return (
    <div style={{ marginBottom: spacing.lg }}>
      {stats && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: spacing.lg,
            marginBottom: spacing.lg,
          }}
        >
          <Card>
            <h3 style={{ margin: "0 0 8px 0", fontSize: 14, color: colors.gray[700] }}>
              Просмотры
            </h3>
            <p style={{ fontSize: "1.75em", margin: 0, color: colors.primary[600] }}>
              {stats.total_views}
            </p>
          </Card>
          <Card>
            <h3 style={{ margin: "0 0 8px 0", fontSize: 14, color: colors.gray[700] }}>
              Клики
            </h3>
            <p style={{ fontSize: "1.75em", margin: 0, color: colors.success }}>
              {stats.total_clicks}
            </p>
          </Card>
          <Card>
            <h3 style={{ margin: "0 0 8px 0", fontSize: 14, color: colors.gray[700] }}>
              Средний CTR
            </h3>
            <p style={{ fontSize: "1.75em", margin: 0, color: colors.warning }}>
              {stats.avg_ctr}%
            </p>
          </Card>
          <Card>
            <h3 style={{ margin: "0 0 8px 0", fontSize: 14, color: colors.gray[700] }}>
              Переходы на маркетплейс
            </h3>
            <p style={{ fontSize: "1.75em", margin: 0, color: colors.gray[700] }}>
              {stats.total_marketplace_clicks}
            </p>
          </Card>
        </div>
      )}

      <div style={{ marginBottom: spacing.lg }}>
        <Card title="Просмотры и клики по дням">
          <div style={{ height: 280 }}>
            {loading ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "100%",
                  color: colors.gray[500],
                }}
              >
                Загрузка...
              </div>
            ) : timeSeriesData.length === 0 ? (
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
                <LineChart data={timeSeriesData}>
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

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: spacing.lg,
        }}
      >
        <Card title="Топ контент: просмотры и клики">
          <div style={{ height: 280 }}>
            {loading ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "100%",
                  color: colors.gray[500],
                }}
              >
                Загрузка...
              </div>
            ) : chartData.length === 0 ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "100%",
                  color: colors.gray[500],
                }}
              >
                Нет данных для отображения
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="views" fill="#8884d8" name="Просмотры" />
                  <Bar dataKey="clicks" fill="#82ca9d" name="Клики" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        <Card title="График CTR">
          <div style={{ height: 280 }}>
            {loading ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "100%",
                  color: colors.gray[500],
                }}
              >
                Загрузка...
              </div>
            ) : chartData.length === 0 ? (
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center",
                  height: "100%",
                  color: colors.gray[500],
                }}
              >
                Нет данных для отображения
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="ctr"
                    stroke="#ff7300"
                    name="CTR %"
                    strokeWidth={2}
                    dot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};
