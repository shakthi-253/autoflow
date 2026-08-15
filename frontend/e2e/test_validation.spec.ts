import { test, expect } from "@playwright/test";

test("submitting an empty form shows field-level errors and does not navigate away", async ({
  page,
}) => {
  await page.goto("/services/new");
  await page.getByRole("button", { name: /create service/i }).click();

  await expect(page.getByText("Registration number is required")).toBeVisible();
  await expect(page.getByText("Owner name is required")).toBeVisible();
  await expect(page.getByText("Contact number is required")).toBeVisible();
  await expect(page).toHaveURL(/\/services\/new$/);
});

test("invalid contact number shows a client-side error before submission", async ({ page }) => {
  await page.goto("/services/new");
  const contactField = page.getByLabel("Contact Number");
  await contactField.fill("abc");
  await contactField.blur();

  await expect(
    page.getByText("Enter 7-15 digits, optionally starting with +")
  ).toBeVisible();
});

test("invalid registration number shows a client-side error before submission", async ({
  page,
}) => {
  await page.goto("/services/new");
  const regField = page.getByLabel("Registration Number");
  await regField.fill("AB");
  await regField.blur();

  await expect(page.getByText(/5-17 letters\/numbers/i)).toBeVisible();
});

test("backend validation error surfaces even if frontend somehow allows submission", async ({
  page,
}) => {
  // Simulate bypassing the frontend by calling the API directly, then
  // confirm the app surfaces the backend's structured error rather than
  // silently failing. This mirrors "never trust client-side validation".
  const response = await page.request.post("http://127.0.0.1:8000/services", {
    data: {
      registration_number: "",
      owner_name: "X",
      contact_number: "9876543210",
      vehicle_model: "Y",
      service_type: "OIL_CHANGE",
      issue_description: "Z",
      appointment_date: "2027-06-05T10:00:00",
    },
  });
  expect(response.status()).toBe(422);
  const body = await response.json();
  expect(body.error).toBe("VALIDATION_ERROR");
});
