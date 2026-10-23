import { useEffect, useState, type FormEvent } from "react";
import { ArrowRight, Plus, Trash2 } from "lucide-react";
import {
  all,
  api,
  body,
  date,
  money,
  type Customer,
  type Order,
  type OrderStatus,
  type Product,
} from "../api";
import {
  Badge,
  Empty,
  ErrorMessage,
  Loading,
  Modal,
  Pager,
  PageTitle,
  Submit,
  useApi,
} from "../components";

function OrderForm({ close, saved }: { close: () => void; saved: () => void }) {
  const [products, setProducts] = useState<Product[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [lines, setLines] = useState([{ product_id: "", quantity: 1 }]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    Promise.all([all<Product>("/products/"), all<Customer>("/customers/")])
      .then(([products, customers]) => {
        if (active) {
          setProducts(products);
          setCustomers(customers);
        }
      })
      .catch((error) => {
        if (active) setError(error.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  const total = lines.reduce(
    (total, line) =>
      total +
      Number(
        products.find((p) => p.id === Number(line.product_id))?.price || 0,
      ) *
        line.quantity,
    0,
  );
  function change(
    index: number,
    key: "product_id" | "quantity",
    value: string,
  ) {
    setLines(
      lines.map((line, i) =>
        i === index
          ? { ...line, [key]: key === "quantity" ? Number(value) : value }
          : line,
      ),
    );
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api<Order>("/orders/", {
        method: "POST",
        body: body({
          customer_id: Number(form.get("customer_id")),
          items: lines.map((line) => ({
            product_id: Number(line.product_id),
            quantity: line.quantity,
          })),
        }),
      });
      saved();
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title="Create an order"
      subtitle="Choose a customer. Add products. Keep things moving."
      close={() => !busy && close()}
    >
      {loading ? (
        <Loading />
      ) : (
        <form onSubmit={submit}>
          <ErrorMessage message={error} />
          {!customers.length || !products.length ? (
            <Empty title="A few things first">
              Add at least one product and one customer before creating an
              order.
            </Empty>
          ) : (
            <>
              <label>
                Customer
                <select name="customer_id" required defaultValue="" autoFocus>
                  <option value="" disabled>
                    Select a customer
                  </option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name} · {customer.email}
                    </option>
                  ))}
                </select>
              </label>
              <div className="form-section-title">ORDER ITEMS</div>
              {lines.map((line, index) => (
                <div className="order-line" key={index}>
                  <label>
                    Product
                    <select
                      aria-label={`Product ${index + 1}`}
                      required
                      value={line.product_id}
                      onChange={(event) =>
                        change(index, "product_id", event.target.value)
                      }
                    >
                      <option value="" disabled>
                        Select a product
                      </option>
                      {products.map((product) => (
                        <option
                          value={product.id}
                          key={product.id}
                          disabled={
                            product.stock === 0 ||
                            lines.some(
                              (other, i) =>
                                i !== index &&
                                Number(other.product_id) === product.id,
                            )
                          }
                        >
                          {product.name} · {product.stock} available ·{" "}
                          {money(product.price)}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Quantity
                    <input
                      aria-label={`Quantity ${index + 1}`}
                      type="number"
                      min="1"
                      max="1000000"
                      step="1"
                      value={line.quantity}
                      required
                      onChange={(event) =>
                        change(index, "quantity", event.target.value)
                      }
                    />
                  </label>
                  <button
                    type="button"
                    className="icon-button"
                    aria-label={`Remove item ${index + 1}`}
                    disabled={lines.length === 1}
                    onClick={() =>
                      setLines(lines.filter((_, i) => i !== index))
                    }
                  >
                    <Trash2 size={17} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="button ghost small"
                disabled={lines.length >= Math.min(100, products.length)}
                onClick={() =>
                  setLines([...lines, { product_id: "", quantity: 1 }])
                }
              >
                <Plus size={15} />
                Add another product
              </button>
              <div className="order-total">
                <span>
                  Estimated total
                  <strong>Calculated by the API when saved</strong>
                </span>
                <b>{money(total)}</b>
              </div>
              <p className="form-hint">
                Creating an order immediately reserves its stock. Cancellation
                restores it.
              </p>
            </>
          )}
          <div className="form-actions">
            <button
              type="button"
              className="button ghost"
              disabled={busy}
              onClick={close}
            >
              Cancel
            </button>
            {!!customers.length && !!products.length && (
              <Submit busy={busy}>
                Create order
                <ArrowRight size={16} />
              </Submit>
            )}
          </div>
        </form>
      )}
    </Modal>
  );
}

export default function OrdersPage({
  notify,
}: {
  notify: (message: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(0);
  const [status, setStatus] = useState("");
  const [creating, setCreating] = useState(false);
  const [selected, setSelected] = useState<Order | null>(null);
  const [transition, setTransition] = useState<OrderStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const resource = useApi<Order[]>(
    `/orders/?offset=${page * 20}&limit=21${status ? `&status=${status}` : ""}`,
    revision,
  );
  const records = resource.data?.slice(0, 20) || [];
  async function updateStatus() {
    setBusy(true);
    setError("");
    try {
      const order = await api<Order>(`/orders/${selected!.id}/status`, {
        method: "PATCH",
        body: body({ status: transition }),
      });
      setSelected(order);
      setTransition(null);
      setRevision((value) => value + 1);
      notify(`Order #${order.id} ${order.status}.`);
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="FROM CART TO CUSTOMER"
        title="Orders"
        description="Every order. Every detail. All in one place."
        action={
          <button className="button primary" onClick={() => setCreating(true)}>
            <Plus size={17} />
            Create order
          </button>
        }
      />
      <section className="card">
        <div className="toolbar">
          <div className="filter-tabs" aria-label="Filter orders">
            {["", "pending", "confirmed", "shipped", "cancelled"].map(
              (value) => (
                <button
                  key={value}
                  className={status === value ? "selected" : ""}
                  onClick={() => {
                    setStatus(value);
                    setPage(0);
                  }}
                >
                  {value || "All orders"}
                </button>
              ),
            )}
          </div>
        </div>
        <ErrorMessage message={resource.error} />
        {resource.loading ? (
          <Loading />
        ) : !records.length ? (
          <Empty title="No orders here yet">
            Your next order is a fresh start.
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Order</th>
                  <th>Customer</th>
                  <th>Date</th>
                  <th>Items</th>
                  <th>Status</th>
                  <th className="number">Total</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {records.map((order) => (
                  <tr key={order.id}>
                    <td className="record-id">
                      #OF-{String(order.id).padStart(4, "0")}
                    </td>
                    <td>Customer #{order.customer_id}</td>
                    <td className="muted">{date(order.created_at)}</td>
                    <td>
                      {order.items.reduce(
                        (total, item) => total + item.quantity,
                        0,
                      )}{" "}
                      units
                    </td>
                    <td>
                      <Badge value={order.status} />
                    </td>
                    <td className="number strong">{money(order.total)}</td>
                    <td>
                      <button
                        className="text-link"
                        aria-label={`View order ${order.id}`}
                        onClick={() => {
                          setSelected(order);
                          setTransition(null);
                          setError("");
                        }}
                      >
                        View
                        <ArrowRight size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pager
          page={page}
          next={(resource.data?.length || 0) > 20}
          setPage={setPage}
          count={records.length}
        />
      </section>
      {creating && (
        <OrderForm
          close={() => setCreating(false)}
          saved={() => {
            setCreating(false);
            setRevision((value) => value + 1);
            setPage(0);
            setStatus("");
            notify("Order created and inventory reserved.");
          }}
        />
      )}
      {selected && (
        <Modal
          title={`Order #OF-${String(selected.id).padStart(4, "0")}`}
          subtitle={`${date(selected.created_at)} · Customer #${selected.customer_id}`}
          close={() => !busy && setSelected(null)}
        >
          <div className="order-status">
            <Badge value={selected.status} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th className="number">Qty</th>
                  <th className="number">Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {selected.items.map((item) => (
                  <tr key={item.product_id}>
                    <td>
                      <strong>{item.product_name}</strong>
                      <small className="block muted">
                        {money(item.unit_price)} / unit
                      </small>
                    </td>
                    <td className="number">{item.quantity}</td>
                    <td className="number strong">{money(item.subtotal)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="order-total">
            <span>Order total</span>
            <b>{money(selected.total)}</b>
          </div>
          <ErrorMessage message={error} />
          {transition ? (
            <div className="transition-confirm">
              <p>
                {transition === "cancelled"
                  ? "Cancel this order and restore all reserved stock?"
                  : `Mark this order as ${transition}?`}
              </p>
              <div className="form-actions">
                <button
                  className="button ghost"
                  disabled={busy}
                  onClick={() => setTransition(null)}
                >
                  Go back
                </button>
                <button
                  className={`button ${transition === "cancelled" ? "danger" : "primary"}`}
                  disabled={busy}
                  onClick={updateStatus}
                >
                  {busy ? "Updating…" : "Confirm change"}
                </button>
              </div>
            </div>
          ) : (
            <div className="form-actions">
              {["pending", "confirmed"].includes(selected.status) && (
                <button
                  className="button ghost danger-text"
                  onClick={() => setTransition("cancelled")}
                >
                  Cancel order
                </button>
              )}
              {selected.status === "pending" && (
                <button
                  className="button primary"
                  onClick={() => setTransition("confirmed")}
                >
                  Confirm order
                </button>
              )}
              {selected.status === "confirmed" && (
                <button
                  className="button primary"
                  onClick={() => setTransition("shipped")}
                >
                  Mark as shipped
                </button>
              )}
            </div>
          )}
        </Modal>
      )}
    </>
  );
}
