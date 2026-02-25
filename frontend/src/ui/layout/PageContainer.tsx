import React from "react";
import { spacing } from "../theme";

export const PageContainer: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div
      style={{
        maxWidth: "1400px",
        margin: "0 auto",
        padding: spacing.lg,
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      {children}
    </div>
  );
};
