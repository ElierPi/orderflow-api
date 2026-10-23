import { useState, type FormEvent } from "react";
import { Archive, Pencil, Plus, Search } from "lucide-react";
import { api, body, type Customer } from "../api";
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

export default function CustomersPage({
  admin,
  notify,
}: {
  admin: boolean;
  notify: (message: string) => void;
}) {
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(0);
  const { search, setSearch, query } = useSearch();
  const [editing, setEditing] = useState<Customer | "new" | null>(null);
  const [archive, setArchive] = useState<Customer | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const resource = useApi<Customer[]>(
    `/customers/?q=${encodeURIComponent(query)}&offset=${page * 20}&limit=21`,
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
      await api(
        `/customers/${editing !== "new" && editing ? editing.id : ""}`,
        {
          method: editing === "new" ? "POST" : "PUT",
          body: body({ ...form, phone: form.phone || null }),
        },
      );
      changed(editing === "new" ? "Customer added." : "Customer updated.");
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
      await api(`/customers/${archive!.id}`, { method: "DELETE" });
      changed("Customer archived. Their orders are preserved.");
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const customer = editing && editing !== "new" ? editing : null;
  return (
    <>
      <PageTitle
        eyebrow="THE PEOPLE BEHIND THE ORDERS"
        title="Customers"
        description="Keep your customer relationships in good company."
        action={
          <button
            className="button primary"
            onClick={() => {
              setEditing("new");
              setError("");
            }}
          >
            <Plus size={17} />
            Add customer
          </button>
        }
      />
      <section className="card">
        <div className="toolbar">
          <label className="search">
            <Search size={18} />
            <input
              aria-label="Search customers"
              placeholder="Search by name or email…"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(0);
              }}
            />
          </label>
          <span className="muted small-text">Active customers</span>
        </div>
        <ErrorMessage message={resource.error} />
        {resource.loading ? (
          <Loading />
        ) : !records.length ? (
          <Empty title="No customers found">
            Add your first customer to start taking orders.
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Email address</th>
                  <th>Phone</th>
                  <th className="number">Actions</th>
                </tr>
              </thead>
              <tbody>
                {records.map((customer) => (
                  <tr key={customer.id}>
                    <td>
                      <div className="product-cell">
                        <span className="avatar customer-avatar">
                          {customer.name.slice(0, 1)}
                        </span>
                        <div>
                          <strong>{customer.name}</strong>
                          <small>Customer #{customer.id}</small>
                        </div>
                      </div>
                    </td>
                    <td>{customer.email}</td>
                    <td className="muted">{customer.phone || "—"}</td>
                    <td>
                      <div className="row-actions">
                        <button
                          className="icon-button"
                          aria-label={`Edit ${customer.name}`}
                          onClick={() => {
                            setEditing(customer);
                            setError("");
                          }}
                        >
                          <Pencil size={16} />
                        </button>
                        {admin && (
                          <button
                            className="icon-button"
                            aria-label={`Archive ${customer.name}`}
                            onClick={() => {
                              setArchive(customer);
                              setError("");
                            }}
                          >
                            <Archive size={16} />
                          </button>
                        )}
                      </div>
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
      {editing && (
        <Modal
          title={customer ? "Edit customer" : "Add a customer"}
          subtitle="A good relationship starts with the details."
          close={() => !busy && setEditing(null)}
        >
          <form onSubmit={save}>
            <ErrorMessage message={error} />
            <label>
              Full name
              <input
                name="name"
                required
                minLength={2}
                maxLength={100}
                defaultValue={customer?.name}
                autoFocus
              />
            </label>
            <label>
              Email address
              <input
                name="email"
                type="email"
                required
                maxLength={254}
                defaultValue={customer?.email}
              />
            </label>
            <label>
              Phone number
              <input
                name="phone"
                type="tel"
                maxLength={30}
                defaultValue={customer?.phone || ""}
              />
            </label>
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
                {customer ? "Save changes" : "Add customer"}
              </Submit>
            </div>
          </form>
        </Modal>
      )}
      {archive && (
        <Modal
          title="Archive this customer?"
          close={() => !busy && setArchive(null)}
        >
          <p>
            “{archive.name}” will leave the active list. Their order history
            will remain available.
          </p>
          <ErrorMessage message={error} />
          <div className="form-actions">
            <button
              className="button ghost"
              disabled={busy}
              onClick={() => setArchive(null)}
            >
              Keep customer
            </button>
            <button className="button danger" disabled={busy} onClick={remove}>
              {busy ? "Archiving…" : "Archive customer"}
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
