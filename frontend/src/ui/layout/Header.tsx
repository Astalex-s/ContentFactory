import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { colors, spacing } from "../theme";

export const Header: React.FC = () => {
  const navigate = useNavigate();

  return (
    <header
      style={{
        height: "64px",
        backgroundColor: colors.white,
        borderBottom: `1px solid ${colors.gray[200]}`,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: `0 ${spacing.lg}`,
        position: "sticky",
        top: 0,
        zIndex: 9,
        flexShrink: 0,
      }}
    >
      <div style={{ fontWeight: 600, fontSize: "16px", color: colors.gray[900] }}>
        {/* Breadcrumbs or Page Title could go here */}
      </div>
      <div style={{ display: "flex", gap: spacing.sm, flexWrap: "wrap" }}>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => navigate("/products/import")}
        >
          Import Products
        </Button>
        <Button
          variant="primary"
          size="sm"
          onClick={() => navigate("/content/generate")}
        >
          Generate Content
        </Button>
      </div>
    </header>
  );
};
