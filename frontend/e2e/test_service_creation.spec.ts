import { test, expect } from "@playwright/test";

test("dashboard shows empty state before any services exist for a fresh filter view", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(
    page.getByRole("button", { name: /new service/i })
  ).toBeVisible();
});

test("creating a service navigates to its detail page and lists it on the dashboard", async ({
  page,
}) => {
  const reg = `E2E${Date.now().toString().slice(-8)}`;

  await page.goto("/services/new");
  await page.getByLabel("Registration Number").fill(reg);
  await page.getByLabel("Owner Name").fill("Dashboard Tester");
  await page.getByLabel("Contact Number").fill("9876500002");
  await page.getByLabel("Vehicle Model").fill("Test Vehicle");
  await page.getByLabel("Service Type").selectOption("BRAKE_SERVICE");
  await page
    .getByLabel("Appointment Date & Time")
    .fill("2027-06-03T10:00");
  await page.getByLabel("Issue Description").fill("Dashboard listing test");
  await page.getByRole("button", { name: /create service/i }).click();

  await expect(page).toHaveURL(/\/services\/\d+$/);

  // Verify the specific service on the detail page.
  await expect(
    page.locator(".reg-plate").filter({ hasText: reg })
  ).toBeVisible();

  await page.getByRole("link", { name: /AutoFlow/i }).click();

  // Verify the specific service on the dashboard.
  await expect(
    page.locator(".reg-plate").filter({ hasText: reg })
  ).toBeVisible();

  // Verify the specific owner's row rather than every matching text.
  await expect(
    page.getByRole("cell", { name: "Dashboard Tester" }).last()
  ).toBeVisible();
});

test("service detail page only shows actions valid for the current status", async ({
  page,
}) => {
  const reg = `E2E${Date.now().toString().slice(-8)}`;

  await page.goto("/services/new");
  await page.getByLabel("Registration Number").fill(reg);
  await page.getByLabel("Owner Name").fill("Action Tester");
  await page.getByLabel("Contact Number").fill("9876500003");
  await page.getByLabel("Vehicle Model").fill("Test Vehicle");
  await page.getByLabel("Service Type").selectOption("ENGINE_REPAIR");
  await page
    .getByLabel("Appointment Date & Time")
    .fill("2027-06-04T10:00");
  await page.getByLabel("Issue Description").fill("Action visibility test");
  await page.getByRole("button", { name: /create service/i }).click();

  // BOOKED: Start Inspection + Cancel should be visible; Complete should not.
  await expect(
    page.getByRole("button", { name: /start inspection/i })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /cancel service/i })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /complete service/i })
  ).not.toBeVisible();

  await page.getByRole("button", { name: /start inspection/i }).click();

  // INSPECTION: Start Repair + Cancel visible; Start Inspection no longer offered.
  await expect(
    page.getByRole("button", { name: /start repair/i })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /cancel service/i })
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: /start inspection/i })
  ).not.toBeVisible();
});