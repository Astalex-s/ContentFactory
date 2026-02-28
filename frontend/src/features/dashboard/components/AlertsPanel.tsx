import React from "react";
import { useNavigate } from "react-router-dom";
import { Alert } from "../../../ui/components/Alert";
import { Card } from "../../../ui/components/Card";
import { DashboardAlerts } from "../types";

interface AlertsPanelProps {
  alerts: DashboardAlerts;
}

export const AlertsPanel: React.FC<AlertsPanelProps> = ({ alerts }) => {
  const navigate = useNavigate();

  return (
    <Card title="Уведомления">
      {alerts.products_no_content > 0 && (
        <Alert
          type="warning"
          title="Товары без контента"
          onClick={() => navigate("/products?filter=no_content")}
        >
          {alerts.products_no_content} товаров требуют генерации контента.
        </Alert>
      )}
      {alerts.publication_failed > 0 && (
        <Alert
          type="error"
          title="Ошибки публикаций"
          onClick={() => navigate("/publishing?status=failed")}
        >
          {alerts.publication_failed} публикаций завершились ошибкой.
        </Alert>
      )}
      {alerts.low_ctr_count > 0 && (
        <Alert
          type="warning"
          title="Низкая эффективность"
          onClick={() => navigate("/analytics?filter=low_ctr")}
        >
          {alerts.low_ctr_count} материалов имеют CTR ниже 2%.
        </Alert>
      )}
      {alerts.ai_errors_count > 0 && (
        <Alert type="error" title="Ошибки AI-генерации">
          {alerts.ai_errors_count} задач AI завершились ошибкой.
        </Alert>
      )}
      {alerts.products_no_content === 0 &&
        alerts.publication_failed === 0 &&
        alerts.low_ctr_count === 0 &&
        alerts.ai_errors_count === 0 && (
          <div style={{ color: "#666", textAlign: "center", padding: "1rem" }}>
            Нет активных уведомлений.
          </div>
        )}
    </Card>
  );
};
