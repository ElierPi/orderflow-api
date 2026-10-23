export type User = {
  id: number;
  email: string;
  role: "admin" | "operator";
  active: boolean;
};
export type Product = {
  id: number;
  name: string;
  description: string | null;
  price: string;
  stock: number;
  active: boolean;
};
export type Customer = {
  id: number;
  name: string;
  email: string;
  phone: string | null;
  active: boolean;
};
export type OrderStatus = "pending" | "confirmed" | "shipped" | "cancelled";
export type Order = {
  id: number;
  customer_id: number;
  status: OrderStatus;
  total: string;
  created_at: string;
  items: {
    product_id: number;
    product_name: string;
    quantity: number;
    unit_price: string;
    subtotal: string;
  }[];
};
export type Movement = {
  id: number;
  product_id: number;
  order_id: number | null;
  actor_id: number | null;
  quantity: number;
  stock_after: number;
  reason: string;
  created_at: string;
};
export type Dashboard = {
  products: number;
  customers: number;
  orders: number;
  pending_orders: number;
  order_value: string;
  low_stock: Product[];
  daily_value: { date: string; total: string }[];
};

// Short-lived access token stays in memory. A reload requires signing in again.
let accessToken = "";
export function setToken(value: string) {
  accessToken = value;
}
const base = import.meta.env.VITE_API_URL || "/api";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
  let response: Response;
  try {
    response = await fetch(`${base}${path}`, { ...options, headers });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError")
      throw error;
    throw new Error(
      "Cannot reach OrderFlow. Check the API connection and try again.",
    );
  }
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    const detail = data.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map(
                (item: { loc: string[]; msg: string }) =>
                  `${item.loc.slice(1).join(".")}: ${item.msg}`,
              )
              .join("; ")
          : `Request failed (${response.status}). Please try again.`;
    if (response.status === 401 && accessToken)
      window.dispatchEvent(new Event("session-expired"));
    throw new ApiError(response.status, message);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export async function all<T>(path: string): Promise<T[]> {
  const result: T[] = [];
  for (let offset = 0; ; offset += 100) {
    const page = await api<T[]>(`${path}?limit=100&offset=${offset}`);
    result.push(...page);
    if (page.length < 100) return result;
  }
}

export const money = (value: string | number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: import.meta.env.VITE_CURRENCY || "COP",
    maximumFractionDigits: 2,
  }).format(Number(value));
export const date = (value: string) =>
  new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
export const body = (data: unknown) => JSON.stringify(data);
