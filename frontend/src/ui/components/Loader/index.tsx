import React from "react";
import { colors } from "../../theme";

export const Loader: React.FC = () => {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        padding: "2rem",
      }}
    >
      <div
        style={{
          width: "24px",
          height: "24px",
          border: `3px solid ${colors.gray[200]}`,
          borderTopColor: colors.primary[500],
          borderRadius: "50%",
          animation: "spin 1s linear infinite",
        }}
      />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export const Skeleton: React.FC<{ height?: string | number; width?: string | number }> = ({
  height = "20px",
  width = "100%",
}) => {
  return (
    <div
      style={{
        height,
        width,
        backgroundColor: colors.gray[200],
        borderRadius: "4px",
        animation: "pulse 1.5s ease-in-out infinite",
      }}
    >
      <style>{`
        @keyframes pulse {
          0% { opacity: 0.6; }
          50% { opacity: 1; }
          100% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
};
