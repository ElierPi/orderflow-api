import {
  ArrowRight,
  ArrowUpRight,
  Clock3,
  Package,
  ShoppingBag,
  Users,
  Wallet,
} from "lucide-react";
import { date, money, type Dashboard, type Order } from "../api";
import { Badge, Empty, ErrorMessage, Loading, useApi } from "../components";

export default function DashboardPage() {
  const stats = useApi<Dashboard>("/dashboard/");
  const orders = useApi<Order[]>("/orders/?limit=5");
  if (stats.loading) return <Loading />;
  if (stats.error || !stats.data)
    return (
      <ErrorMessage message={stats.error || "Unable to load dashboard."} />
    );
  const data = stats.data;
  const max = Math.max(...data.daily_value.map((day) => Number(day.total)), 1);
  return (
    <>
      <div className="overview-heading">
        <div>
          <div className="eyebrow">THE BIG PICTURE</div>
          <h1>
            Your operations, at a glance<span>.</span>
          </h1>
          <p>Everything you need to keep your business moving.</p>
        </div>
        <a className="button primary" href="#orders">
          View orders
          <ArrowUpRight size={16} />
        </a>
      </div>
      <div className="metric-grid">
        {[
          {
            label: "Total order value",
            value: money(data.order_value),
            compact: new Intl.NumberFormat("en-US", {
              style: "currency",
              currency: import.meta.env.VITE_CURRENCY || "COP",
              notation: "compact",
              maximumFractionDigits: 2,
            }).format(Number(data.order_value)),
            icon: Wallet,
            detail: "Excludes cancelled orders",
            primary: true,
          },
          {
            label: "Orders",
            value: data.orders,
            icon: ShoppingBag,
            detail: `${data.pending_orders} awaiting confirmation`,
          },
          {
            label: "Active products",
            value: data.products,
            icon: Package,
            detail: "Available in your catalog",
          },
          {
            label: "Customers",
            value: data.customers,
            icon: Users,
            detail: "Active customer relationships",
          },
        ].map((item) => (
          <section
            className={`metric ${item.primary ? "featured" : ""}`}
            key={item.label}
          >
            <div>
              <span>{item.label}</span>
              <item.icon size={19} strokeWidth={1.6} />
            </div>
            <strong title={String(item.value)}>
              <span className="metric-full">{item.value}</span>
              <span className="metric-compact">
                {item.compact ?? item.value}
              </span>
            </strong>
            <small>{item.detail}</small>
          </section>
        ))}
      </div>
      <div className="dashboard-middle">
        <section className="card chart-card">
          <div className="card-heading">
            <div>
              <h2>A week in motion</h2>
              <p>Order value over the last 7 days · UTC</p>
            </div>
            <span className="chart-legend">
              <i />
              Order value
            </span>
          </div>
          <div
            className="chart"
            role="img"
            aria-label="Daily order value over the past seven days"
          >
            {data.daily_value.map((day, index) => (
              <div className="chart-column" key={day.date}>
                <div className="bar-track">
                  <div
                    className={`bar ${index === 6 ? "today" : ""}`}
                    style={{ height: `${(Number(day.total) / max) * 100}%` }}
                  />
                  <span className="bar-tooltip">{money(day.total)}</span>
                </div>
                <span>
                  {new Date(`${day.date}T12:00:00Z`).toLocaleDateString(
                    "en-US",
                    { weekday: "short", timeZone: "UTC" },
                  )}
                </span>
                <span className="sr-only">
                  {day.date}: {money(day.total)}
                </span>
              </div>
            ))}
          </div>
          <div className="chart-caption">
            <span>Each order starts with a little momentum.</span>
            <span>Last 7 days</span>
          </div>
        </section>
        <section className="card low-stock">
          <div className="card-heading">
            <div>
              <h2>A little attention</h2>
              <p>Products with 5 units or fewer</p>
            </div>
            <span className="attention-dot" />
          </div>
          {data.low_stock.length ? (
            <div className="stock-list">
              {data.low_stock.map((product) => (
                <div key={product.id}>
                  <span className="product-icon">
                    <Package size={19} />
                  </span>
                  <div>
                    <strong>{product.name}</strong>
                    <small>Product #{product.id}</small>
                  </div>
                  <span
                    className={`stock-pill ${product.stock === 0 ? "out" : ""}`}
                  >
                    {product.stock === 0
                      ? "Out of stock"
                      : `${product.stock} left`}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <Empty title="All stocked up">
              Your active products have healthy stock levels.
            </Empty>
          )}
          <a className="card-link" href="#inventory">
            Go to inventory
            <ArrowRight size={15} />
          </a>
        </section>
      </div>
      <section className="card">
        <div className="card-heading">
          <div>
            <h2>Recent orders</h2>
            <p>The latest activity across your workspace</p>
          </div>
          <a className="text-link" href="#orders">
            All orders
            <ArrowRight size={15} />
          </a>
        </div>
        <ErrorMessage message={orders.error} />
        {orders.loading ? (
          <Loading />
        ) : !orders.data?.length ? (
          <Empty title="Your first order starts here">
            Add products and a customer, then create an order.
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th className="number">Total</th>
                </tr>
              </thead>
              <tbody>
                {orders.data.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <span className="record-id">
                        #OF-{String(order.id).padStart(4, "0")}
                      </span>
                    </td>
                    <td>Customer #{order.customer_id}</td>
                    <td className="muted">{date(order.created_at)}</td>
                    <td>
                      <Badge value={order.status} />
                    </td>
                    <td className="number strong">{money(order.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <div className="overview-note">
        <Clock3 size={15} />
        <span>A clear view today. A better decision tomorrow.</span>
      </div>
    </>
  );
}
