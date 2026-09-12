import { assertEquals } from "https://deno.land/std@0.224.0/assert/mod.ts";
import { isOperationalSession, projectOperationalSession } from "./projection.ts";

Deno.test("only proven committed lifecycle states enter the operational projection", () => {
  for (const status of ["scheduled", "active", "completed"]) assertEquals(isOperationalSession({ status }), true);
  for (const status of ["proposed_window", "draft", "tentative", "pending_proposal", "canceled", "deleted"]) {
    assertEquals(isOperationalSession({ status }), false);
  }
});

Deno.test("canonical session projects names and truthful zero named registrations", () => {
  const session = { id: "session-1", status: "scheduled", course_id: "course-1", location_id: "location-1", lead_instructor_id: "person-1" };
  const row = projectOperationalSession(session, new Map(), new Map([["course-1", "BLS"]]), new Map([["location-1", "Wilmington"]]), new Map([["person-1", "Instructor"]]));
  assertEquals([row.course_name, row.location_name, row.lead_instructor_name], ["BLS", "Wilmington", "Instructor"]);
  assertEquals(row.registered_count, 0);
  assertEquals(row.participant_count_available, true);
});
