/** Product entity from API */
export interface Product {
  id: string;
  name: string;
  description: string | null;
  category: string | null;
  price: number | null;
  popularity_score: number | null;
  marketplace_url: string | null;
}

/** Filters for product list */
export interface ProductFilters {
  category?: string;
  min_price?: number;
  max_price?: number;
  sort_by?: "price" | "popularity";
  page?: number;
  page_size?: number;
}

/** Paginated product list response */
export interface ProductListResponse {
  items: Product[];
  total: number;
  page: number;
  page_size: number;
}
