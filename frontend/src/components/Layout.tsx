import { Outlet, useNavigate, useLocation } from "react-router-dom";

const btnStyle: React.CSSProperties = {
  padding: "0.5rem 1rem",
  background: "#666",
  color: "#fff",
  border: "none",
  borderRadius: 6,
  cursor: "pointer",
};

export function Layout() {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === "/";

  return (
    <div>
      <header
        style={{
          padding: "0.75rem 1.5rem",
          borderBottom: "1px solid #ddd",
          background: "#fafafa",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <button
          onClick={() => navigate("/")}
          style={{
            ...btnStyle,
            background: isHome ? "#444" : "#0066cc",
          }}
        >
          На главную
        </button>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
