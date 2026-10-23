import { useEffect, useState, type FormEvent } from "react";
import { ArrowDownLeft, ArrowUpRight, Plus } from "lucide-react";
import { all, api, body, date, type Movement, type Product } from "../api";
import {
  Empty,
  ErrorMessage,
  Loading,
  Modal,
  Pager,
  PageTitle,
  Submit,
  useApi,
} from "../components";

export default function InventoryPage({
  notify,
}: {
  notify: (message: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(0);
  const [productId, setProductId] = useState("");
  const [products, setProducts] = useState<Product[]>([]);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    all<Product>("/products/")
      .then((data) => {
        if (active) setProducts(data);
      })
      .catch((error) => {
        if (active) setError(error.message);
      });
    return () => {
      active = false;
    };
  }, [revision]);
  const resource = useApi<Movement[]>(
    `/inventory/movements?offset=${page * 20}&limit=21${productId ? `&product_id=${productId}` : ""}`,
    revision,
  );
  const records = resource.data?.slice(0, 20) || [];
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api("/inventory/adjustments", {
        method: "POST",
        body: body({
          product_id: Number(form.get("product_id")),
          quantity: Number(form.get("quantity")),
          reason: form.get("reason"),
        }),
      });
      setCreating(false);
      setRevision((value) => value + 1);
      setPage(0);
      notify("Stock adjusted and movement recorded.");
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <PageTitle
        eyebrow="EVERY UNIT ACCOUNTED FOR"
        title="Inventory"
        description="A clear trail of what comes in and what goes out."
        action={
          <button
            className="button primary"
            onClick={() => {
              setCreating(true);
              setError("");
            }}
          >
            <Plus size={17} />
            Adjust stock
          </button>
        }
      />
      <section className="card">
        <div className="toolbar">
          <div>
            <h2>Stock movements</h2>
            <p className="muted small-text">
              An auditable history of every change
            </p>
          </div>
          <select
            aria-label="Filter inventory by product"
            value={productId}
            onChange={(event) => {
              setProductId(event.target.value);
              setPage(0);
            }}
          >
            <option value="">All products</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>
        </div>
        {!creating && <ErrorMessage message={error} />}
        <ErrorMessage message={resource.error} />
        {resource.loading ? (
          <Loading />
        ) : !records.length ? (
          <Empty title="No movements yet">
            Stock changes will appear here automatically.
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Movement</th>
                  <th>Product</th>
                  <th>Reason</th>
                  <th className="number">Change</th>
                  <th className="number">Stock after</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {records.map((movement) => (
                  <tr key={movement.id}>
                    <td>
                      <div className="product-cell">
                        <span
                          className={`movement-icon ${movement.quantity > 0 ? "incoming" : "outgoing"}`}
                        >
                          {movement.quantity > 0 ? (
                            <ArrowDownLeft size={18} />
                          ) : (
                            <ArrowUpRight size={18} />
                          )}
                        </span>
                        <span className="record-id">
                          #{String(movement.id).padStart(4, "0")}
                        </span>
                      </div>
                    </td>
                    <td>
                      <strong>
                        {products.find(
                          (product) => product.id === movement.product_id,
                        )?.name || `Product #${movement.product_id}`}
                      </strong>
                      {movement.order_id && (
                        <small className="block muted">
                          Order #{movement.order_id}
                        </small>
                      )}
                    </td>
                    <td className="muted">{movement.reason}</td>
                    <td
                      className={`number strong ${movement.quantity > 0 ? "positive" : "negative"}`}
                    >
                      {movement.quantity > 0 ? "+" : ""}
                      {movement.quantity}
                    </td>
                    <td className="number">{movement.stock_after}</td>
                    <td className="muted">{date(movement.created_at)}</td>
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
        <Modal
          title="Adjust stock"
          subtitle="Every adjustment has a reason and a record."
          close={() => !busy && setCreating(false)}
        >
          <form onSubmit={save}>
            <ErrorMessage message={error} />
            <label>
              Product
              <select name="product_id" required defaultValue="" autoFocus>
                <option value="" disabled>
                  Select a product
                </option>
                {products.map((product) => (
                  <option value={product.id} key={product.id}>
                    {product.name} · {product.stock} in stock
                  </option>
                ))}
              </select>
            </label>
            <label>
              Quantity change
              <input
                name="quantity"
                type="number"
                required
                min="-1000000"
                max="1000000"
                step="1"
                placeholder="e.g. 10 for incoming, -3 for outgoing"
              />
            </label>
            <p className="form-hint">
              Use a positive number to add stock or a negative number to remove
              it.
            </p>
            <label>
              Reason
              <textarea
                name="reason"
                rows={3}
                required
                minLength={3}
                maxLength={255}
                placeholder="Delivery received, warehouse count…"
              />
            </label>
            <div className="form-actions">
              <button
                className="button ghost"
                type="button"
                disabled={busy}
                onClick={() => setCreating(false)}
              >
                Cancel
              </button>
              <Submit busy={busy}>Save adjustment</Submit>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
