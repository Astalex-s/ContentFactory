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
    <Card title="Alerts & Issues">
      {alerts.products_no_content > 0 && (
        <Alert
          type="warning"
          title="Products without content"
          onClick={() => navigate("/products?filter=no_content")}
        >
          {alerts.products_no_content} products need content generation.
        </Alert>
      )}
      {alerts.publication_failed > 0 && (
        <Alert
          type="error"
          title="Publication errors"
          onClick={() => navigate("/publishing?status=failed")}
        >
          {alerts.publication_failed} publications failed.
        </Alert>
      )}
      {alerts.low_ctr_count > 0 && (
        <Alert
          type="warning"
          title="Low Performance"
          onClick={() => navigate("/analytics?filter=low_ctr")}
        >
          {alerts.low_ctr_count} items have CTR below 2%.
        </Alert>
      )}
      {alerts.ai_errors_count > 0 && (
        <Alert type="error" title="AI Generation Errors">
          {alerts.ai_errors_count} AI tasks failed.
        </Alert>
      )}
      {alerts.products_no_content === 0 &&
        alerts.publication_failed === 0 &&
        alerts.low_ctr_count === 0 &&
        alerts.ai_errors_count === 0 && (
          <div style={{ color: "#666", textAlign: "center", padding: "1rem" }}>
            No active alerts.
          </div>
        )}
    </Card>
  );
};
