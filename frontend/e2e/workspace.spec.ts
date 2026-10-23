import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

test("real workspace: catalog, customers, orders, cancellation, inventory", async ({
  page,
}) => {
  const credentials = JSON.parse(
    readFileSync(path.resolve("../.tools/e2e-credentials.json"), "utf-8"),
  );
  await page.goto("/");
  await page
    .getByLabel("Email address", { exact: true })
    .fill(credentials.email);
  await page.getByLabel("Password", { exact: true }).fill(credentials.password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Your operations, at a glance." }),
  ).toBeVisible();
  await expect(page.getByText("Your first order starts here")).toBeVisible();
  await page.getByRole("link", { name: "Products", exact: true }).click();
  await page.getByRole("button", { name: "Add product", exact: true }).click();
  await page.getByLabel("Product name").fill("Studio keyboard");
  await page
    .getByRole("textbox", { name: "Description", exact: true })
    .fill("Compact wireless keyboard for creative work");
  await page.getByLabel("Price (COP)").fill("190000");
  await page.getByLabel("Stock", { exact: true }).fill("10");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add product", exact: true })
    .click();
  await expect(
    page.getByText("Studio keyboard", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit Studio keyboard" }).click();
  await expect(
    page.getByRole("textbox", { name: "Description", exact: true }),
  ).toHaveValue("Compact wireless keyboard for creative work");
  await page
    .getByRole("textbox", { name: "Description", exact: true })
    .fill("Low profile keys. Quiet, comfortable typing.");
  await page.getByRole("button", { name: "Save changes" }).click();
  await expect(
    page.getByRole("cell", {
      name: "Low profile keys. Quiet, comfortable typing.",
    }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/products.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Customers", exact: true }).click();
  await page.getByRole("button", { name: "Add customer", exact: true }).click();
  await page.getByLabel("Full name").fill("Alex Morgan");
  await page
    .getByLabel("Email address", { exact: true })
    .fill("alex@example.com");
  await page.getByLabel("Phone number").fill("+57 300 000 0000");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Add customer", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "alex@example.com" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Orders", exact: true }).click();
  await page.getByRole("button", { name: "Create order", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Customer", exact: true })
    .selectOption({ index: 1 });
  await page
    .getByLabel("Product 1", { exact: true })
    .selectOption({ index: 1 });
  await page.getByLabel("Quantity 1", { exact: true }).fill("2");
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Create order", exact: true })
    .click();
  await expect(
    page.getByRole("cell", { name: "pending", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "View order 1", exact: true }).click();
  await expect(
    page.getByRole("dialog").getByText("Studio keyboard"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Cancel order", exact: true }).click();
  await page.getByRole("button", { name: "Confirm change" }).click();
  await expect(
    page.getByRole("dialog").getByText("cancelled", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("link", { name: "Products", exact: true }).click();
  await expect(page.getByText("10 units", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Inventory", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "Order cancellation", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Adjust stock" }).click();
  await page
    .getByRole("combobox", { name: "Product", exact: true })
    .selectOption({ index: 1 });
  await page.getByLabel("Quantity change").fill("-6");
  await page
    .getByLabel("Reason", { exact: true })
    .fill("Warehouse count correction");
  await page.getByRole("button", { name: "Save adjustment" }).click();
  await expect(
    page.getByRole("cell", { name: "Warehouse count correction" }),
  ).toBeVisible();
  // Populate presentation records through the real API, in the same disposable
  // schema. These are explicitly test records, never mocked API responses.
  const login = await page.request.post("http://127.0.0.1:9001/auth/login", {
    data: credentials,
  });
  expect(login.ok()).toBeTruthy();
  const headers = {
    Authorization: `Bearer ${(await login.json()).access_token}`,
  };
  const createdProducts = [];
  for (const data of [
    {
      name: "Contour monitor",
      description: "27-inch display for a little more perspective.",
      price: "980000.00",
      stock: 16,
    },
    {
      name: "Desk lamp",
      description: "Warm light for your next good idea.",
      price: "89000.00",
      stock: 3,
    },
    {
      name: "Notebook set",
      description: "A fresh page for every plan.",
      price: "24000.00",
      stock: 32,
    },
    {
      name: "USB-C dock",
      description: "One connection. Everything in reach.",
      price: "240000.00",
      stock: 8,
    },
  ]) {
    const response = await page.request.post(
      "http://127.0.0.1:9001/products/",
      { headers, data },
    );
    expect(response.status()).toBe(201);
    createdProducts.push(await response.json());
  }
  const createdCustomers = [];
  for (const data of [
    { name: "Sam Rivera", email: "sam@example.com" },
    { name: "Jordan Lee", email: "jordan@example.com" },
  ]) {
    const response = await page.request.post(
      "http://127.0.0.1:9001/customers/",
      { headers, data },
    );
    expect(response.status()).toBe(201);
    createdCustomers.push(await response.json());
  }
  for (let i = 0; i < 5; i++) {
    const response = await page.request.post("http://127.0.0.1:9001/orders/", {
      headers,
      data: {
        customer_id: createdCustomers[i % 2].id,
        items: [
          { product_id: createdProducts[0].id, quantity: 1 },
          { product_id: createdProducts[2].id, quantity: 2 },
        ],
      },
    });
    expect(response.status()).toBe(201);
    const order = await response.json();
    if (i < 2 || i === 3) {
      expect(
        (
          await page.request.patch(
            `http://127.0.0.1:9001/orders/${order.id}/status`,
            { headers, data: { status: "confirmed" } },
          )
        ).ok(),
      ).toBeTruthy();
    }
    if (i === 0) {
      expect(
        (
          await page.request.patch(
            `http://127.0.0.1:9001/orders/${order.id}/status`,
            { headers, data: { status: "shipped" } },
          )
        ).ok(),
      ).toBeTruthy();
    }
  }
  if (
    await page.getByRole("button", { name: "Dismiss notification" }).count()
  ) {
    await page.getByRole("button", { name: "Dismiss notification" }).click();
  }
  await page.getByRole("link", { name: "Products", exact: true }).click();
  await expect(
    page.getByText("Contour monitor", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/products.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Orders", exact: true }).click();
  await expect(
    page.getByRole("cell", { name: "shipped", exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/orders.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.getByText("4 left", { exact: true })).toBeVisible();
  await page.screenshot({
    path: "../docs/screenshots/dashboard.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(
    page.getByRole("heading", { name: "Your operations, at a glance." }),
  ).toBeVisible();
  expect(
    await page.evaluate(() => document.documentElement.scrollWidth),
  ).toBeLessThanOrEqual(390);
  await page.screenshot({
    path: "../docs/screenshots/mobile.png",
    fullPage: true,
  });
  await page.getByRole("link", { name: "Products", exact: true }).click();
  await page.getByRole("button", { name: "Add product", exact: true }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.getByRole("button", { name: "Close dialog" }).click();
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(
    page.getByRole("heading", { name: "Welcome back" }),
  ).toBeVisible();
});
