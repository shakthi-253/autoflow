import { test, expect } from "@playwright/test";

/**
 * Full workflow, driven through the actual UI:
 * Create Service -> verify BOOKED -> Start Inspection -> verify INSPECTION
 * -> Start Repair -> verify REPAIR -> Complete Service -> verify COMPLETED.
 *
 * Each run uses a unique registration number so the test is independent
 * of any data already in the (isolated, per-test-server) database.
 */
test("full service workflow from booking to completion", async ({ page }) => {
  const reg = `E2E${Date.now().toString().slice(-8)}`;

  await page.goto("/");
  await page.getByRole("button", { name: /new service/i }).click();

  await page.getByLabel("Registration Number").fill(reg);
  await page.getByLabel("Owner Name").fill("Playwright Tester");
  await page.getByLabel("Contact Number").fill("9876500000");
  await page.getByLabel("Vehicle Model").fill("Test Vehicle");
  await page.getByLabel("Service Type").selectOption("GENERAL_SERVICE");
  await page
    .getByLabel("Appointment Date & Time")
    .fill("2027-06-01T10:00");
  await page.getByLabel("Issue Description").fill("End-to-end workflow test");

  await page.getByRole("button", { name: /create service/i }).click();

  // Should land on the service detail page, status BOOKED.
  await expect(page.locator(".status-badge")).toHaveText(/Booked/i);

  await expect(
    page.locator(".reg-plate").filter({ hasText: reg })
  ).toHaveText(reg);

  await page.getByRole("button", { name: /start inspection/i }).click();
  await expect(page.locator(".status-badge")).toHaveText(/Inspection/i);

  await page.getByRole("button", { name: /start repair/i }).click();
  await expect(page.locator(".status-badge")).toHaveText(/Repair/i);

  await page.getByRole("button", { name: /complete service/i }).click();
  await expect(page.locator(".status-badge")).toHaveText(/Completed/i);

  // No further actions should be offered on a completed service.
  await expect(
    page.getByText(/no further workflow action/i)
  ).toBeVisible();

  // Dashboard should reflect the completed service.
  await page.getByRole("link", { name: /AutoFlow/i }).click();

  await expect(
    page.locator(".reg-plate").filter({ hasText: reg })
  ).toBeVisible();
});

test("cancellation from BOOKED removes further workflow actions", async ({
  page,
}) => {
  const reg = `E2E${Date.now().toString().slice(-8)}`;

  await page.goto("/services/new");
  await page.getByLabel("Registration Number").fill(reg);
  await page.getByLabel("Owner Name").fill("Playwright Tester");
  await page.getByLabel("Contact Number").fill("9876500001");
  await page.getByLabel("Vehicle Model").fill("Test Vehicle");
  await page.getByLabel("Service Type").selectOption("TYRE_SERVICE");
  await page
    .getByLabel("Appointment Date & Time")
    .fill("2027-06-02T10:00");
  await page.getByLabel("Issue Description").fill("Cancellation test");
  await page.getByRole("button", { name: /create service/i }).click();

  await page.getByRole("button", { name: /cancel service/i }).click();

  await expect(page.locator(".status-badge")).toHaveText(/Cancelled/i);

  await expect(
    page.getByText(/no further workflow action/i)
  ).toBeVisible();
});