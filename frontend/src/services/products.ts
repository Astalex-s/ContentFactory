/**
 * Product API service.
 * All product-related API calls go through this module.
 */
import { api } from "./api";
import type { Product, ProductFilters, ProductListResponse } from "@/types/product";

export interface ImportReport {
  total_rows: number;
  imported: number;
  skipped: number;
  errors: string[];
}

export const productsService = {
  async getProduct(id: string): Promise<Product | null> {
    try {
      const { data } = await api.get<Product>(`/products/${id}`);
      return data;
    } catch {
      return null;
    }
  },

  async getProducts(filters: ProductFilters = {}): Promise<ProductListResponse> {
    const params = new URLSearchParams();

    if (filters.category) params.set("category", filters.category);
    if (filters.min_price != null) params.set("min_price", String(filters.min_price));
    if (filters.max_price != null) params.set("max_price", String(filters.max_price));
    if (filters.sort_by) params.set("sort_by", filters.sort_by);
    params.set("page", String(filters.page ?? 1));
    params.set("page_size", String(filters.page_size ?? 20));

    const { data } = await api.get<ProductListResponse>(`/products?${params.toString()}`);
    return data;
  },

  async importFromCsv(file: File): Promise<ImportReport> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await api.post<ImportReport>("/products/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async deleteProduct(id: string): Promise<void> {
    await api.delete(`/products/${id}`);
  },

  async deleteAllProducts(): Promise<{ deleted: number }> {
    const { data } = await api.delete<{ deleted: number }>("/products/all");
    return data;
  },
};
