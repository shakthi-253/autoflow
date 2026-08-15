# AutoFlow — User Guide

This guide is for anyone at the service center who books, tracks, and
completes vehicle services in AutoFlow — no technical background
needed.

## Opening AutoFlow

Open the application in your web browser. You'll land on the
**Dashboard**, which shows:
- A row of counters at the top — how many services are currently
  Booked, in Inspection, in Repair, Completed, or Cancelled.
- A table below listing every service, newest first.

## Booking a new service

1. Click the **+ New Service** button in the top right of the Dashboard.
2. Fill in the vehicle and owner details:
   - Registration Number
   - Owner Name
   - Contact Number
   - Vehicle Model
3. Fill in the service details:
   - Service Type (pick from the dropdown: General Service, Oil
     Change, Brake Service, Engine Repair, or Tyre Service)
   - Appointment Date & Time
   - Issue Description — describe the problem in your own words, e.g.
     *"Brake making a squeaking noise"* or *"Routine oil change"*.
4. Click **Create Service**.

If anything's missing or entered incorrectly (like a contact number
that isn't the right length), you'll see a message under that field
telling you exactly what to fix — nothing is submitted until every
field is valid.

You'll then be taken straight to that service's detail page.

### A note on booking the same vehicle twice

If you try to book the same vehicle for the exact same date and time
as an appointment it already has (and that appointment hasn't been
completed or cancelled), AutoFlow will stop you and show an error
instead of creating a duplicate booking.

## Understanding Priority

Every service is automatically labeled **High**, **Medium**, or **Low**
priority, based on the words in the Issue Description you typed —
you never set this yourself. For example:
- *"Engine failure, vehicle won't start"* → **High**
- *"AC not cooling properly"* → **Medium**
- *"Oil change"* → **Low**

This label appears on the service's detail page and in the Dashboard
table, so urgent jobs stand out at a glance. If a description doesn't
match any of the urgent or moderate keywords, it's simply Low priority
— that's the normal, expected outcome for routine work, not an error.

## Moving a service through its stages

Open any service from the Dashboard table (click anywhere on its row)
to see its detail page. Near the top you'll see a progress tracker:

```
Booked → Inspection → Repair → Completed
```

On the right, you'll only see the buttons that make sense for where
the service currently is:

| Current stage | What you can do |
|---|---|
| **Booked** | Start Inspection, or Cancel Service |
| **Inspection** | Start Repair, or Cancel Service |
| **Repair** | Complete Service |
| **Completed** | Nothing further — the job is done |
| **Cancelled** | Nothing further |

Click the relevant button to move the service forward. The status
badge and progress tracker update immediately.

You can't skip a stage — for example, there's no way to jump a service
straight from Booked to Completed. This is by design, so nothing gets
marked "done" without actually going through inspection and repair.

## If something goes wrong

If an action can't be completed (for example, trying an action that's
no longer valid because someone else already updated the service), a
clear message will appear explaining what happened. Nothing is ever
silently ignored — you'll always know whether your action succeeded.

## Quick reference

| I want to... | Where to go |
|---|---|
| See everything at a glance | Dashboard (home page) |
| Book a new vehicle in | **+ New Service** button |
| Check a specific service's status | Click its row on the Dashboard |
| Move a service to the next stage | Open the service, click the relevant action button |
| Cancel a booking | Open the service (while Booked or Inspection), click **Cancel Service** |
