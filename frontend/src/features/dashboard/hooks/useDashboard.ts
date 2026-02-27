import { useState, useEffect, useCallback } from "react";
import { AxiosError } from "axios";
import { dashboardService } from "../services/dashboardService";
import { DashboardStats } from "../types";

export const useDashboard = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dashboardService.getStats();
      setStats(data);
    } catch (err: unknown) {
      const status = err instanceof AxiosError ? err.response?.status : undefined;
      const msg =
        status !== undefined
          ? `Ошибка ${status} (сервер недоступен)`
          : err instanceof Error
            ? err.message
            : "Failed to load dashboard stats";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
};
