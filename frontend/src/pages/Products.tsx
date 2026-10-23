import { useState, type FormEvent } from "react";
import { Archive, Package, Pencil, Plus, Search } from "lucide-react";
import { api, body, money, type Product } from "../api";
import {
  Empty,
  ErrorMessage,
  Loading,
  Modal,
  Pager,
  PageTitle,
  Submit,
  useApi,
  useSearch,
} from "../components";

export default function ProductsPage({
  admin,
  notify,
}: {
  admin: boolean;
  notify: (message: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(0);
  const { search, setSearch, query } = useSearch();
  const [stock, setStock] = useState("");
  const [editing, setEditing] = useState<Product | "new" | null>(null);
  const [archive, setArchive] = useState<Product | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const resource = useApi<Product[]>(
    `/products/?q=${encodeURIComponent(query)}&offset=${page * 20}&limit=21${stock ? `&in_stock=${stock}` : ""}`,
    revision,
  );
  const records = resource.data?.slice(0, 20) || [];
  function changed(message: string) {
    setEditing(null);
    setArchive(null);
    setRevision((value) => value + 1);
    notify(message);
  }
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = Object.fromEntries(new FormData(event.currentTarget));
    try {
      await api(`/products/${editing !== "new" && editing ? editing.id : ""}`, {
        method: editing === "new" ? "POST" : "PUT",
        body: body({
          ...form,
          description: form.description || null,
          stock: Number(form.stock),
        }),
      });
      changed(
        editing === "new"
          ? "Product added to your catalog."
          : "Product updated.",
      );
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function remove() {
    setBusy(true);
    setError("");
    try {
      await api(`/products/${archive!.id}`, { method: "DELETE" });
      changed("Product archived. Its history is preserved.");
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const product = editing && editing !== "new" ? editing : null;
  return (
    <>
      <PageTitle
        eyebrow="YOUR CATALOG"
        title="Products"
        description="A home for everything you sell."
        action={
          admin && (
            <button
              className="button primary"
              onClick={() => {
                setEditing("new");
                setError("");
              }}
            >
              <Plus size={17} />
              Add product
            </button>
          )
        }
      />
      <section className="card">
        <div className="toolbar">
          <label className="search">
            <Search size={18} />
            <input
              aria-label="Search products"
              placeholder="Search products or descriptions…"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(0);
              }}
            />
          </label>
          <select
            aria-label="Filter stock"
            value={stock}
            onChange={(event) => {
              setStock(event.target.value);
              setPage(0);
            }}
          >
            <option value="">All stock levels</option>
            <option value="true">In stock</option>
            <option value="false">Out of stock</option>
          </select>
        </div>
        <ErrorMessage message={resource.error} />
        {resource.loading ? (
          <Loading />
        ) : !records.length ? (
          <Empty title="No products found">
            {query
              ? "Try a different search."
              : "Build your catalog by adding your first product."}
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Description</th>
                  <th className="number">Price</th>
                  <th className="number">Stock</th>
                  {admin && <th className="number">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {records.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <div className="product-cell">
                        <span className="product-icon">
                          <Package size={20} />
                        </span>
                        <div>
                          <strong>{product.name}</strong>
                          <small>#{String(product.id).padStart(4, "0")}</small>
                        </div>
                      </div>
                    </td>
                    <td className="description-cell muted">
                      {product.description || "—"}
                    </td>
                    <td className="number strong">{money(product.price)}</td>
                    <td className="number">
                      <span
                        className={`stock-pill ${product.stock === 0 ? "out" : product.stock <= 5 ? "" : "healthy"}`}
                      >
                        {product.stock} units
                      </span>
                    </td>
                    {admin && (
                      <td>
                        <div className="row-actions">
                          <button
                            className="icon-button"
                            aria-label={`Edit ${product.name}`}
                            onClick={() => {
                              setEditing(product);
                              setError("");
                            }}
                          >
                            <Pencil size={16} />
                          </button>
                          <button
                            className="icon-button"
                            aria-label={`Archive ${product.name}`}
                            onClick={() => {
                              setArchive(product);
                              setError("");
                            }}
                          >
                            <Archive size={16} />
                          </button>
                        </div>
                      </td>
                    )}
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
      {editing && (
        <Modal
          title={product ? "Edit product" : "Add a product"}
          subtitle="The details that make your catalog useful."
          close={() => !busy && setEditing(null)}
        >
          <form onSubmit={save}>
            <ErrorMessage message={error} />
            <label>
              Product name
              <input
                name="name"
                required
                minLength={2}
                maxLength={100}
                defaultValue={product?.name}
                autoFocus
              />
            </label>
            <label>
              Description
              <textarea
                name="description"
                maxLength={255}
                rows={3}
                defaultValue={product?.description || ""}
              />
            </label>
            <div className="form-grid">
              <label>
                Price ({import.meta.env.VITE_CURRENCY || "COP"})
                <input
                  name="price"
                  type="number"
                  required
                  min="0.01"
                  max="9999999999.99"
                  step="0.01"
                  defaultValue={product?.price}
                />
              </label>
              <label>
                Stock
                <input
                  name="stock"
                  type="number"
                  required
                  min="0"
                  max="2147483647"
                  step="1"
                  defaultValue={product?.stock ?? 0}
                />
              </label>
            </div>
            <p className="form-hint">
              Stock changes are recorded in your inventory history.
            </p>
            <div className="form-actions">
              <button
                type="button"
                className="button ghost"
                disabled={busy}
                onClick={() => setEditing(null)}
              >
                Cancel
              </button>
              <Submit busy={busy}>
                {product ? "Save changes" : "Add product"}
              </Submit>
            </div>
          </form>
        </Modal>
      )}
      {archive && (
        <Modal
          title="Archive this product?"
          close={() => !busy && setArchive(null)}
        >
          <p>
            “{archive.name}” will leave the active catalog. Existing orders and
            inventory history stay available.
          </p>
          <ErrorMessage message={error} />
          <div className="form-actions">
            <button
              className="button ghost"
              disabled={busy}
              onClick={() => setArchive(null)}
            >
              Keep product
            </button>
            <button className="button danger" disabled={busy} onClick={remove}>
              {busy ? "Archiving…" : "Archive product"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
