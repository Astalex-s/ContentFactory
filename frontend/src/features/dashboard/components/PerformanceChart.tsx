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
import { colors } from "../../../ui/theme";

interface PerformanceChartProps {
  data: Record<string, unknown>[];
  loading?: boolean;
}

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ data, loading }) => {
  return (
    <Card title="Performance Overview">
      <div style={{ height: "300px", width: "100%" }}>
        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100%" }}>
            Loading...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke={colors.gray[200]} />
              <XAxis dataKey="name" stroke={colors.gray[500]} fontSize={12} />
              <YAxis stroke={colors.gray[500]} fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: colors.white,
                  border: `1px solid ${colors.gray[200]}`,
                  borderRadius: "8px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="views"
                stroke={colors.primary[500]}
                strokeWidth={2}
                dot={{ r: 4 }}
                activeDot={{ r: 6 }}
              />
              <Line
                type="monotone"
                dataKey="clicks"
                stroke={colors.success}
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
};
